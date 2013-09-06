# coding: utf-8
"""
Copyright (c) 2007 - 2013 Novutec Inc. (http://www.novutec.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@category Novutec
@package pynsd-rpcd
@copyright Copyright (c) 2007 - 2013 Novutec Inc. (http://www.novutec.com)
@license http://www.apache.org/licenses/LICENSE-2.0
"""

from setuptools import setup, find_packages

VERSION = open('VERSION', 'r').read().strip()
PROJECT_NAME = 'pynsd'

install_requires = []

setup(name='%s' % PROJECT_NAME,
      url='https://github.com/novutec/%s' % PROJECT_NAME,
      author="novutec Inc.",
      author_email='dev@novutec.com',
      keywords='nsd api',
      description="Library to connect and call command against new NSD >=4 control api.",
      license='Apache2',
      classifiers=[
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Operating System :: OS Independent',
          'Topic :: Software Development'
      ],
      version='%s' % VERSION,
      install_requires=install_requires,
      packages=['pynsd'],
      package_dir={'pynsd': 'src/pynsd'}
)
