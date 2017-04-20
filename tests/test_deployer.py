import json
import os
from marathon_release import cli


def test_empty_values(pytestconfig):
    """
    empty values are properly detected.
    """
    os.chdir(os.path.join(str(pytestconfig.rootdir), 'tests'))
    deployer = cli.MarathonDeployer('test')
    assert deployer.is_empty_value(0)
    assert deployer.is_empty_value(0.0)
    assert deployer.is_empty_value("")
    assert deployer.is_empty_value(u"")
    assert deployer.is_empty_value(None)
    assert deployer.is_empty_value([])
    assert deployer.is_empty_value({})
    assert not deployer.is_empty_value({"a": 1})
    assert not deployer.is_empty_value([1])
    assert not deployer.is_empty_value(1)
    assert not deployer.is_empty_value(1.0)
    assert not deployer.is_empty_value("a")
    assert not deployer.is_empty_value(u"a")


def test_clean_runtime_fields(pytestconfig):
    """
     whether runtime fields are removed from an application definition.
    """
    os.chdir(os.path.join(str(pytestconfig.rootdir), 'tests'))
    deployer = cli.MarathonDeployer('test')

    app = None
    with open('actual.json') as f:
        app = json.load(f)

    deployer.clean_app(app)

    runtime_fields = ['deployments', 'tasksStaged', 'tasksHealthy',
                      'tasksRunning', 'tasksUnhealthy', 'version',
                      'versionInfo', 'tasks', 'lastTaskFailure']

    for field in runtime_fields:
        assert field not in app


def test_clean_empty_fields(pytestconfig):
    """
    tests whether runtime fields are removed from an application definition.
    """

    os.chdir(os.path.join(str(pytestconfig.rootdir), 'tests'))
    deployer = cli.MarathonDeployer('test')

    app = None
    with open('actual.json') as f:
        app = json.load(f)
    org = json.loads(json.dumps(app))

    deployer.clean_app(app)

    empty_fields = ['gpus', 'executor', 'acceptedResourceRoles', 'args', 'fetch', 'secrets',
                    'cmd', 'readinessChecks', 'ipAddress', 'uris', 'constraints', 'residency',
                    'taskKillGracePeriodSeconds', 'storeUrls', 'dependencies', 'user', 'labels']

    deployer.clean_app(app)

    for field in empty_fields:
        if field in org:
            if deployer.is_empty_value(org[field]):
                assert field not in app
            else:
                assert field in app


def test_load_app_definition(pytestconfig):
    """
    using templates.
    """
    testdir = os.path.join(str(pytestconfig.rootdir), 'tests')
    os.chdir(testdir)
    deployer = cli.MarathonDeployer('test')
    apps = deployer.load_all_app_definitions(directory=os.path.join(testdir, 'apps'))
    assert '/a' in apps
    assert '/b' in apps
    assert apps['/a']['id'] == '/a'
    assert apps['/b']['id'] == '/b'
    assert apps['/a']['env']['RELEASE'] == '1.1'
    assert apps['/b']['env']['RELEASE'] == '1.0'
