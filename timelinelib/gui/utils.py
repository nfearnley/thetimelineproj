# Copyright (C) 2009, 2010  Rickard Lindberg, Roger Lindberg
#
# This file is part of Timeline.
#
# Timeline is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Timeline is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Timeline.  If not, see <http://www.gnu.org/licenses/>.


"""
Utility functions for working with GUI.
"""


import wx


# Border, in pixels, between controls in a window (should always be used when
# border is needed)
BORDER = 5
# Used by dialogs as a return code when a TimelineIOError has been raised
ID_ERROR = wx.NewId()


class TxtException(ValueError):
    """
    Thrown if a text control contains an invalid value.

    The constructor takes two arguments.

    The first is a text string containing any exception text.
    The seocond is a TextCtrl object.
    """
    def __init__(self, error_message, control):
        ValueError.__init__(self, error_message)
        self.error_message = error_message
        self.control = control


class WildcardHelper(object):
    """
    Help manage wildcards for wx.FileDialog.

    Tested in ../../tests/wildcard_helper.py.
    """

    def __init__(self, name, extensions):
        self.name = name
        self.ext_data = {}
        self.ext_names = []
        self._extract_ext_info(extensions)

    def wildcard_string(self):
        return "%s (%s)|%s" % (
            self.name,
            ", ".join(["*." + e for e in self.ext_names]),
            ";".join(["*." + e for e in self.ext_names]))

    def get_path(self, dialog):
        path = dialog.GetPath()
        for ext_name in self.ext_names:
            if path.endswith("." + ext_name):
                return path
        return "%s.%s" % (path, self.ext_names[0])

    def get_extension_data(self, path):
        split_path = path.split(".")
        if len(split_path) > 1:
            ext_name = split_path[-1]
            return self.ext_data.get(ext_name, None)
        return None
        
    def _extract_ext_info(self, extensions):
        for ext in extensions:
            if isinstance(ext, tuple):
                name, data = ext
                self.ext_data[name] = data
                self.ext_names.append(name)
            else:
                self.ext_names.append(ext)


def category_tree(category_list, parent=None, remove=None):
    """
    Transform flat list of categories to a tree based on parent attribute.

    The top-level categories have the given parent and each level in the tree
    is sorted.

    If remove is given then the subtree with remove as root will not be
    included.

    The tree is represented as a list of tuples, (cat, sub-tree), where cat is
    the parent category and subtree is the same tree representation of the
    children.
    """
    children = [child for child in category_list
                if (child.parent is parent and child is not remove)]
    sorted_children = sort_categories(children)
    tree = [(x, category_tree(category_list, x, remove))
            for x in sorted_children]
    return tree


def sort_categories(categories):
    sorted_categories = list(categories)
    sorted_categories.sort(cmp, lambda x: x.name.lower())
    return sorted_categories


def show_modal(fn_create_dialog, fn_handle_db_error, fn_success=None):
    """Show a modal dialog using error handling pattern."""
    try:
        dialog = fn_create_dialog()
    except TimelineIOError, e:
        fn_handle_db_error(e)
    else:
        dialog_result = dialog.ShowModal()
        if dialog_result == ID_ERROR:
            fn_handle_db_error(dialog.error)
        elif fn_success:
            fn_success(dialog)
        dialog.Destroy()


def create_dialog_db_error_handler(dialog):
    def handler(error):
        handle_db_error_in_dialog(dialog, error)
    return handler


def handle_db_error_in_dialog(dialog, error):
    if dialog.IsShown():
        # Close the dialog and let the code that created it handle the error.
        # Eventually this error will end up in the main frame (which is the
        # only object which can handle the error properly).
        dialog.error = error
        dialog.EndModal(ID_ERROR)
    else:
        # Re-raise the TimelineIOError exception and let the code that created
        # the dialog handle the error.
        raise error


def _set_focus_and_select(ctrl):
    ctrl.SetFocus()
    if hasattr(ctrl, "SelectAll"):
        ctrl.SelectAll()


def _parse_text_from_textbox(txt, name):
    """
    Return a text control field.

    If the value is an empty string the method raises a ValueError
    exception and sets focus on the control.

    If the value is valid the text in the control is returned
    """
    data = txt.GetValue().strip()
    if len(data) == 0:
        raise TxtException, (_("Field '%s' can't be empty.") % name, txt)
    return data


def _display_error_message(message, parent=None):
    """Display an error message in a modal dialog box"""
    dial = wx.MessageDialog(parent, message, _("Error"), wx.OK | wx.ICON_ERROR)
    dial.ShowModal()


def _ask_question(question, parent=None):
    """Ask a yes/no question and return the reply."""
    return wx.MessageBox(question, _("Question"),
                         wx.YES_NO|wx.CENTRE|wx.NO_DEFAULT, parent)


def _step_function(x_value):
    """
    A step function.

            {-1   when x < 0
    F(x) =  { 0   when x = 0
            { 1   when x > 0
    """
    y_value = 0
    if x_value < 0:
        y_value = -1
    elif x_value > 0:
        y_value = 1
    return y_value


def set_wait_cursor(parent):
    parent.SetCursor(wx.StockCursor(wx.CURSOR_WAIT))
    
    
def set_default_cursor(parent):
    parent.SetCursor(wx.StockCursor(wx.CURSOR_DEFAULT))    
