import wx
import os.path


COPYRIGHT = """\
# Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014, 2015  Rickard Lindberg, Roger Lindberg
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

IMPORTS = """\
import wx

from timelinelib.wxgui.dialogs.%s.%scontroller import %sController


"""

TEST_IMPORTS = """\
from mock import Mock

from timelinetest import UnitTestCase
from timelinelib.wxgui.dialogs.%s.%s import %s
from timelinelib.wxgui.dialogs.%s.%scontroller import %sController


"""


DIALOG = """\
class %sGuiCreator(wx.Dialog):

    def __init__(self, title, parent=None):
        wx.Dialog.__init__(self, parent, title=title)
        self._create_gui()

    def _create_gui(self):
        pass


class %s(%sGuiCreator):

    def __init__(self, title, parent=None):
        %sGuiCreator.__init__(self, parent, title=title)
        self.controller = %sController(self)
"""


CONTROLLER = """\
class %sController(object):

    def __init__(self, view):
        self.view = view
"""

TEST = """\
class %sTestCase(UnitTestCase):

    def setUp(self):
        self.view = Mock(%s)
        self.controller = %sController(self.view)


class describe_controller_instantiation(%sTestCase):

    def test_controller_can_be_instantiated(self):
        self.assertTrue(self.controller is not None)

"""


def get_user_ack(question, parent=None):
    return wx.MessageBox(question, "Question",
                         wx.YES_NO | wx.CENTRE | wx.NO_DEFAULT, parent) == wx.YES


def create_init_file(path):
    f = open(os.path.join(path, "__init__.py"), "w")
    f.close()


def create_dialog_source_file(path, file_name, class_name):
    f = open(os.path.join(path, file_name + ".py"), "w")
    f.write(COPYRIGHT)
    f.write(IMPORTS % (file_name, file_name, class_name))
    f.write(DIALOG % (class_name, class_name, class_name, class_name, class_name))
    f.close()


def create_dialog_controller_source_file(path, file_name, class_name):
    f = open(os.path.join(path, file_name + "controller.py"), "w")
    f.write(COPYRIGHT)
    f.write(CONTROLLER % (class_name))
    f.close()


def create_test_source_file(path, file_name, class_name):
    f = open(os.path.join(path, file_name + ".py"), "w")
    f.write(COPYRIGHT)
    f.write(TEST_IMPORTS % (file_name, file_name, class_name, file_name, file_name, class_name))
    f.write(TEST % (class_name, class_name, class_name, class_name))
    f.close()


def create_source_files(path, file_name, class_name):
    exists = False
    if os.path.exists(path):
        exists = True
        if not get_user_ack("Module %s already exists\nOverwrite?" % path, None):
            return
    if not exists:
        os.makedirs(path)
    create_init_file(path)
    create_dialog_source_file(path, file_name, class_name)
    create_dialog_controller_source_file(path, file_name, class_name)


def create_test_files(path, file_name, class_name):
    path = path.replace("source", "test")
    path = path.replace("timelinelib", "specs")
    exists = False
    if os.path.exists(path):
        exists = True
        if not get_user_ack("Module %s already exists\nOverwrite?" % path, None):
            return
    if not exists:
        os.makedirs(path)
    create_init_file(path)
    create_test_source_file(path, file_name, class_name)


def create_py_files(class_name):
    file_name = class_name.lower()
    file_name = file_name.replace("_", "")
    path = os.path.join(os.getcwd(), "source", "timelinelib", "wxgui", "dialogs", file_name)
    create_source_files(path, file_name, class_name)
    create_test_files(path, file_name, class_name)


def get_class_name():
    dlg = wx.TextEntryDialog(None, "Enter the class name:", "Create a Dialog class", "")
    if dlg.ShowModal() == wx.ID_OK:
        return dlg.GetValue()
    else:
        raise Exception("Name is mandatory")


def execute():
    app = wx.App()
    app.MainLoop()
    try:
        class_name = get_class_name()
        if class_name == "":
            raise Exception("Name can't be empty")
        create_py_files(class_name)
    except Exception, ex:
        print ex
        pass
        print "None"


if __name__ == "__main__":
    execute()