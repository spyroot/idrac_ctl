from setuptools import setup, find_packages

setup_info = dict(name='idrac_ctl',
                  version='1.0',
                  author='Mustafa Bayramov',
                  description='Standalone command line tool to '
                              'interact with Dell iDRAC via Redfish REST API.',
                  author_email='spyroot@gmail.com',
                  packages=['base'] + ['base.' + pkg for pkg in find_packages('base')],
                  )
setup(**setup_info)
