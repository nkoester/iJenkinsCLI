"""iJenkinsCLI

Usage:
  iJenkins <host> [(--user=<USER> --password=<PASSWORD>)][--proxy=<PROXY>][-ns]
  iJenkins -h | --help
  iJenkins --version

Options:
  -h, --help               this.
  --version                show version
  -u USER, --user=USER     username
  -p PWD, --password=PWD   password or API token
  -n, --no-color           do not use colored output
  -s, --noverification     disable SSL certificate verification

"""
from JenkinsJobBrowser import JenkinsJobBrowser
from JenkinsSettingsContainer import JenkinsSettingsContainer
from docopt import docopt


def get_proxy(args):
    """
    Return a proxy dictionary
    """
    if args is None or args['--proxy'] is None:
        return {"http": "", "https": ""}
    else:
        return {"http": args['--proxy'], "https": args['--proxy']}


def get_noverification(args):
    """
    Return desired status of verification
    """
    if args is None or args['--noverification'] is None:
        return False
    else:
        return True


def get_auth(args):
    """
    Return a tuple of (user, password) or None if no authentication
    """
    if args is None or args['--user'] is None:
        return None
    else:
        return (args['--user'], args['--password'])


def startup():
    options = docopt(__doc__, version='iJenkinsCLI 0.1.0')
    jenkins_settings = JenkinsSettingsContainer(options['<host>'],
                                                get_auth(options),
                                                get_proxy(options),
                                                (not get_noverification(options)))
    jjb = JenkinsJobBrowser(jenkins_settings)
    ragequit = jjb.main()
    if ragequit:
        print "Ctrl+C? Ouch! Why so rough?"
