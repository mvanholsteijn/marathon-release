#!/usr/bin/env python
#
#   Copyright 2017 Xebia Nederland B.V.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

import os
import sys
import configparser

import json
import fnmatch
import click
import requests
from jsondiff import diff as jdiff
from jinja2 import Environment, FileSystemLoader


class MarathonDeployer:

    def __init__(self, domain_name, dry_run=False, verbose=False, verify_ssl=True):
        self.dry_run = dry_run
        self.verbose = verbose
        self.headers = {}
        self.domain_name = domain_name
        self.read_domain_cfg()
        self.read_authorization_header()
        self.application_definitions = {}
        self.verify_ssl = verify_ssl

    def is_empty_value(self, value):
        if value is None:
            return True
        elif isinstance(value, list):
            return len(value) == 0
        elif isinstance(value, (str, unicode)):
            return len(value) == 0
        elif isinstance(value, int):
            return value == 0
        elif isinstance(value, float):
            return value == 0
        elif isinstance(value, dict):
            return len(value.keys()) == 0
        else:
            return False

    def clean_app(self, app):
        """
            removes all null and runtime fields from an app definition.
        """
        runtime_fields = ['deployments', 'tasksStaged', 'tasksHealthy',
                          'tasksRunning', 'tasksUnhealthy', 'version',
                          'versionInfo', 'tasks', 'lastTaskFailure']
        for field in runtime_fields:
            if field in app:
                del app[field]

        empty_fields = ['gpus', 'executor', 'acceptedResourceRoles', 'args', 'fetch', 'secrets',
                        'cmd', 'readinessChecks', 'ipAddress', 'uris', 'constraints', 'residency',
                        'taskKillGracePeriodSeconds', 'storeUrls', 'dependencies', 'user', 'labels']
        for field in empty_fields:
            if field not in app:
                continue

            if self.is_empty_value(app[field]):
                del app[field]

    def read_domain_cfg(self):
        """
        returns the configuration from ./cfg/domain.cfg'
        """
        try:
            cdir = os.path.abspath(os.path.join('.', 'cfg'))
            config = configparser.ConfigParser(
                {'domain_name': self.domain_name})
            config.read(os.path.join(cdir, 'domain.cfg'))

            if not config.has_section(self.domain_name):
                sys.stderr.write(
                    'ERROR: the domain "%s" does not exist in cfg/domain.cfg\n' % self.domain_name)
                sys.exit(1)

            self.marathon_url = config.get(self.domain_name, 'marathon_url')
            if self.marathon_url is None:
                sys.stderr.write(
                    'ERROR: No marathon_url has been defined for domain "%s" in cfg/domain.cfg\n'
                    % self.domain_name)
                sys.exit(1)
        except configparser.Error as e:
            sys.stderr.write(
                'ERROR: failed to read domain configuration ./cfg/domain.cfg, %s\n' % e)
            sys.exit(1)

        return config

    def read_authorization_header(self):
        """
        reads id_token from the file ~/.auth_token and returns
        an HTTP Bearer token Authorization header
        """
        self.headers = {}
        filename = os.path.join(os.path.expanduser('~'), '.auth_tokens')
        if os.path.isfile(filename):
            try:
                with open(filename, 'r') as file_ptr:
                    bearer_token = json.load(file_ptr)['id_token']
                self.headers['Authorization'] = 'Bearer %s' % bearer_token
            except Exception as e:
                sys.stderr.write(
                    'could not read token from %s: %s\n' % (filename, e))
                sys.exit(1)

    def load_application_definition(self, path):
        """
        generates application definitions for a specific environment.
        """
        app_id = os.path.splitext(os.path.basename(path))[0]
        cfg_file = os.path.join(os.path.dirname(path), '%s.cfg' % app_id)

        try:
            config = self.read_domain_cfg()
            config.read(cfg_file)
            items = dict(config.items(self.domain_name)) if config.has_section(
                self.domain_name) else config.defaults()
        except configparser.Error as e:
            sys.stderr.write(
                'ERROR: failed to read  configuration %s, %s\n' % (cfg_file, e))
            sys.exit(1)

        try:
            jinja = Environment(
                autoescape=False,
                loader=FileSystemLoader(os.path.dirname(path)),
                trim_blocks=False)
            filename = os.path.basename(path)
            rendered_app_def = jinja.get_template(filename).render(items)
            app = json.loads(rendered_app_def)

            if app['id'] != '/%s' % app_id:
                sys.stderr.write(
                    'ERROR: application id in template "%s" is not "/%s"\n' % (path, app_id))
                sys.exit(1)

        except Exception as error:
            sys.stderr.write(
                'ERROR: invalidate template %s, %s\n' % (path, error))
            sys.exit(1)

        return app


    def load_all_app_definitions(self, directory=os.path.join('.', 'apps')):
        """
        load all files with the suffix `.json` from the `directory` as application definition.
        """
        result = {}
        app_files = fnmatch.filter(os.listdir(directory), '*.json')
        for filename in app_files:
            path = os.path.join(directory, filename)
            if os.path.isfile(path):
                app = self.load_application_definition(path)
                if app['id'] not in result:
                    result[app['id']] = app
                else:
                    sys.stderr.write(
                        'ERROR: skipping "%s" as it contains a duplicate app definition "%s"\n'
                        % (path, app['id']))
            else:
                sys.stderr.write(
                    'WARN: skipping "%s" as it is not a file\n' % path)
        return result

    def delete_application(self, app_id):
        sys.stderr.write(
            'INFO: deleting application "%s"\n' % app_id)
        if self.dry_run:
            return

        result = requests.delete('%s/v2/apps/%s' % (self.marathon_url, app_id),
                                 headers=self.headers, verify=self.verify_ssl)
        if result.status_code == 200 or result.status_code == 201:
            sys.stderr.write(
                'INFO: delete running for application "%s"\n' % app_id)
        else:
            sys.stderr.write(
                'ERROR: deployment for application "%s" failed, with status code %d\n'
                % (app_id, result.status_code))

    def deploy_new_application(self, app):
        app_id = app['id']
        sys.stderr.write(
            'INFO: deploying new application "%s"\n' % app_id)
        if self.dry_run:
            return

        result = requests.post(self.marathon_url + "/v2/apps",
                               json=app, headers=self.headers, verify=self.verify_ssl)
        if result.status_code == 200 or result.status_code == 201:
            sys.stderr.write(
                'INFO: deployment running for application "%s"\n' % app_id)
        else:
            sys.stderr.write(
                'ERROR: deployment for application "%s" failed, with status code %d\n'
                % (app_id, result.status_code))

    def get_application(self, app_id):
        result = requests.get(self.marathon_url + "/v2/apps/%s" %
                              app_id, headers=self.headers, verify=self.verify_ssl)
        if result.status_code == 200:
            app = result.json()['app']
            self.clean_app(app)
        elif result.status_code == 404:
            app = None
        else:
            sys.stderr.write(
                'ERROR: could not retrieve application "%s", received status code %d from %s\n'
                % (app_id, result.status_code, self.marathon_url))
            sys.exit(1)
        return app

    def update_application(self, app, existing_app):
        app_id = app['id']
        self.clean_app(existing_app)
        differences = json.loads(
            jdiff(existing_app, app, syntax='explicit', dump=True))

        if len(differences.keys()) == 0:
            sys.stderr.write(
                'INFO: no changes to application "%s"\n' % app_id)
            return
        else:
            sys.stderr.write(
                'INFO: updating application "%s"\n' % (app_id))

        if self.verbose:
            json.dump(differences, sys.stderr, indent=2)
            sys.stderr.write('\n')

        if self.dry_run:
            return

        result = requests.put(self.marathon_url + "/v2/apps/%s" % app_id,
                              json=app,
                              headers=self.headers, verify=self.verify_ssl)
        if result.status_code == 200 or result.status_code == 201:
            sys.stderr.write(
                'INFO: deployment running for application "%s"\n' % app_id)
        else:
            sys.stderr.write(
                'ERROR: deployment for application "%s" failed, with status code %d\n' % (
                    app_id, result.status_code))

    def deploy_application(self, app):
        app_id = app['id']
        existing_app = self.get_application(app_id)
        if existing_app is not None:
            self.update_application(app, existing_app)
        else:
            self.deploy_new_application(app)

    def get_all_applications(self):
        """
        retrieve all Marathon application definitions and return
        an dictionary with app_id -> app_definition.
        """
        apps = {}
        result = requests.get(self.marathon_url +
                              "/v2/apps", headers=self.headers, verify=self.verify_ssl)
        if result.status_code == 200:
            for app in result.json()['apps']:
                app_id = app['id']
                apps[app_id] = app
        elif result.status_code == 404:
            pass
        else:
            sys.stderr.write(
                'ERROR: could not retrieve applications from "%s", status %d\n' % (
                    self.marathon_url, result.status_code))
            sys.exit(1)

        return apps

    def save_application_definitions(self, apps, directory):
        directory = os.path.abspath(directory)
        if not os.path.exists(directory):
            os.makedirs(directory)

        for app_id in apps:
            app = apps[app_id]
            self.clean_app(app)
            filename = os.path.join(directory, './%s.json' % app_id)
            with open(filename, 'w') as file_ptr:
                json.dump(app, file_ptr, indent=2)


@click.group()
def cli():
    pass


@cli.command()
@click.option('--domain-name',
              required=True,
              help='to deploy to.')
@click.option('--dry-run',
              default=False,
              is_flag=True,
              help='do not do actual deploy.')
@click.option('--verbose',
              default=False,
              is_flag=True,
              help='show changes that are applied.')
@click.option('--all-applications',
              default=False,
              is_flag=True,
              help='deploy all applications.')
@click.option('--verify-ssl/--no-verify-ssl',
              required=False, default=True,
              help='ignore ssl verification errors.')
@click.argument('applications',
                nargs=-1)
def deploy(domain_name, dry_run, verbose, all_applications, verify_ssl, applications):
    """
        deploys selected or all application definitions to the domain 'domain-name'.

        the definitions are read from ./apps/.

        The marathon_url for the domain is read from the configuration file 'cfg/domain.cfg'
    """

    applications = map(lambda id: '/%s' %
                       id if id[0] != '/' else id, applications)
    deployer = MarathonDeployer(
        domain_name, verify_ssl=verify_ssl, dry_run=dry_run, verbose=verbose)
    apps = deployer.load_all_app_definitions()

    sys.stderr.write(
        'INFO: loaded %d applications defined in ./apps\n' % len(apps))
    if all_applications:
        applications = apps

    if applications is None or len(applications) == 0:
        sys.stderr.write(
            'ERROR: no applications to deploy, specify specific ones or use --all-applications\n')
        sys.exit(1)

    for app_id in applications:
        if app_id in apps:
            deployer.deploy_application(apps[app_id])
        else:
            sys.stderr.write('WARN: No application "%s" found\n' % app_id)


@cli.command()
@click.option('--domain-name',
              required=True,
              help='to deploy to.')
@click.option('--verify-ssl/--no-verify-ssl',
              required=False, default=True,
              help='ignore ssl verification errors.')
def diff(domain_name, verify_ssl):
    """
        differences between defined and deployed application definitions.
    """
    deployer = MarathonDeployer(
        domain_name, verify_ssl=verify_ssl, dry_run=True, verbose=True)
    applications = deployer.load_all_app_definitions()
    sys.stderr.write(
        'INFO: loaded %d applications from ./apps\n' % len(applications))

    if len(applications) == 0:
        sys.stderr.write('ERROR: no applications found to deploy.\n')
        sys.exit(1)

    for app_id in applications.keys():
        deployer.deploy_application(applications[app_id])


@cli.command()
@click.option('--domain-name', required=True, help='to download application definitions from.')
@click.option('--directory',
              type=click.Path(exists=True, file_okay=False),
              help='the directory to save all application definitions in.')
@click.option('--verify-ssl/--no-verify-ssl',
              required=False, default=True,
              help='ignore ssl verification errors.')
def download(domain_name, directory, verify_ssl):
    """
        saves all application definitions deployed by marathon at the defined URL to the specified
        directory.
    """
    if directory is None:
        directory = os.path.abspath(os.path.join('current', domain_name))

    deployer = MarathonDeployer(domain_name, verify_ssl=verify_ssl)
    apps = deployer.get_all_applications()
    if len(apps) > 0:
        sys.stderr.write('INFO: saving %d applications to %s.\n' %
                         (len(apps), directory))
        deployer.save_application_definitions(apps, directory)
    else:
        sys.stderr.write('WARN: no applications deployed at %s.\n' %
                         deployer.marathon_url)


@cli.command()
@click.option('--domain-name', required=True, help='to delete applications from.')
@click.option('--dry-run',
              default=False,
              is_flag=True,
              help='do not do actually deleted.')
@click.option('--verify-ssl/--no-verify-ssl',
              required=False, default=True,
              help='ignore ssl verification errors.')
def delete(domain_name, dry_run, verify_ssl):
    """
        deletes all undefined applications deployed without an application definition in ./apps.
    """
    deployer = MarathonDeployer(
        domain_name, verify_ssl=verify_ssl, dry_run=dry_run)
    defined_apps = deployer.load_all_app_definitions().keys()
    deployed_apps = deployer.get_all_applications().keys()
    undefined_apps = set(deployed_apps).difference(set(defined_apps))
    for app_id in undefined_apps:
        deployer.delete_application(app_id)


@cli.command()
@click.option('--input-directory',
              type=click.Path(exists=True, file_okay=False),
              default='./apps',
              help='the directory with the template application definitions.')
@click.option('--output-directory',
              type=click.Path(file_okay=False),
              help='the directory with the generated application definitions.')
@click.option('--domain-name',
              required=True,
              help='to generate the application definitions for.')
@click.option('--verify-ssl/--no-verify-ssl',
              required=False, default=True,
              help='ignore ssl verification errors.')
def generate(input_directory, output_directory, domain_name, verify_ssl):
    """
    generates application definitions for a domain.
    """
    deployer = MarathonDeployer(domain_name, verify_ssl=verify_ssl)
    if output_directory is None:
        output_directory = os.path.join('.', 'deployments', domain_name)

    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    apps = deployer.load_all_app_definitions(input_directory)
    if len(apps) > 0:
        sys.stderr.write('INFO: generating %d applications to %s.\n' %
                         (len(apps), output_directory))
        deployer.save_application_definitions(apps, output_directory)
    else:
        sys.stderr.write(
            'INFO: no applications defined at %s.\n' % input_directory)


if __name__ == '__main__':
    cli()
