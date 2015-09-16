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


def _(message):
    return message
import __builtin__
__builtin__.__dict__["_"] = _


from timelinelib.wxgui.dialogs.filenewdialog.filenewdialogcontroller import FileNewDialogController
from timelinelib.wxgui.framework import Dialog


class FileNewDialog(Dialog):

    """
    <BoxSizerVertical>
        <BoxSizerHorizontal
            proportion="1"
            border="LEFT|TOP|RIGHT"
        >
            <ListBox
                id="type_list"
                width="150"
                height="300"
                event_EVT_LISTBOX="on_selection_changed"
            />
            <StaticBoxSizerVertical
                width="300"
                proportion="1"
                label="$(DESCRIPTION)"
                border="LEFT"
            >
                <StaticText
                    id="description"
                    style="TE_READONLY"
                    proportion="1"
                    border="ALL"
                />
            </StaticBoxSizerVertical>
        </BoxSizerHorizontal>
        <StdDialogButtonSizer
            buttons="OK|CANCEL"
            border="TOP|BOTTOM"
        />
    </BoxSizerVertical>
    """

    DESCRIPTION = _("Description")

    def __init__(self, parent):
        Dialog.__init__(self, FileNewDialogController, parent=parent)
        self.controller.on_init()
        self.type_list.SetFocus()

    def SetItems(self, items):
        self.type_list.SetItems(items)

    def SelectItem(self, index):
        self.type_list.SetSelection(index)
        event = wx.CommandEvent()
        event.SetInt(index)
        self.controller.on_selection_changed(event)

    def SetDescription(self, text):
        self.description.SetLabel(text)
        self.description.Wrap(self.description.GetSize()[0])

    def GetSelection(self):
        return self.controller.get_selection()


if __name__ == "__main__":
    import wx
    app = wx.App()
    dialog = FileNewDialog(None)
    dialog.ShowModal()
    print("you chose: %s" % dialog.GetSelection())
