# marathon release 
marathon-release allows you to manage multiple Marathon application definitions as a
single release.

This utility allows you to define all the Marathon application definition that 
make up the release of your application landscape and handle environment 
specific variations.

You get to:
- keep the complete release under version control.
- deploy the same release to different environments.
- handle environment specific variations.
- detect configuration drift.
- keep your release in sync with the intended state.

marathon-release is a just a tiny bit of glue code between the Python:
- requests 
- configparser 
- jinja

# Installation

First install pipsi by following the [Pipsi installation instructions](https://github.com/mitsuhiko/pipsi#readme), then type:

```
git clone https://github.com/mvanholsteijn/marathon-release 
pipsi install marathon-release
```


## directory layout
marathon-release expects the following directory layout:

```
.
├── cfg
|   ├── domain.cfg          # definition of different domains.
├── apps
|   ├── <app-id>.cfg        # environment specific configuration for <app-id>.
|   ├── <app-id>.json	    # Marathon application definition template for <app-id>.
```

The application definition files are [Jinja](http://jinja.pocoo.org/) templates which may refer to any properties that are defined
in the configuration files (.cfg) which are standard [Python configuration](https://docs.python.org/2/library/configparser.html) 
files. 

### Domain configuration
The domain configuration file in ./cfg/domain.cfg is required to define a property named `marathon_url` which 
points to Marathon application. For each environment there should be a separate section. The following example
shows the definition for the domains `dev`, `tst`, `acc` and `prd`.

```
[DEFAULT]
marathon_url		=	http://marathon.%(external_domain_name)s:8080

[dev]
external_domain_name	=	dev.127.0.0.1.xip.io

[tst]
external_domain_name	=	test.127.0.0.1.xip.io

[acc]
external_domain_name	=	acc.127.0.0.1.xip.io

[prd]
external_domain_name	=	prd.127.0.0.1.xip.io
```

The domain configuration file can also be used to define any global variables which are applicable to all application
definitions. In the above example, we have defined the global variable `external_domain_name` which is used in the
definition of the required property `marathon_url`.

### Application configuration
For each application you can define it Marathon application definition in `./apps/<app-id>.json`. The `app-id` should match the
marathon application id defined in the file.

Any environment specific properties can be defined in the file `./apps/<app-id>.json`. The following example shows 
the configuration of the properties `number_of_instances` and `release` for the domains `dev`, `tst`, `acc` and `prd`.

```
[DEFAULT]
number_of_instances	=	1

[dev]
release			=	latest

[tst]
release			= 	1.6.9

[acc]
release			= 	1.6.8
number_of_instances	=	2

[prd]
release			= 	1.6.7
number_of_instances	=	4
```

As the application definition file is a  [Jinja](http://jinja.pocoo.org/) you may refer to these and the properties defined in the domain configuration files, as show in the following snippet:

```
{
  "id": "/paas-monitor", 
  "mem": 16, 
  "cpus": 0.10, 
  "instances": {{number_of_instances}}, 
      ....
      "image": "mvanholsteijn/paas-monitor:{{release}}", 
   "labels" : {
     ...
     "HAPROXY_0_VHOST" : "paas-monitor.{{external_domain_name}}"
   }
}
```


### Diffing a release
To determine what is going to happen, you can use the diff command:

```
$ marathon-release diff --domain-name dev 

INFO: loaded 1 applications from ./apps
INFO: deploying new application "/paas-monitor"
```

### Deploying a release
To actually deploy, use:

```
$ marathon-release deploy --domain-name dev --all-applications
INFO: loaded 1 applications defined in ./apps
INFO: deploying new application "/paas-monitor"
INFO: deployment running for application "/paas-monitor"
```

### Downloading current application definitions
If you are interested to keep the current application definitions of the domain, type:

```
$ marathon-release download --domain-name dev
```

The resulting files will be written to `./deployments/dev/`


### Removing undefined applications
Sometimes you will find that applications are deployed that are no longer defined. To remove these, type:

```
$ marathon-release delete --domain-name dev  --dry-run
INFO: deleting application "/mies-monitor"
INFO: deleting application "/aap-monitor"
```

If you like what you see, run it without the `--dry-run`.

### Generating new application definitions
If you are interested to see the application definitions for a domain that result from your configuration, type:

```
$ marathon-release generate --domain-name dev
```

The resulting files will be written to `./deployments/dev/`
