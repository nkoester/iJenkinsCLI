'''
Created on Jul 23, 2015

@author: nkoester
'''
import tempfile

import urwid


class VimBindingTreeListBox(urwid.TreeListBox):

    def __init__(self, node, x):
        self.__super.__init__(node)
        self.x = x

    def keypress(self, size, key):
        if key is 'j':
            return urwid.TreeListBox.keypress(self, size, 'down')
        elif key is 'k':
            return urwid.TreeListBox.keypress(self, size, 'up')
        elif key is 'l':
            return urwid.TreeListBox.keypress(self, size, 'right')
        elif key is 'h':
            return urwid.TreeListBox.keypress(self, size, '-')
        elif key is 'left':
            return urwid.TreeListBox.keypress(self, size, '-')
        else:
            return urwid.TreeListBox.keypress(self, size, key)

    def void_keypress(self, size, key):
        if key in ('up', 'down', 'left', 'right', '+', '-'):
            return True
        else:
            return urwid.TreeListBox.keypress(self, size, key)

    def disable_keys(self):
        self.old_keypress = self.keypress
        self.keypress = self.void_keypress

    def enable_keys(self):
        self.keypress = self.old_keypress


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

    '''
    A simple Edit widget which starts with a '/' and provides a the text
    without this indicator when asked.
    '''

    def __init__(self):
        '''
        Override superclass init to add a leading "/".
        '''
        self.__super.__init__("/")

    def get_search_term(self):
        '''
        Returns the search string.
        '''
        return self.get_text()[0][1:]


class JenkinsInstanceTreeWidget(urwid.TreeWidget):

    '''
    Display widget for a Jenkins instance.
    '''

    def __init__(self, node):
        self.__super.__init__(node)
        # insert an extra AttrWrap for our own use
        self._w = urwid.AttrWrap(self._w, None)
        self._w.attr = 'table_heading'
        self.expanded_icon = urwid.SelectableIcon(' ', 0)
        self.update_expanded_icon()

    def get_display_text(self):
        return self.get_node().get_value()['name']

    def selectable(self):
        return False


COLOM_WIDTH = [4, 80, 21, 21, 15]


def job_lines_to_column(lines):
    cols = []
    seperator = (3, urwid.Text("|", wrap='clip'))
    for i, a_col in enumerate(lines):

        # in case we have more columns then defined widths
        if i >= len(COLOM_WIDTH):
            i = len(COLOM_WIDTH) - 1

        # our current width
        cur_width = COLOM_WIDTH[i]

        # shorten or extend the string
        if isinstance(a_col, tuple):
            #             attwrapped items
            if len(a_col[1]) >= cur_width:
                text = a_col[1][:cur_width - 3] + "..."
            else:
                text = "{: <{}s}".format(a_col[1], cur_width)
            text = (a_col[0], text)
        else:
            #             simple text items
            if len(a_col) >= cur_width:
                text = a_col[:cur_width - 3] + "..."
            else:
                text = "{: <{}s}".format(a_col, cur_width)

        # add to list
        cols.append(('weight', cur_width, urwid.Text(text, wrap='clip')))
        cols.append(seperator)

    return urwid.Columns(cols[:-1], dividechars=2, min_width=2)


class JenkinsJobTreeWidget(JenkinsInstanceTreeWidget):

    def __init__(self, node):
        self.__super.__init__(node)
        self._w.focus_attr = 'focus'
        self._w.attr = 'body'
        self.expanded_icon = urwid.SelectableIcon('-', 0)
        self.update_expanded_icon()

    def selectable(self):
        return True

    def get_indent_cols(self):
        return self.indent_cols * self.get_node().get_depth() - 2

    def load_inner_widget(self):
        return job_lines_to_column(self.get_display_text())


class JenkinsOptionTreeWidget(urwid.TreeWidget):

    def __init__(self, node):
        self.__super.__init__(node)
        self._w = urwid.AttrWrap(self._w, None)
        self._w.focus_attr = 'focus'

    def selectable(self):
        return True

    def get_display_text(self):
        return self.get_node().get_value()['name']


class JenkinsOptionNode(urwid.TreeNode):

    '''
    Meta storage for job option leaf nodes
    '''

    def load_widget(self):
        return JenkinsOptionTreeWidget(self)

    def get_job_name(self):
        return self.get_parent().get_job_name()

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

    def highlight_search_result(self, job_name):
        if isinstance(job_name, basestring):
            for i, job_id in enumerate(self.get_child_keys()):
                # if its in the list of results, visually highlight
                if self.get_child_node(job_id).get_job_name() is job_name:
                    self.get_child_node(job_id)._widget._w.attr = 'search_result'
            return True
        else:
            return False

    def job_name2node(self, job_name):
        for job_id in self.get_child_keys():
            # if its in the list of results, visually highlight
            if self.get_child_node(job_id).get_job_name() == job_name:
                return self.get_child_node(job_id)

    def visually_highlight_jobs(self, job_names, style='search_result'):

        selectees = []

        if isinstance(job_names, basestring):
            job_names = [job_names, ]

        for i, job_id in enumerate(self.get_child_keys()):
            # if its in the list of results, visually highlight
            if self.get_child_node(job_id).get_job_name() in job_names:
                # only if its visible
                if self.get_child_node(job_id)._widget:
                    self.get_child_node(job_id)._widget._w.attr = style
                selectees.append(self.get_child_node(job_id))

        return selectees

    def reset_highlights(self, style="body"):
        for i, job_id in enumerate(self.get_child_keys()):
            # only if its visible
            if self.get_child_node(job_id)._widget:
                self.get_child_node(job_id)._widget._w.attr = style


class JenkinsJobNode(JenkinsInstanceNode):

    def load_widget(self):
        wid = JenkinsJobTreeWidget(self)
        wid.expanded = False
        wid.update_expanded_icon()
        return wid

    def get_job_name(self):
        return self.get_value()['realname']
