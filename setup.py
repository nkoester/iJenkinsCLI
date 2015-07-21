from setuptools import setup, find_packages

setup(name='iJenkinsCLI',
      version='0.0.1',
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

      install_requires=['docopt', 'urwid'],


      packages=find_packages('src'),
      package_dir={'': 'src'},


      entry_points={
          'console_scripts': [
              'iJenkins = ijenkinscli.ijenkinscli:startup',
          ]
      },

      test_suite='nose.collector',
      )
