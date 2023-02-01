from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup_info = dict(name='idrac_ctl',
                  version='1.0',
                  author='Mustafa Bayramov',
                  author_email="spyroot@gmail.com",
                  url="https://github.com/spyroot/idrac_ctl",
                  description='Standalone command line tool to '
                              'interact with Dell iDRAC via Redfish REST API.',
                  packages=['base'] + ['base.' + pkg for pkg in find_packages('base')],
                  python_requires='>=3',
                  extras_require={
                      "dev": [
                          "pytest >= 3.7"
                      ]
                  },
                  )
setup(**setup_info)
