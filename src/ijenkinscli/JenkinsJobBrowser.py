'''
Created on Jul 23, 2015

@author: nkoester
'''
import signal

import urwid

from JenkinsWrapper import JenkinsWrapper
from URWIDElements import JenkinsInstanceNode, SearchBar,\
    ConsoleOutputPager, JenkinsOptionNode, JenkinsJobNode


class JenkinsJobBrowser():
    palette = [
        ('body', urwid.LIGHT_GRAY, urwid.BLACK),
        ('focus', urwid.LIGHT_GRAY, urwid.DARK_BLUE, 'standout'),
        ('selected', urwid.LIGHT_GRAY, urwid.DARK_BLUE, 'standout'),

        ('title', urwid.WHITE, urwid.DARK_BLUE),
        ('head_foot', urwid.WHITE, urwid.DARK_BLUE, ),
        ('key', 'yellow,bold', urwid.DARK_BLUE,),

        ('console', urwid.WHITE, urwid.DARK_BLUE),

        ('searchbar', urwid.WHITE, urwid.DARK_BLUE),

        ('SUCCESS', urwid.DARK_GREEN, urwid.DEFAULT),
        ('FAILED', urwid.DARK_RED, urwid.DEFAULT),
        ('UNSTABLE', urwid.DARK_CYAN, urwid.DEFAULT),
        ('ABORTED', urwid.DARK_MAGENTA, urwid.DEFAULT),
        ('DISABLED', urwid.LIGHT_GRAY, urwid.DEFAULT),
        ('NOTBUILT', urwid.DARK_BLUE, urwid.DEFAULT),
        ('BUILDIONG', urwid.BROWN, urwid.DEFAULT),

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

    def __init__(self, jenkins_settings):
        # set some class vars
        self.jenkins_settings = jenkins_settings
        self.jenkins_wrapper = JenkinsWrapper(self.jenkins_settings)

        self.openedconsole = False
        self.quit_confirm = False
        self.pager_term = None
        self.search_bar = None
        self.searchmode = False
        self.current_joblist = []
        self.search_result = []
        self.ragequit = False
        self.main_loop = None

        # ctrl+c support
        def signal_handler(signal, frame):
            self.ragequit = True
            raise urwid.ExitMainLoop()
        signal.signal(signal.SIGINT, signal_handler)

        # create the layout
        self.view = urwid.Frame(None, header=None, footer=None)
        self.reset_view()

    def reset_view(self):
        self.__refresh_jenkins()
        self.__refresh_header_footer()

    def __refresh_header_footer(self):
        self.header = urwid.AttrWrap(urwid.Text(self.get_header(self.jenkins_wrapper.settings.host, user=self.jenkins_wrapper.settings.auth[0] if self.jenkins_wrapper.settings.auth else "Anonymous")), 'head_foot')
        self.view.header = self.header

        self.user_input = urwid.Text("Status: ")
        self.status_bar = urwid.AttrWrap(urwid.Text(self.footer_text), 'head_foot')
        self.footer = urwid.Pile([self.status_bar, self.user_input], focus_item=0)
        self.view.footer = self.footer

    def __refresh_jenkins(self):
        # Actually load data from jenkins ...
        #         self.jenkins = self.create_jenkins(self.host, self.auth, self.proxies, self.ssl_verification)
        #         job_list_tree, self.current_joblist = self.get_available_jobs(self.jenkins)

        job_list_tree, self.current_joblist = self.jenkins_wrapper.get_available_jobs()
        self.topnode = JenkinsInstanceNode(job_list_tree)
        self.listbox = urwid.TreeListBox(urwid.TreeWalker(self.topnode))
        self.listbox.offset_rows = 1
        self.view.body = self.listbox

    def main(self):
        """Run the program."""

        self.main_loop = urwid.MainLoop(self.view, self.palette, unhandled_input=self.unhandled_input)
        self.main_loop.run()
        return self.ragequit

    def get_header(self, host, user="Anonymous"):
        return [('title', "Jenkins runnung at "), "  ", ('key', str(host)),
                "  |  ",
                ('title', 'Login: '), ('key', str(user))]

    def search_function(self, search_term):
        self.print_status("search for " + str(search_term))

        self.search_result = []
        for a_job, _ in self.current_joblist:
            if search_term.lower() in a_job.lower():
                self.search_result.append(a_job)

        self.print_status("res:" + str(self.search_result))

        if len(self.search_result) > 0:
            self.view.focus_position = "body"
            self.select_job(self.search_result[0])

#
#             elif k is 'n':
#                 self.select_job(self.search_result[1])
#             elif k is 'N':
#                 self.select_job(self.search_result[0])
#

    def show_search_bar(self):
        self.search_bar = SearchBar(self.hide_search_bar, self.search_function)
        self.view.footer = urwid.Pile([self.user_input, self.search_bar], focus_item=1)
        self.view.focus_position = "footer"
        self.print_status("Press 'ESC' to abort search...")

    def hide_search_bar(self):
        if self.search_bar:
            self.__refresh_header_footer()
            self.search_bar = None
            self.print_status("")
            self.searchmode = False
            self.view.focus_position = "body"

    def show_pager_term(self, text):
        self.pager_term = ConsoleOutputPager(self.hide_pager_term, text, self.main_loop)
#         self.main_loop.widget = urwid.Overlay(self.pager_term,
#                                          self.view,
#                                          'center',
#                                          ('relative', 100),
#                                          'middle',
#                                          ('relative', 100),
#                                          top=1,
#                                          bottom=2)
        self.view.body = self.pager_term
        self.print_status("Press 'q' to quit console view...")

    def hide_pager_term(self):
        if self.pager_term:
            #             self.loop.widget = self.loop.widget[0]
            self.view.body = self.listbox
            self.pager_term = None
            self.print_status("")

    def print_status(self, text):
        self.user_input.set_text(text)

    def append_status(self, text):
        self.user_input.set_text(self.user_input.get_text()[0] + text)

    def unhandled_input(self, k):
        #self.print_status("key: " + str(k))

        if self.quit_confirm:
            if k in ('q', 'Q'):
                raise urwid.ExitMainLoop()

            self.quit_confirm = False
            self.print_status("")
            return

        if self.searchmode:
            if k is 'enter':
                self.print_status("wooopp")
            elif k is 'tab':
                if self.view.focus == self.listbox:
                    self.view.focus_position = "footer"
                else:
                    self.view.focus_position = "body"

            return True

        if k in ('q', 'Q'):
            if not self.quit_confirm:
                self.quit_confirm = True
                self.print_status("Press 'q' again to quit...")

        elif k is '/':
            self.show_search_bar()
            self.searchmode = True

        elif k is 'f5':
            self.print_status("Refreshing...")
            self.reset_view()

        elif k is 'enter':
            selected_node = self.listbox.get_focus()[1]

            # Execute the selected option
            if isinstance(selected_node, JenkinsOptionNode):

                job_name = selected_node.get_job_name()
                chosen_option = selected_node.get_display_text()

                if chosen_option is JenkinsWrapper.OPTION_LABEL_JOB_INFO:
                    self.print_status("not implemented :(")

                elif chosen_option is JenkinsWrapper.OPTION_LABEL_BUILD:
                    self.print_status("Triggering build of '{}'...".format(job_name))
                    try:
                        result_code = self.jenkins_wrapper.jenkins_build(job_name)
                        if result_code < 400:
                            self.print_status("Build was successfully triggered, Code: " + str(result_code))
                    except Exception as error:
                        self.print_status("Error when building {}: {}".format(job_name, str(error)))

                elif chosen_option is JenkinsWrapper.OPTION_LABEL_LAST_BUILD_LOG:
                    self.show_pager_term(self.jenkins_wrapper.get_last_build_log(job_name))

            # Toggle folding using enter
            elif isinstance(selected_node, JenkinsJobNode) or \
                    isinstance(selected_node, JenkinsInstanceNode):
                widget = self.listbox.get_focus()[0]
                widget.expanded = not widget.expanded
                widget.update_expanded_icon()

            # Should never happen ...
            else:
                self.user_input.set_text("wut?!")

        return True

    def select_job(self, job_name):
        # TODO: allow to select a job
        self.print_status("focus: " + str(self.listbox))
#         self.listbox.set_focus(??)
