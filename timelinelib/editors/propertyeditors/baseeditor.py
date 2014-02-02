# Copyright (C) 2009, 2010, 2011  Rickard Lindberg, Roger Lindberg
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


import wx


class BaseEditor(wx.Panel):

    def __init__(self, parent, editor):
        wx.Panel.__init__(self, parent)
        self.editor = editor
        self.data = None

    def create_gui(self):
        sizer = self.create_sizer()
        controls = self.create_controls()
        self.put_controls_in_sizer(sizer, controls)
        self.SetSizerAndFit(sizer)
        
    def get_data(self):
        return self.data.GetValue()

    def set_data(self, data):
        self.data.SetValue(data)

    def focus(self):
        if self.data is not None:
            self.data.SetFocus()
