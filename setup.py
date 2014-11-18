#!/usr/bin/env python3
# encoding: utf-8

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
import os

import sys

#Inform user that Kerminal must use Python 3.4.0 or higher
py_version = sys.version_info[:3]
if py_version[0] < 3:
    sys.exit('Sorry, Kerminal only works with Python 3.4.0 or higher')
elif py_version[1] < 4:
    sys.exit('Sorry, Kerminal only works with Python 3.4.0 or higher')


def long_description():
    readme = os.path.join(os.path.dirname(__file__), 'README.md')
    with open(readme, 'r') as inf:
        readme_text = inf.read()
    return(readme_text)

setup(name='Kerminal',
      version='0.1.1',
      description='Kerbal Space Program in the Terminal, via Telemachus',
      long_description=long_description(),
      author='Paul Barton',
      author_email='pablo.barton@gmail.com',
      url='https://github.com/SavinaRoja/Kerminal',
      #package_dir = {'': 'kerminal'},
      packages=['kerminal'],
      scripts=['scripts/kerminal'],
      license='http://www.gnu.org/licenses/gpl-3.0.html',
      keywords='npyscreen, telemetry, websocket,',
      install_requires=['autobahn',
                        #'npyscreen2',  # Not on PyPI yet; manually install
                        'docopt']
)
