from setuptools import setup, find_packages

setup_info = dict(name='idrack_ctl',
                  version='1.0',
                  author='Mustafa Bayramov',
                  description='Standalone ctl tool to interact with iDRAC.',
                  author_email='spyroot@gmail.com',
                  packages=['base'] + ['base.' + pkg for pkg in find_packages('base')],
                  )
setup(**setup_info)
