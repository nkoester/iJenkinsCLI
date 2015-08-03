'''
Created on Jul 23, 2015

@author: nkoester
'''
from __builtin__ import str
import datetime
import pprint
import signal
import traceback

import urwid
from urwid.treetools import TreeWalker

from JenkinsWrapper import JenkinsWrapper
from URWIDElements import JenkinsInstanceNode, SearchBar,\
    ConsoleOutputPager, JenkinsOptionNode, JenkinsJobNode
from URWIDElements import JenkinsInstanceTreeWidget
from URWIDElements import JenkinsJobTreeWidget
from URWIDElements import VimBindingTreeListBox
import URWIDElements


class JenkinsJobBrowser():

    OPTION_LABEL_JOB_INFO = "Job Info"
    OPTION_LABEL_BUILD = "Build"
    OPTION_LABEL_LAST_BUILD_LOG = "Last Build Log"

    COLOR_MAPPING = {
        'blue': 'SUCCESS',
        'green': 'SUCCESS',
        'red': 'FAILED',
        'yellow': 'UNSTABLE',
        'aborted': 'ABORTED',
        'disabled': 'DISABLED',
        'grey': 'NOTBUILT',
        'notbuilt': 'NOTBUILT',
        'building': 'BUILDIONG',
    }

    palette = [
        ('body', urwid.LIGHT_GRAY, urwid.BLACK),
        ('table_heading', urwid.LIGHT_GRAY + ",bold", urwid.BLACK),
        ('focus', urwid.LIGHT_GRAY + ",standout", urwid.BLACK),
        ('selected', urwid.DARK_MAGENTA, urwid.DARK_CYAN),

        #         ('title', urwid.WHITE, urwid.DARK_BLUE),
        #         ('head_foot', urwid.WHITE, urwid.DARK_BLUE, ),
        ('title', urwid.LIGHT_GRAY + ",standout", urwid.BLACK),
        ('head_foot', urwid.LIGHT_GRAY + ",standout", urwid.BLACK),
        ('key', urwid.BLACK, urwid.DARK_GREEN,),

        ('console', urwid.WHITE, urwid.DARK_BLUE),

        ('searchbar', urwid.WHITE, urwid.DARK_BLUE),
        ('search_result', urwid.DARK_GREEN + ",standout", urwid.WHITE),
        ('searchterm', urwid.DARK_GREEN, urwid.WHITE),

        ('SUCCESS', urwid.DARK_GREEN, urwid.DEFAULT),
        ('FAILED', urwid.DARK_RED, urwid.DEFAULT),
        ('UNSTABLE', urwid.DARK_CYAN, urwid.DEFAULT),
        ('ABORTED', urwid.DARK_MAGENTA, urwid.DEFAULT),
        ('DISABLED', urwid.LIGHT_GRAY, urwid.DEFAULT),
        ('NOTBUILT', urwid.DARK_BLUE, urwid.DEFAULT),
        ('BUILDIONG', urwid.BROWN, urwid.DEFAULT),

    ]

    table_head_text = [("table_heading", "ID"),
                       ("table_heading", " Available Jobs"),
                       ("table_heading", "Last Successful"),
                       ("table_heading", "Last Fail"),
                       ("table_heading", "Last Duration")]

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

    def __init__(self, jenkins_settings):
        # set some class vars
        self.jenkins_settings = jenkins_settings
        self.jenkins_wrapper = JenkinsWrapper(self.jenkins_settings)

        self.openedconsole = False
        self.quit_confirm = False
        self.pager_term = None
        self.search_bar = None
        self.searchmode = False
        self.current_jobdict = None
        self.search_result = []
        self.ragequit = False
        self.main_loop = None
        self.old_search_term = ""
        self.current_search_term = ""

        # ctrl+c support
        def signal_handler(signal, frame):
            self.ragequit = True
            raise urwid.ExitMainLoop()
        signal.signal(signal.SIGINT, signal_handler)

        # create the layout
        self.view = urwid.Frame(None, header=None, footer=None)
        self.__refresh_header_footer()
        self.__refresh_jenkins(init=True)

    def main(self):
        """Run the program."""

        self.main_loop = urwid.MainLoop(self.view, self.palette, unhandled_input=self.unhandled_input)
#         self.reset_view()

        def initial_update(y, z):
            self.__refresh_jenkins()
        self.main_loop.set_alarm_in(0.01, initial_update)
        self.main_loop.run()

        return self.ragequit

    def reset_view(self):
        self.__refresh_jenkins(init=True)
        self.__refresh_header_footer()
        self.__refresh_jenkins()

    def __refresh_header_footer(self):

        # headder
        self.head_connection = urwid.AttrWrap(urwid.Text(self.get_header(self.jenkins_wrapper.settings.host, user=self.jenkins_wrapper.settings.auth[0] if self.jenkins_wrapper.settings.auth else "Anonymous")), 'head_foot')
        self.head_table = URWIDElements.job_lines_to_column(self.table_head_text)
        self.header = urwid.Pile([self.head_connection, self.head_table], focus_item=0)
        self.view.header = self.header

        # footer
        self.user_input = urwid.Text("Status: ")
        self.status_bar = urwid.AttrWrap(urwid.Text(self.footer_text), 'head_foot')
        self.footer = urwid.Pile([self.status_bar, self.user_input], focus_item=0)
        self.view.footer = self.footer

    def __refresh_jenkins(self, init=False):
        if not init:
            # Actually load data from jenkins ...
            self.print_status("Refreshing Jobs - please wait...")
            self.main_loop.draw_screen()
            self.current_jobdict = self.jenkins_wrapper.get_detailed_joblist(self.status_function)
        else:
            self.current_jobdict = {"Loading...": {"color": "blue"}}
        self.topnode = JenkinsInstanceNode(self.jobdict2urwiddict(self.current_jobdict))
        self.listboxcontent = urwid.TreeWalker(self.topnode)

        self.listbox = VimBindingTreeListBox(self.listboxcontent, self.print_status)
        self.listbox.offset_rows = 1
        self.view.body = self.listbox

    def jobdict2urwiddict(self, detailed_jobdict):
        retval = {"name": [""], "children": []}

        for i, (job_name, info) in enumerate(detailed_jobdict.iteritems()):
            color = info['color']

            if '_anime' in color:
                color = color.split('_')[0]
                color = 'building'

            last_success = None
            last_fail = None
            last_dur = None

            try:
                last_success = info['lastSuccessfulBuild']['number'] if info['lastSuccessfulBuild'] else "N/A"
                last_fail = info['lastFailedBuild']['number'] if info['lastFailedBuild'] else "N/A"
                last_dur = info['lastSuccessfulBuild']['number'] if info['lastSuccessfulBuild'] else "N/A"

                for a_build in info['builds']:

                    if last_success and a_build['number'] == last_success:
                        last_success = datetime.datetime.fromtimestamp(a_build['info']['timestamp'] / 1000).strftime('%H:%M:%S %d.%m.%y')

                    if last_fail and a_build['number'] == last_fail:
                        last_fail = datetime.datetime.fromtimestamp(a_build['info']['timestamp'] / 1000).strftime('%H:%M:%S %d.%m.%y')

                    if last_dur and a_build['number'] == last_dur:
                        ms = a_build['info']['duration']

                        last_dur = "{:02}".format(int((ms / (1000.0 * 60.0 * 60.0)) % 24.0)) + ":" + \
                            "{:02}".format(int((ms / (1000.0 * 60.0)) % 60.0)) + ":" + \
                            "{:02}".format(int((ms / 1000.0) % 60.0))
            except Exception as e:
                pass

            retval['children'].append({"name": [str(i + 1), (self.COLOR_MAPPING[color], job_name), str(last_success), str(last_fail), str(last_dur)], "realname": str(job_name), "job_number": i + 1})
            retval['children'][i]['children'] = []
            retval['children'][i]['children'].append({"name": self.OPTION_LABEL_JOB_INFO})
            retval['children'][i]['children'].append({"name": self.OPTION_LABEL_BUILD})
            retval['children'][i]['children'].append({"name": self.OPTION_LABEL_LAST_BUILD_LOG})

        return retval

    def get_header(self, host, user="Anonymous"):
        return [('title', "Jenkins runnung at "), "  ", ('key', str(host)),
                "  |  ",
                ('title', 'Login: '), ('key', str(user))]

    def update_search_info(self, amount, extra=[]):
        status = ["Found {} search results for '".format(amount), ('searchterm', str(self.current_search_term)), "'  --  ", ('key', 'ESC'), " exit search mode"]
        status = status + extra
        self.print_status(status)

    def search_function(self, search_term):
        search_result = []
        for a_job, _ in self.current_jobdict.iteritems():
            if search_term.lower() in a_job.lower():
                search_result.append(a_job)

        self.update_search_info(len(search_result), extra=[", ", ('key', 'Enter'), " submit search"])

        # always select the first hit
        self.search_result_selection = -1
        self.select_next_searchresult()

        return search_result

    def execute_search(self, x, y):
        self.current_search_term = y
        self.search_result = self.search_function(self.current_search_term)
        self.search_result_selection = -1
        self.old_search_term = self.search_bar.get_search_term()
        self.highlight_search_results()

    def show_search_bar(self):
        self.search_bar = SearchBar()
        self.view.footer = urwid.Pile([self.user_input, self.search_bar], focus_item=1)
        self.view.focus_position = "footer"
        self.print_status("Press 'ESC' to abort search...")
        urwid.connect_signal(self.search_bar, 'change', self.execute_search)
        self.listbox.disable_keys()

    def hide_search_bar(self):
        if self.search_bar:
            self.listbox.enable_keys()
            self.topnode.reset_highlights()
            self.__refresh_header_footer()
            self.search_bar = None
            self.print_status("")
            self.current_search_term = ""
            self.searchmode = False
            self.view.focus_position = "body"

    def show_pager_term(self, text):
        self.pager_term = ConsoleOutputPager(self.hide_pager_term, text, self.main_loop)
        self.view.body = self.pager_term
        self.print_status("Press 'q' to quit console view...")

    def hide_pager_term(self):
        if self.pager_term:
            self.pager_term.change_focus(False)
            self.view.body = self.listbox
            self.pager_term = None
            self.print_status("")

    def status_function(self, message):
        self.print_status(message)
        self.main_loop.draw_screen()

    def print_status(self, text):
        self.user_input.set_text(text)

    def print_append_status(self, text):
        self.user_input.set_text(str(self.user_input.get_text()) + text)

    def append_status(self, text):
        self.user_input.set_text(self.user_input.get_text()[0] + text)

    def unhandled_input(self, k):
        if self.quit_confirm:
            if k in ('q', 'Q'):
                raise urwid.ExitMainLoop()

            self.quit_confirm = False
            self.print_status("")
            return

        if self.searchmode:
            self.highlight_search_results()
            if self.view.focus_position == "body":
                if k is 'enter':
                    self.hide_search_bar()
                    self._keypress_enter()
                if k is '/':
                    self.view.focus_position = "footer"
                elif k in ('f3', "n", 'j', 'down'):
                    self.select_next_searchresult()
                elif k in ('f4', "N", 'k', 'up'):
                    self.select_next_searchresult(revese=True)
                elif k in ('ctrl l', 'f8'):
                    self.search_bar.set_edit_text("")
                elif k in ('esc', 'q'):
                    self.hide_search_bar()
                elif k in ('h', 'l', 'left', 'right'):
                    pass
            else:
                if k is 'enter':
                    self.update_search_info(len(self.search_result), extra=[", ", ('key', 'n'), "/", ('key', 'N'), " or ", ('key', 'F3'), "/", ('key', 'F4'), " jump to next/previous search result"])
                    # Note: this is a hack as results off screen would not be
                    # highlighted. no idea why ...

                    self.view.focus_position = "body"

            return False

        if k in ('q', 'Q'):
            if not self.quit_confirm:
                self.quit_confirm = True
                self.print_status("Press 'q' again to quit...")

        elif k is '/':
            self.show_search_bar()
            self.searchmode = True

#        elif k in ('ctrl d',):
#            self.print_status("wooop")

        elif k is 'f5':
            self.reset_view()
            self.print_status("Refresh done.")

        elif k is 'enter':
            self._keypress_enter()
        return True

    def _keypress_enter(self):
        selected_node = self.listbox.get_focus()[1]

        # Execute the selected option
        if isinstance(selected_node, JenkinsOptionNode):

            job_name = selected_node.get_job_name()
            chosen_option = selected_node.get_display_text()

            if chosen_option is self.OPTION_LABEL_JOB_INFO:
                import pprint

                self.show_pager_term(pprint.pformat(self.current_jobdict[job_name], indent=4))

                #self.show_pager_term(pprint.pformat(self.jenkins_wrapper.get_jobs_details(job_name), indent=4))

            elif chosen_option is self.OPTION_LABEL_BUILD:
                self.print_status("Triggering build of '{}'...".format(job_name))
                try:
                    result_code = self.jenkins_wrapper.jenkins_build(job_name)
                    if result_code < 400:
                        self.print_status("Build was successfully triggered, Code: " + str(result_code))
                except Exception as error:
                    self.print_status("Error when building {}: {}".format(job_name, str(error)))

            elif chosen_option is self.OPTION_LABEL_LAST_BUILD_LOG:
                try:
                    log = self.jenkins_wrapper.get_last_build_log(job_name)
                    self.show_pager_term(log)
                except Exception as error:
                    self.print_status("Error when querying for log of {}: {}".format(job_name, str(error)))

        # Toggle folding using enter
        elif isinstance(selected_node, JenkinsJobNode) or \
                isinstance(selected_node, JenkinsInstanceNode):
            widget = self.listbox.get_focus()[0]
            widget.expanded = not widget.expanded
            widget.update_expanded_icon()

        # Should never happen ...
        else:
            self.user_input.set_text("wut?!")

    def highlight_search_results(self):
        self.topnode.reset_highlights()
        # make sure we have the instance root element
        self.topnode.visually_highlight_jobs(self.search_result)

    def select_next_searchresult(self, revese=False):
        # reset the view to draw the new results
        self.topnode.reset_highlights()

        if len(self.search_result) > 0:
            # increase the counter
            if revese:
                self.search_result_selection = (self.search_result_selection + -1) if self.search_result_selection > 0 else len(self.search_result) - 1
            else:
                self.search_result_selection = (self.search_result_selection + 1) if self.search_result_selection < len(self.search_result) - 1 else 0

            # obtain name of the job to highlight
            job_name = self.search_result[self.search_result_selection]

            self.view.body.set_focus(self.topnode.job_name2node(job_name))
            self.main_loop.draw_screen()
            self.highlight_search_results()

            selected_node = self.topnode.visually_highlight_jobs(job_name, style="focused")
