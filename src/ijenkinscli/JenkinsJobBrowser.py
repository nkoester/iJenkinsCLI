'''
Created on Jul 23, 2015

@author: nkoester
'''
import pprint
import signal

import urwid
from urwid.treetools import TreeWalker

from JenkinsWrapper import JenkinsWrapper
from URWIDElements import JenkinsInstanceNode, SearchBar,\
    ConsoleOutputPager, JenkinsOptionNode, JenkinsJobNode
from URWIDElements import JenkinsInstanceTreeWidget
from URWIDElements import JenkinsJobTreeWidget


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
        ('focus', urwid.LIGHT_GRAY, urwid.DARK_BLUE, 'standout'),
        ('selected', urwid.DARK_MAGENTA, urwid.DARK_CYAN, 'standout'),

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
        self.current_jobdict = None
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
        self.current_jobdict = self.jenkins_wrapper.get_detailed_joblist()
        self.topnode = JenkinsInstanceNode(self.jobdict2urwiddict(self.current_jobdict))
        self.listboxcontent = urwid.TreeWalker(self.topnode)
        self.listbox = urwid.TreeListBox(self.listboxcontent)
        self.listbox.offset_rows = 1
        self.view.body = self.listbox

#         a = self.listbox.body
#         print a
#         assert isinstance(a, TreeWalker)
#
#         b = self.listbox.body.focus
#         print b
#         assert isinstance(b, JenkinsInstanceNode)
#
#         import pprint
#         job_name = "rst-converters-python-0.11-toolkit-nao-naoqi2.1-rsb0.11"
#         root = self.listbox.body.focus
#         for id in root.get_child_keys():
#             if root.get_child_node(id).get_job_name()[1] == job_name:
#                 print "ASDF:"
#                 pprint.pprint(root.get_child_node(id).__dict__)
#
#         print self.listbox.base_widget
#
#         import sys
#         sys.exit()

    def jobdict2urwiddict(self, detailed_jobdict):
        retval = {"name": "Available Jobs", "children": []}

        for i, (job_name, info) in enumerate(detailed_jobdict.iteritems()):

            color = info['color']

            if '_anime' in color:
                color = color.split('_')[0]
                color = 'building'

            retval['children'].append({"name": (self.COLOR_MAPPING[color], job_name)})
            retval['children'][i]['children'] = []
            retval['children'][i]['children'].append({"name": self.OPTION_LABEL_JOB_INFO})
            retval['children'][i]['children'].append({"name": self.OPTION_LABEL_BUILD})
            retval['children'][i]['children'].append({"name": self.OPTION_LABEL_LAST_BUILD_LOG})

        return retval

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

        search_result = []
        for a_job, _ in self.current_jobdict.iteritems():
            if search_term.lower() in a_job.lower():
                search_result.append(a_job)

        self.print_status("res:" + str(search_result))
        return search_result

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
            self.pager_term.change_focus(False)
            self.view.body = self.listbox
            self.pager_term = None
            self.print_status("")

    def print_status(self, text):
        self.user_input.set_text(text)

    def print_append_status(self, text):
        self.user_input.set_text(str(self.user_input.get_text()) + text)

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
                # self.print_status("wooopp")
                self.search_result = self.search_function(self.search_bar.get_search_term())
                self.search_result_selection = -1
                self.select_next_searchresult()
            elif k is 'f3':
                self.select_next_searchresult()
            elif k in ('esc', 'q'):
                self.hide_search_bar()
            elif k in ('tab', "/"):
                self.view.focus_position = "footer"

            return True

        if k in ('q', 'Q'):
            if not self.quit_confirm:
                self.quit_confirm = True
                self.print_status("Press 'q' again to quit...")

        elif k is '/':
            self.show_search_bar()
            self.searchmode = True

#         elif k is 'n':
#
#             import pprint
#             job_name = "rsb-opencv-0.11-toolkit-nao-naoqi2.1-rsb0.11"
#             root = self.listbox.body.focus
#             self.listbox.get_focus()
#             self.print_status(str(self.listboxcontent.get_next(self.listboxcontent.get_focus()[1])))
#             self.listboxcontent.set_focus(self.listboxcontent.get_focus()[1])
#             self.listbox.body.set_focus(self.listbox.get_focus()[1])
#             for i, id in enumerate(root.get_child_keys()):
#                 if root.get_child_node(id).get_job_name()[1] == job_name:
# self.print_status(pprint.pformat(root.get_child_node(id).__dict__, indent=4))
# self.print_status(str(i))
#                     return
# root.get_child_node(id)._value['name'] = ('selected', root.get_child_node(id)._value['name'][1])

        elif k is 'f5':
            self.print_status("Refreshing...")
            self.reset_view()

        elif k is 'enter':
            selected_node = self.listbox.get_focus()[1]

            # Execute the selected option
            if isinstance(selected_node, JenkinsOptionNode):

                job_name = selected_node.get_job_name()
                chosen_option = selected_node.get_display_text()

                if chosen_option is self.OPTION_LABEL_JOB_INFO:
                    import pprint
                    self.show_pager_term(pprint.pformat(self.jenkins_wrapper.get_jobs_details(job_name), indent=4))

                elif chosen_option is self.OPTION_LABEL_BUILD:
                    self.print_status("Triggering build of '{}'...".format(job_name))
                    try:
                        result_code = self.jenkins_wrapper.jenkins_build(job_name)
                        if result_code < 400:
                            self.print_status("Build was successfully triggered, Code: " + str(result_code))
                    except Exception as error:
                        self.print_status("Error when building {}: {}".format(job_name, str(error)))

                elif chosen_option is self.OPTION_LABEL_LAST_BUILD_LOG:
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

    def select_next_searchresult(self):
        self.view.focus_position = "body"

        if len(self.search_result) > 0:
            # increase the counter
            self.search_result_selection = (self.search_result_selection + 1) if self.search_result_selection < len(self.search_result) - 1 else 0

            job_name = self.search_result[self.search_result_selection]

            self.print_status(str(self.search_result) + " -- select: " + str(job_name))
            root = self.listbox.body.focus
            for i, id in enumerate(root.get_child_keys()):
                if root.get_child_node(id).get_job_name()[1] == job_name:
                    #                     self.print_append_status("found:" + str(i))
                    self.print_status(pprint.pformat(root.get_child_node(id).__dict__, indent=4))
#                     self.print_status("asdf " + str(i))
#                     self.view.body.set_focus(i)
#                     self.listboxcontent.set_focus(i)
                    return
#         self.listbox.set_focus(??)
