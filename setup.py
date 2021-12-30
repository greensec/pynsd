# coding: utf-8
"""
Copyright (c) 2007 - 2013 Novutec Inc. (http://www.novutec.com)
Copyright (c) 2014 - 2021 greenSec GmbH (https://www.greensec.de)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

@package pynsd
@copyright Copyright (c) 2007 - 2013 Novutec Inc. (http://www.novutec.com)
@copyright Copyright (c) 2014 - 2021 greenSec GmbH (https://www.greensec.de)
@license http://www.apache.org/licenses/LICENSE-2.0
"""

from setuptools import setup

VERSION = open('VERSION', 'r').read().strip()
PROJECT_NAME = 'pynsd'

install_requires = []

with open('README.md', 'r', 'utf-8') as f:
    readme = f.read()

setup(name='%s' % PROJECT_NAME,
    url='https://github.com/greensec/%s' % PROJECT_NAME,
    author="Stefan Meinecke",
    author_email='meinecke@greensec.de',
    keywords='nsd api',
    description="Library to connect and call command against new NSD >=4 control api.",
    long_description=readme,
    long_description_content_type='text/markdown',    
    package_data={'': ['LICENSE', ]},
    python_requires=">=3.5",
    license='Apache2',
    classifiers=[
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Software Development'
        'Topic :: Software Development :: Libraries',        
    ],
    version='%s' % VERSION,
    install_requires=install_requires,
    packages=['pynsd'],
    package_dir={'pynsd': 'src/pynsd'}
)
