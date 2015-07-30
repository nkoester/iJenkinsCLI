from setuptools import setup, find_packages

# Determine version
import os
version_file = os.path.realpath(__file__)
version_file = os.path.join(version_file[:version_file.rfind("/")], "VERSION")
version = open(version_file).read().strip()

setup(name='iJenkinsCLI',
      version=version,
      description='''
                  An interactive CLI for Jenkins.
                  ''',
      author='Norman Koester',
      author_email='nkoester@techfak.uni-bielefeld.de',
      license='LGPLv3+',
      url='https://github.com/nkoester/iJenkinsCLI',
      keywords=['Jenkins, CLI'],
      classifiers=['Programming Language :: Python'],

      setup_requires=['nose>=1.3', 'coverage'],

      install_requires=['docopt', 'urwid', 'autojenkins==1.0.0'],


      packages=find_packages('src'),
      package_dir={'': 'src'},


      entry_points={
          'console_scripts': [
              'iJenkins = ijenkinscli.ijenkinscli:startup',
          ]
      },

      test_suite='nose.collector',
      )
