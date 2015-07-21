"""ConsoleJenkins CLI

Usage:
  jenkins <host> [(--user=<USER> --password=<PASSWORD>)][--proxy=<PROXY>][-ns]
  jenkins -h | --help

Options:
  -h, --help               show this help message and exit
  -u USER, --user=USER     username
  -p PWD, --password=PWD   password or API token
  -n, --no-color           do not use colored output
  -s, --noverification     disable SSL certificate verification

"""
from docopt import docopt
import sys
from autojenkins import Jenkins, jobs

import signal
import curses
import pydoc
import getpass
import subprocess
from subprocess import PIPE
import tempfile

import urwid
import os

JOB_INFO = "Job Info"
BUILD = "Build"
LAST_BUILD_LOG = "Last Build Log"


class ConsoleOutputPager(urwid.Terminal):

    def __init__(self, content):
        new_file = tempfile.NamedTemporaryFile(delete=False)
        new_file.write(str(content) + "\n")
        new_file.flush()
        self.__super.__init__(["less", new_file.name])

        #pydoc.pipepager(str(content), cmd='less -R -N -i +G')
        # main_loop.screen.clear()

        #global main_loop
        #self.__super.__init__(["/usr/bin/less -R -N -i +G /tmp/asdf"], main_loop=main_loop)


class JenkinsJobTreeWidget(urwid.TreeWidget):

    """ Display widget for leaf nodes """

    def __init__(self, node):
        self.__super.__init__(node)
        # insert an extra AttrWrap for our own use
        self._w = urwid.AttrWrap(self._w, None)
        self._w.focus_attr = 'focus'

    def get_display_text(self):
        return self.get_node().get_value()['name']

    def selectable(self):
        return True


class JenkinsOptionTreeWidget(JenkinsJobTreeWidget):

    def get_display_text(self):
        return self.get_node().get_value()['name']

    def keypress(self, size, key):
        """allow subclasses to intercept keystrokes"""
        key = self.__super.keypress(size, key)
        if key:
            key = self.unhandled_keys(size, key)
        return key

    def unhandled_keys(self, size, key):
        if key == " ":
            pass
        else:
            return key


class JenkinsOptionNode(urwid.TreeNode):

    """ Meta storage for job option leaf nodes """

    def load_widget(self):
        return JenkinsOptionTreeWidget(self)

    def get_job_name(self):
        return self.get_parent().get_value()['name']

    def get_display_text(self):
        return self.get_value()['name']


class JenkinsInstanceNode(urwid.ParentNode):

    """ Data storage object for interior/parent nodes """

    def load_widget(self):
        return JenkinsJobTreeWidget(self)

    def load_child_keys(self):
        data = self.get_value()
        return range(len(data['children']))

    def load_child_node(self, key):
        """Return either an JenkinsOptionNode or JenkinsJobNode"""
        childdata = self.get_value()['children'][key]
        childdepth = self.get_depth() + 1
        if 'children' in childdata:
            childclass = JenkinsJobNode
        else:
            childclass = JenkinsOptionNode
        return childclass(childdata, parent=self, key=key, depth=childdepth)


class JenkinsJobNode(JenkinsInstanceNode):

    def load_widget(self):
        wid = JenkinsJobTreeWidget(self)
        wid.expanded = False
        wid.update_expanded_icon()
        return wid

    def get_job_name(self):
        return self.get_value()['name']


class JenkinsJobBrowser:
    palette = [
        ('body', 'light gray', 'black'),
        ('focus', 'light gray', 'dark blue', 'standout'),
        ('head', 'yellow', 'black', 'standout'),

        ('title', 'white', 'dark blue'),
        ('head_foot', 'white', 'dark blue', ),
        ('key', 'yellow,bold', 'dark blue',),

        ('console', 'white', 'dark blue'),
    ]
    footer_text = [
        "   -",
        ('title', "Jenkins Job Browser"), "-    ",
        ('key', "(PAGE) UP/DOWN"), ",",
        ('key', "LEFT/RIGHT"), ",",
        ('key', "HOME/END"),
        " | ",
        ('key', "Enter"), ",",
        ('key', "+"), ",",
        ('key', "-"),
        " | ",
        ('key', "Q"),
    ]
    COLOR_MEANING = {
        'blue': ('1;32', 'SUCCESS'),
        'green': ('1;32', 'SUCCESS'),
        'red': ('1;31', 'FAILED'),
        'yellow': ('1;33', 'UNSTABLE'),
        'aborted': ('1;37', 'ABORTED'),
        'disabled': ('0;37', 'DISABLED'),
        'grey': ('1;37', 'NOT BUILT'),
        'notbuilt': ('1;37', 'NOT BUILT'),
    }

    def __init__(self, options):

        self.jenkins = self.create_jenkins(options)
        data = self.get_available_jobs(self.jenkins)

        self.topnode = JenkinsInstanceNode(data)

        self.header = urwid.AttrWrap(urwid.Text(self.get_header(options['<host>'], user=options['--user'] if options['--user'] else "Anonymous")), 'head_foot')

        self.listbox = urwid.TreeListBox(urwid.TreeWalker(self.topnode))
        self.listbox.offset_rows = 1

        self.user_input = urwid.Text("Status: ")
        self.status_bar = urwid.AttrWrap(urwid.Text(self.footer_text), 'head_foot')
        self.footer = urwid.Pile([self.status_bar, self.user_input], focus_item=0)

        self.view = urwid.Frame(
            urwid.AttrWrap(self.listbox, 'body'),
            header=urwid.AttrWrap(self.header, 'head'),
            footer=self.footer)

    def get_header(self, host, user="Anonymous"):
        return [('title', "Jenkins runnung at "), "  ", ('key', str(host)),
                "  |  ",
                ('title', 'Login: '), ('key', str(user))]

    def show_console(self, text):
        term = ConsoleOutputPager(text)
        self.loop.widget = urwid.Overlay(urwid.AttrWrap(term, 'console'),
                                         self.view,
                                         'left',
                                         ('relative', 50),
                                         'top',
                                         ('relative', 50),
                                         top=1)

    def print_status(self, text):
        self.user_input.set_text(text)

    def unhandled_input(self, k):
        if k in ('q', 'Q'):
            raise urwid.ExitMainLoop()
        elif k is 'enter':

            selected_node = self.listbox.get_focus()[1]
            job_name = selected_node.get_job_name()

            self.user_input.set_text("Selected job: {}".format(job_name))

            if isinstance(selected_node, JenkinsOptionNode):
                chosen_option = selected_node.get_display_text()
                self.user_input.set_text("Selected job/option: {} / {} ".format(job_name, chosen_option))

                if chosen_option is JOB_INFO:
                    #self.print_status("not implemented :(")
                    pass

                elif chosen_option is BUILD:
                    if self.jenkins_build(job_name):
                        self.print_status("Build was triggered!")

                elif chosen_option is LAST_BUILD_LOG:
                    self.show_last_build_log(job_name)
                    # self.show_console(self.jenkins.last_build_console(job_name));

            elif isinstance(selected_node, JenkinsJobNode):
                widget = self.listbox.get_focus()[0]
                widget.expanded = not widget.expanded
                widget.update_expanded_icon()

            else:
                self.user_input.set_text("wut?!")

                # self.show_console(self.jenkins.last_build_console(self.listbox.focus.get_display_text()));

    def main(self):
        """Run the program."""

        self.loop = urwid.MainLoop(self.view, self.palette, unhandled_input=self.unhandled_input)
        global main_loop
        main_loop = self.loop
        self.loop.run()

    def show_last_build_log(self, job_name):
        #new_file = tempfile.NamedTemporaryFile(delete=False)
        #new_file.write(str(content) + "\n")
        # new_file.flush()
        content = self.jenkins.last_build_console(job_name)
        pydoc.pipepager(str(content), cmd='less -R -N -i +G')
        main_loop.screen.clear()

    def jenkins_build(self, job_name):
        try:
            self.print_status("Triggering build of '{}'...".format(job_name))
            response = self.jenkins.build(job_name)
            return response.status_code < 400
        except (jobs.JobInexistent, jobs.JobNotBuildable) as error:
            self.print_status("Error when building {}: {}".format(job_name, str(error)))
            return False
        except (jobs.HttpForbidden, jobs.HttpUnauthorized) as error:
            self.print_status("Error when building {}: {}".format(job_name, str(error)))
            return False

    def joblist_interactive(self, joblist, color=True, raw=False):
        if color:
            FORMAT = "\033[{0}m{1}\033[0m"
            position = 0
        else:
            FORMAT = "{0:<10} {1}"
            position = 1

        prettyjobs = []
        for name, color in joblist:
            if '_' in color:
                color = color.split('_')[0]
                building = True
            else:
                building = False
            prefix = '' if raw else '* ' if building else '  '
            prettyjobs.append(FORMAT.format(COLOR_MEANING[color][position], name))
        return prettyjobs, joblist

    def get_available_jobs(self, jenkins):
        retval = {"name": "Available Jobs",
                  "children": []}
        for i, (job_name, color) in enumerate(jenkins.all_jobs()):
            if '_' in color:
                color = color.split('_')[0]
                building = True
            else:
                building = False

            retval['children'].append({"name": job_name})
            retval['children'][i]['children'] = []
            retval['children'][i]['children'].append({"name": JOB_INFO})
            retval['children'][i]['children'].append({"name": BUILD})
            retval['children'][i]['children'].append({"name": LAST_BUILD_LOG})

        return retval

    def create_jenkins(self, options):
        return Jenkins(options['<host>'],
                       proxies=get_proxy(options),
                       auth=get_auth(options),
                       verify_ssl_cert=(not get_verification(options)))


def get_proxy(args):
    """
    Return a proxy dictionary
    """
    if args is None or args['--proxy'] is None:
        return {"http": "", "https": ""}
    else:
        return {"http": args['--proxy'], "https": args['--proxy']}


def get_verification(args):
    """
    Return desired status of verification
    """
    if args is None or args['--noverification'] is None:
        return {"noverification": False, }
    else:
        return {"noverification": True, }


def get_auth(args):
    """
    Return a tuple of (user, password) or None if no authentication
    """
    if args is None or args['--user'] is None:
        return None
    else:
        return (args['--user'], args['--password'])


main_loop = None


def startup():

    options = docopt(__doc__, version='autojenkins 0.9.0-docopt')
    JenkinsJobBrowser(options).main()
