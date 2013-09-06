from setuptools import setup, find_packages

VERSION = open('VERSION', 'r').read().strip()
PROJECT_NAME = 'pynsd'

install_requires = [
    'zerorpc',
    'argparse'
]

setup(name='%s' % PROJECT_NAME,
      url='https://github.com/novutec/%s' % PROJECT_NAME,
      author="novutec Inc.",
      author_email='dev@novutec.com',
      keywords='nsd api',
      description="""Library to connect and call command against new NSD >=4 control api.
Additional zerorpc based RPC daemon to create, update and delete new zones dynamically.""",
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
      package_dir={'pynsd': 'src/pynsd'},
      data_files=[('/etc', ['src/etc/pynsd-rpcd.cfg'])],
      scripts=['src/bin/pynsd-rpcd']
)
