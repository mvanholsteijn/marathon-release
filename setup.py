"""
 marathon-release allows you to manage multiple Marathon application definitions as a single release.
"""
from setuptools import find_packages, setup

dependencies = [ 'click==6.7', 'configparser==3.5.0', 'Jinja2==2.9.6', 'jsondiff==1.1.1', 'requests==2.13.0']

setup(
    name='marathonrelease',
    version='0.9.0',
    url='https://github.com/mvanholsteijn/marathon-release',
    license='BSD',
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
            'marathon-release = marathon_release.cli:main',
        ],
    },
    classifiers=[
        # As from http://pypi.python.org/pypi?%3Aaction=list_classifiers
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        # 'Development Status :: 3 - Alpha',
        'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        # 'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        #'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
