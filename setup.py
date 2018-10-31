"""
 marathon-release allows you to manage multiple Marathon application definitions as a single release.
"""
from setuptools import find_packages, setup

dependencies = [ 'click==6.7', 'configparser==3.5.0', 'Jinja2==2.9.6', 'jsondiff==1.1.1', 'requests>=2.20.0']

setup(
    name='marathonrelease',
    version='0.2.0',
    url='https://github.com/mvanholsteijn/marathon-release',
    license='Apache',
    author='Mark van Holsteijn',
    author_email='mvanholsteijn@xebia.com',
    description=' marathon-release allows you to manage multiple Marathon application definitions as a single release.',
    long_description=__doc__,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
    entry_points={
        'console_scripts': [
            'marathon-release = marathon_release.cli:cli',
        ],
    },
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Topic :: Utilities',
    ]
)
