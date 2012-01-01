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


import os.path

import wx

from timelinelib.editors.event import EventEditor
from timelinelib.repositories.dbwrapper import DbWrapperEventRepository
from timelinelib.wxgui.components.categorychoice import CategoryChoice
from timelinelib.wxgui.utils import BORDER
from timelinelib.wxgui.utils import _display_error_message
from timelinelib.wxgui.utils import _set_focus_and_select
from timelinelib.wxgui.utils import time_picker_for
import timelinelib.wxgui.utils as gui_utils

class EventEditorDialog(wx.Dialog):

    def __init__(self, parent, config, title, timeline,
                 start=None, end=None, event=None):
        wx.Dialog.__init__(self, parent, title=title, name="event_editor",
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.timeline = timeline
        self.config = config
        self._create_gui()
        self.controller = EventEditor(self)
        self.controller.edit(
            timeline.get_time_type(), DbWrapperEventRepository(timeline),
            start, end, event)

    def _create_gui(self):
        properties_box = self._create_properties_box()
        self._create_checkbox_add_more(properties_box)
        self._create_buttons(properties_box)
        self.SetSizerAndFit(properties_box)

    def _create_properties_box(self):
        properties_box = wx.BoxSizer(wx.VERTICAL)
        self._create_main_box_content(properties_box)
        return properties_box

    def _create_main_box_content(self, properties_box):
        groupbox = wx.StaticBox(self, wx.ID_ANY, _("Event Properties"))
        main_box_content = wx.StaticBoxSizer(groupbox, wx.VERTICAL)
        self._create_detail_content(main_box_content)
        self._create_notebook_content(main_box_content)
        properties_box.Add(main_box_content, flag=wx.EXPAND|wx.ALL, 
                           border=BORDER, proportion=1)

    def _create_detail_content(self, properties_box_content):
        details = self._create_details()
        properties_box_content.Add(details, flag=wx.ALL|wx.EXPAND, 
                                   border=BORDER)

    def _create_details(self):
        grid = wx.FlexGridSizer(4, 2, BORDER, BORDER)
        grid.AddGrowableCol(1)
        self._create_time_details(grid)
        self._create_checkboxes(grid)
        self._create_text_field(grid)
        self._create_categories_listbox(grid)
        return grid    

    def _create_time_details(self, grid):
        grid.Add(wx.StaticText(self, label=_("When:")),
                 flag=wx.ALIGN_CENTER_VERTICAL)
        self.dtp_start = self._create_time_picker()
        self.lbl_to = wx.StaticText(self, label=_("to"))
        self.dtp_end = self._create_time_picker()
        when_box = wx.BoxSizer(wx.HORIZONTAL)
        when_box.Add(self.dtp_start, proportion=1)
        when_box.AddSpacer(BORDER)
        flag = wx.ALIGN_CENTER_VERTICAL|wx.RESERVE_SPACE_EVEN_IF_HIDDEN
        when_box.Add(self.lbl_to, flag=flag)
        when_box.AddSpacer(BORDER)
        when_box.Add(self.dtp_end, proportion=1,
                     flag=wx.RESERVE_SPACE_EVEN_IF_HIDDEN)
        grid.Add(when_box)

    def _create_time_picker(self):
        time_type = self.timeline.get_time_type()
        return time_picker_for(time_type)(self, config=self.config)

    def _create_checkboxes(self, grid):
        grid.AddStretchSpacer()
        when_box = wx.BoxSizer(wx.HORIZONTAL)
        self.chb_period = self._create_period_checkbox(when_box)
        if self.timeline.get_time_type().is_date_time_type():
            self.chb_show_time = self._create_show_time_checkbox(when_box)
        self.chb_fuzzy = self._create_fuzzy_checkbox(when_box)
        self.chb_locked = self._create_locked_checkbox(when_box)
        self.chb_ends_today = self._create_ends_today_checkbox(when_box)
        grid.Add(when_box)

    def _create_period_checkbox(self, box):
        handler = self._chb_period_on_checkbox
        return self._create_chb(box, _("Period"), handler)

    def _chb_period_on_checkbox(self, e):
        self._show_to_time(e.IsChecked())

    def _create_show_time_checkbox(self, box):
        handler = self._chb_show_time_on_checkbox
        return self._create_chb(box, _("Show time"), handler)

    def _chb_show_time_on_checkbox(self, e):
        self.dtp_start.show_time(e.IsChecked())
        self.dtp_end.show_time(e.IsChecked())

    def _create_fuzzy_checkbox(self, box):
        handler = None
        return self._create_chb(box, _("Fuzzy"), handler)

    def _create_locked_checkbox(self, box):
        handler = self._chb_show_time_on_locked
        return self._create_chb(box, _("Locked"), handler)

    def _chb_show_time_on_locked(self, e):
        self.chb_ends_today.Enable(not self.chb_locked.GetValue())

    def _create_ends_today_checkbox(self, box):
        handler = None
        return self._create_chb(box, _("Ends today"), handler)

    def _create_chb(self, box, label, handler):
        chb = wx.CheckBox(self, label=label)
        if handler is not None:
            self.Bind(wx.EVT_CHECKBOX, handler, chb)
        box.Add(chb)
        return chb

    def _create_text_field(self, grid):
        self.txt_text = wx.TextCtrl(self, wx.ID_ANY, name="text")
        grid.Add(wx.StaticText(self, label=_("Text:")),
                 flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_text, flag=wx.EXPAND)

    def _create_categories_listbox(self, grid):
        self.lst_category = CategoryChoice(self, self.timeline)
        label = wx.StaticText(self, label=_("Category:"))
        grid.Add(label, flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.lst_category)
        self.Bind(wx.EVT_CHOICE, self.lst_category.on_choice, 
                  self.lst_category)

    def _create_notebook_content(self, properties_box_content):
        notebook = self._create_notebook()
        properties_box_content.Add(notebook, border=BORDER, 
                                   flag=wx.ALL|wx.EXPAND, proportion=1)

    def _create_notebook(self):
        self.event_data = []
        notebook = wx.Notebook(self, style=wx.BK_DEFAULT)
        for data_id in self.timeline.supported_event_data():
            self._add_editor(notebook, data_id)
        return notebook

    def _add_editor(self, notebook, data_id):
        editor_class_decription = self._get_editor_class_description(data_id)
        if editor_class_decription is None:
            return
        editor = self._create_editor(notebook, editor_class_decription)
        self.event_data.append((data_id, editor))

    def _get_editor_class_description(self, editor_class_id):
        editors = {"description" : (_("Description"), DescriptionEditor),
                   "icon" : (_("Icon"), IconEditor) }
        if editors.has_key(editor_class_id):
            return editors[editor_class_id]  
        else:
            return None

    def _create_editor(self, notebook, editor_class_decription):
        name, editor_class = editor_class_decription
        panel = wx.Panel(notebook)
        editor = editor_class(panel)
        notebook.AddPage(panel, name)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(editor, flag=wx.EXPAND, proportion=1)
        panel.SetSizer(sizer)
        return editor

    def _create_checkbox_add_more(self, properties_box):
        label = _("Add more events after this one")
        self.chb_add_more = wx.CheckBox(self, label=label)
        properties_box.Add(self.chb_add_more, flag=wx.ALL, border=BORDER)

    def _create_buttons(self, properties_box):
        button_box = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)
        self.Bind(wx.EVT_BUTTON, self._btn_ok_on_click, id=wx.ID_OK)
        properties_box.Add(button_box, flag=wx.EXPAND|wx.ALL, border=BORDER)

    def _btn_ok_on_click(self, evt):
        self.controller.create_or_update_event()

    def _show_to_time(self, show=True):
        self.lbl_to.Show(show)
        self.dtp_end.Show(show)

    def set_start(self, start):
        self.dtp_start.set_value(start)
    def get_start(self):
        return self.dtp_start.get_value()

    def set_end(self, start):
        self.dtp_end.set_value(start)
    def get_end(self):
        return self.dtp_end.get_value()

    def set_show_period(self, show):
        self.chb_period.SetValue(show)
        self._show_to_time(show)
    def get_show_period(self):
        return self.chb_period.IsChecked()

    def set_show_time(self, checked):
        self.chb_show_time.SetValue(checked)
        self.dtp_start.show_time(checked)
        self.dtp_end.show_time(checked)

    def get_fuzzy(self):
        return self.chb_fuzzy.GetValue()
    def set_fuzzy(self, fuzzy):
        self.chb_fuzzy.SetValue(fuzzy)

    def get_locked(self):
        return self.chb_locked.GetValue()
    def set_locked(self, locked):
        self.chb_locked.SetValue(locked)
        self.chb_ends_today.Enable(not self.chb_locked.GetValue())

    def get_ends_today(self):
        return self.chb_ends_today.GetValue()
    def set_ends_today(self, value):
        self.chb_ends_today.SetValue(value)

    def set_name(self, name):
        self.txt_text.SetValue(name)
    def get_name(self):
        return self.txt_text.GetValue().strip()

    def set_category(self, category):
        self.lst_category.select(category)
    def get_category(self):
        return self.lst_category.get()

    def set_event_data(self, event_data):
        for data_id, editor in self.event_data:
            if event_data.has_key(data_id):
                data = event_data[data_id]
                if data is not None:
                    editor.set_data(data)
    def get_event_data(self):
        event_data = {}
        for data_id, editor in self.event_data:
            data = editor.get_data()
            if data != None:
                event_data[data_id] = editor.get_data()
        return event_data

    def set_show_add_more(self, visible):
        self.chb_add_more.Show(visible)
        self.chb_add_more.SetValue(False)
    def get_show_add_more(self):
        return self.chb_add_more.GetValue()

    def set_focus(self, control_name):
        controls = {"start" : self.dtp_start, "text" : self.txt_text}
        if controls.has_key(control_name):
            controls[control_name].SetFocus()
        else:
            self.dtp_start.SetFocus()

    def display_invalid_start(self, message):
        self._display_invalid_input(message, self.dtp_start)

    def display_invalid_end(self, message):
        self._display_invalid_input(message, self.dtp_end)

    def display_invalid_name(self, message):
        self._display_invalid_input(message, self.txt_text)

    def _display_invalid_input(self, message, control):
        _display_error_message(message, self)
        _set_focus_and_select(control)  

    def display_db_exception(self, e):
        gui_utils.handle_db_error_in_dialog(self, e)

    def display_error_message(self, message):
        _display_error_message(message, self)

    def clear_dialog(self):
        self.controller.clear()
        for data_id, editor in self.event_data:
            editor.clear_data()

    def close(self):
        # TODO: Replace with EventRuntimeData
        self.EndModal(wx.ID_OK)


class DescriptionEditor(wx.TextCtrl):

    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, style=wx.TE_MULTILINE)

    def get_data(self):
        description = self.GetValue().strip()
        if description != "":
            return description
        return None

    def set_data(self, data):
        self.SetValue(data)

    def clear_data(self):
        self.SetValue("")


class IconEditor(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.MAX_SIZE = (128, 128)
        # Controls
        self.img_icon = wx.StaticBitmap(self, size=self.MAX_SIZE)
        label = _("Images will be scaled to fit inside a %ix%i box.")
        description = wx.StaticText(self, label=label % self.MAX_SIZE)
        btn_select = wx.Button(self, wx.ID_OPEN)
        btn_clear = wx.Button(self, wx.ID_CLEAR)
        self.Bind(wx.EVT_BUTTON, self._btn_select_on_click, btn_select)
        self.Bind(wx.EVT_BUTTON, self._btn_clear_on_click, btn_clear)
        # Layout
        sizer = wx.GridBagSizer(5, 5)
        sizer.Add(description, wx.GBPosition(0, 0), wx.GBSpan(1, 2))
        sizer.Add(btn_select, wx.GBPosition(1, 0), wx.GBSpan(1, 1))
        sizer.Add(btn_clear, wx.GBPosition(1, 1), wx.GBSpan(1, 1))
        sizer.Add(self.img_icon, wx.GBPosition(0, 2), wx.GBSpan(2, 1))
        self.SetSizerAndFit(sizer)
        # Data
        self.bmp = None

    def get_data(self):
        return self.get_icon()

    def set_data(self, data):
        self.set_icon(data)

    def clear_data(self):
        self.set_icon(None)

    def set_icon(self, bmp):
        self.bmp = bmp
        if self.bmp == None:
            self.img_icon.SetBitmap(wx.EmptyBitmap(1, 1))
        else:
            self.img_icon.SetBitmap(bmp)
        self.GetSizer().Layout()

    def get_icon(self):
        return self.bmp

    def _btn_select_on_click(self, evt):
        dialog = wx.FileDialog(self, message=_("Select Icon"),
                               wildcard="*", style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            if os.path.exists(path):
                image = wx.EmptyImage(0, 0)
                success = image.LoadFile(path)
                # LoadFile will show error popup if not successful
                if success:
                    # Resize image if too large
                    (w, h) = image.GetSize()
                    (W, H) = self.MAX_SIZE
                    if w > W:
                        factor = float(W) / float(w)
                        w = w * factor
                        h = h * factor
                    if h > H:
                        factor = float(H) / float(h)
                        w = w * factor
                        h = h * factor
                    image = image.Scale(w, h, wx.IMAGE_QUALITY_HIGH)
                    self.set_icon(image.ConvertToBitmap())
        dialog.Destroy()

    def _btn_clear_on_click(self, evt):
        self.set_icon(None)
