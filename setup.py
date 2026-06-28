from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setup_info = dict(name='idrac_ctl',
                  version='1.0.14',
                  author='Mustafa Bayramov',
                  author_email="spyroot@gmail.com",
                  url="https://github.com/spyroot/idrac_ctl",
                  description='Standalone command line tool to '
                              'interact with Dell iDRAC via Redfish REST API.',
                  long_description=long_description,
                  long_description_content_type='text/markdown',
                  packages=['idrac_ctl'] + ['idrac_ctl.' + pkg for pkg in find_packages('idrac_ctl')],
                  license="MIT",
                  python_requires='>=3.10',
                  install_requires=requirements,
                  entry_points={
                      'console_scripts': [
                          'idrac_ctl = idrac_ctl.idrac_main:idrac_main_ctl',
                          'redfish-discover = idrac_ctl.discover.cli:redfish_discover_main',
                      ]
                  },
                  extras_require={
                      "dev": [
                          "pytest >= 7",
                          "requests-mock >= 1.10",
                          "ruff",
                          "mypy",
                      ],
                      "schema": [
                          "jsonschema >= 4.18",
                          "referencing",
                      ],
                      "tui": [
                          "rich >= 13",
                      ],
                  },
                  )
setup(**setup_info)
