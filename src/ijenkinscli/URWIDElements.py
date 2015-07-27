'''
Created on Jul 23, 2015

@author: nkoester
'''
import tempfile

import urwid


class ConsoleOutputPager(urwid.Terminal):

    def __init__(self, exit_function, content, main_loop):

        self.exit_function = exit_function

        new_file = tempfile.NamedTemporaryFile(delete=False)
        new_file.write(str(content) + "\n")
        new_file.flush()
        self.__super.__init__(["less", "-R", "-N", "-i", "+G", new_file.name], main_loop=main_loop)

    def keypress(self, size, key):
        if key in ('esc', 'q', 'Q'):
            self.exit_function()
        else:
            urwid.Terminal.keypress(self, size, key)

        return True


class SearchBar(urwid.Edit):

    def __init__(self, exit_function, search_function):
        self.exit_function = exit_function
        self.search_function = search_function
        self.__super.__init__("/")

    def get_search_term(self):
        return self.get_text()[0][1:]


class JenkinsInstanceTreeWidget(urwid.TreeWidget):

    """ Display widget for leaf nodes """

    def __init__(self, node):
        self.__super.__init__(node)
        # insert an extra AttrWrap for our own use
        self._w = urwid.AttrWrap(self._w, None)
#         self._w = urwid.AttrWrap(self._w, 'selected')
        self._w.focus_attr = 'focus'

    def get_display_text(self):
        return self.get_node().get_value()['name']

    def selectable(self):
        return True


class JenkinsJobTreeWidget(JenkinsInstanceTreeWidget):

    def selectable(self):
        return True


class JenkinsOptionTreeWidget(JenkinsInstanceTreeWidget):

    def selectable(self):
        return True


class JenkinsOptionNode(urwid.TreeNode):

    """ Meta storage for job option leaf nodes """

    def load_widget(self):
        return JenkinsOptionTreeWidget(self)

    def get_job_name(self):
        return self.get_parent().get_value()['name'][1]

    def get_display_text(self):
        return self.get_value()['name']


class JenkinsInstanceNode(urwid.ParentNode):

    """ Data storage object for interior/parent nodes """

    def load_widget(self):
        return JenkinsInstanceTreeWidget(self)

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
