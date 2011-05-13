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


"""
Dialog used for creating and editing events.
"""


import os.path

import wx

from timelinelib.db.interface import TimelineIOError
from timelinelib.db.objects import Event
from timelinelib.db.objects import TimePeriod
from timelinelib.domain.category import sort_categories
from timelinelib.gui.dialogs.categorieseditor import CategoriesEditor
from timelinelib.gui.dialogs.categoryeditor import CategoryEditor
from timelinelib.gui.utils import BORDER
from timelinelib.gui.utils import _display_error_message
from timelinelib.gui.utils import ID_ERROR
from timelinelib.gui.utils import _parse_text_from_textbox
from timelinelib.gui.utils import _set_focus_and_select
from timelinelib.gui.utils import time_picker_for
from timelinelib.gui.utils import TxtException
from timelinelib.utils import ex_msg
import timelinelib.gui.utils as gui_utils


class EventEditor(wx.Dialog):
    """Dialog used for creating and editing events."""

    def __init__(self, parent, config, title, timeline,
                 start=None, end=None, event=None):
        """
        Create a event editor dialog.

        The 'event' argument is optional. If it is given the dialog is used
        to edit this event and the controls are filled with data from
        the event and the arguments 'start' and 'end' are ignored.

        If the 'event' argument isn't given the dialog is used to create a
        new event, and the controls for start and end time are initially
        filled with data from the arguments 'start' and 'end' if they are
        given. Otherwise they will default to today.
        """
        wx.Dialog.__init__(self, parent, title=title, name="event_editor",
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.timeline = timeline
        self.event = event
        self.config = config
        self._create_gui()
        self.controller = EventEditorController(self, timeline, start, end, event)
        self.controller.initialize()
        self._set_initial_focus()

    def set_start(self, start):
        self.dtp_start.set_value(start)

    def get_start(self):
        try:
            try:
                return self.dtp_start.get_value()
            except ValueError, ex:
                raise TxtException(ex_msg(ex), self.dtp_start)
        except TxtException, ex:
            _display_error_message("%s" % ex.error_message)
            _set_focus_and_select(ex.control)


    def set_end(self, start):
        self.dtp_end.set_value(start)

    def get_end(self):
        try:
            if self.chb_period.IsChecked():
                try:
                    end_time = self.dtp_end.get_value()
                    return end_time
                except ValueError, ex:
                    raise TxtException(ex_msg(ex), self.dtp_end)
            else:
                return self.get_start()
        except TxtException, ex:
            _display_error_message("%s" % ex.error_message)
            _set_focus_and_select(ex.control)

    def set_show_period(self, show):
        self.chb_period.SetValue(show)
        self._show_to_time(show)

    def set_show_time(self, checked):
        self.chb_show_time.SetValue(checked)
        self.dtp_start.show_time(checked)
        self.dtp_end.show_time(checked)

    def set_show_add_more(self, visible):
        self.chb_add_more.Show(visible)
        self.chb_add_more.SetValue(False)

    def set_fuzzy(self, fuzzy):
        self.chb_fuzzy.SetValue(fuzzy)

    def get_fuzzy(self):
        return self.chb_fuzzy.GetValue()

    def set_locked(self, locked):
        self.chb_locked.SetValue(locked)

    def get_locked(self):
        return self.chb_locked.GetValue()

    def set_name(self, name):
        self.txt_text.SetValue(name)
        
    def get_name(self):
        return self.txt_text.GetValue().strip()
    
    def display_invalid_end(self, message):
        self._display_invalid_input(message, self.dtp_start)

    def display_invalid_name(self, message):
        self._display_invalid_input(message, self.txt_text)

    def _display_invalid_input(self, message, control):
        _display_error_message(message)
        _set_focus_and_select(control)  
            
    def set_category(self, category):
        self._update_categories(category)
        
    def get_category(self):
        selection = self.lst_category.GetSelection()
        category = self.lst_category.GetClientData(selection)
        return category

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

    def display_exception(self, e):
        gui_utils.handle_db_error_in_dialog(self, e)

    def close_or_clear_dialog(self):
        if self.chb_add_more.GetValue():
            self._clear_dialog()
            self.controller.clear()
        else:
            self._close()
                
    def _create_gui(self):
        main_box = self._create_main_box()
        self._create_add_more_checkbox(main_box)
        self._create_buttons(main_box)
        self.SetSizerAndFit(main_box)

    def _create_main_box(self):
        main_box = wx.BoxSizer(wx.VERTICAL)
        self._create_main_box_content(main_box)
        return main_box

    def _create_add_more_checkbox(self, main_box):
        self.chb_add_more = wx.CheckBox(self, label=_("Add more events after this one"))
        main_box.Add(self.chb_add_more, flag=wx.ALL, border=BORDER)

    def _create_buttons(self, main_box):
        button_box = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)
        self.Bind(wx.EVT_BUTTON, self._btn_ok_on_click, id=wx.ID_OK)
        main_box.Add(button_box, flag=wx.EXPAND|wx.ALL, border=BORDER)
    
    def _create_main_box_content(self, main_box):
        groupbox = wx.StaticBox(self, wx.ID_ANY, _("Event Properties"))
        main_box_content = wx.StaticBoxSizer(groupbox, wx.VERTICAL)
        self._create_detail_content(main_box_content)
        self._create_notebook_content(main_box_content)
        main_box.Add(main_box_content, flag=wx.EXPAND|wx.ALL, border=BORDER,
                     proportion=1)
         
    def _create_detail_content(self, main_box_content):
        details = self._create_details()
        main_box_content.Add(details, flag=wx.ALL|wx.EXPAND, border=BORDER)
    
    def _create_notebook_content(self, main_box_content):
        notebook = self._create_notebook()
        main_box_content.Add(notebook, border=BORDER, flag=wx.ALL|wx.EXPAND,
                           proportion=1)
    
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
        when_box.Add(self.lbl_to, flag=wx.ALIGN_CENTER_VERTICAL|wx.RESERVE_SPACE_EVEN_IF_HIDDEN)
        when_box.AddSpacer(BORDER)
        when_box.Add(self.dtp_end, proportion=1,
                     flag=wx.RESERVE_SPACE_EVEN_IF_HIDDEN)
        grid.Add(when_box)

    def _create_time_picker(self):
        return time_picker_for(self.timeline.get_time_type())(self, config=self.config)

    def _create_checkboxes(self, grid):
        grid.AddStretchSpacer()
        when_box_props = wx.BoxSizer(wx.HORIZONTAL)
        self._create_period_checkbox(when_box_props)
        if self.timeline.get_time_type().is_date_time_type():
            self._create_show_time_checkbox(when_box_props)
        self._create_fuzzy_checkbox(when_box_props)
        self._create_locked_checkbox(when_box_props)
        grid.Add(when_box_props)

    def _create_period_checkbox(self, box):
        self.chb_period = wx.CheckBox(self, label=_("Period"))
        self.Bind(wx.EVT_CHECKBOX, self._chb_period_on_checkbox, 
                  self.chb_period)
        box.Add(self.chb_period)

    def _create_show_time_checkbox(self, box):
        self.chb_show_time = wx.CheckBox(self, label=_("Show time"))
        self.Bind(wx.EVT_CHECKBOX, self._chb_show_time_on_checkbox,
                  self.chb_show_time)
        box.Add(self.chb_show_time)

    def _create_fuzzy_checkbox(self, box):
        self.chb_fuzzy = wx.CheckBox(self, label=_("Fuzzy"))
        self.Bind(wx.EVT_CHECKBOX, self._chb_fuzzy_on_checkbox, 
                  self.chb_fuzzy)
        box.Add(self.chb_fuzzy)
    
    def _create_locked_checkbox(self, box):
        self.chb_locked = wx.CheckBox(self, label=_("Locked"))
        self.Bind(wx.EVT_CHECKBOX, self._chb_locked_on_checkbox, 
                  self.chb_locked)
        box.Add(self.chb_locked)
            
    def _create_text_field(self, grid):
        self.txt_text = wx.TextCtrl(self, wx.ID_ANY, name="text")
        grid.Add(wx.StaticText(self, label=_("Text:")),
                 flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_text, flag=wx.EXPAND)

    def _create_categories_listbox(self, grid):
        self.lst_category = wx.Choice(self, wx.ID_ANY)
        grid.Add(wx.StaticText(self, label=_("Category:")),
                 flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.lst_category)
        self.Bind(wx.EVT_CHOICE, self._lst_category_on_choice,
                  self.lst_category)
        
    def _create_notebook(self):
        self.event_data = []
        notebook = wx.Notebook(self, style=wx.BK_DEFAULT)
        for data_id in self.timeline.supported_event_data():
            if data_id == "description":
                name = _("Description")
                editor_class = DescriptionEditor
            elif data_id == "icon":
                name = _("Icon")
                editor_class = IconEditor
            else:
                continue
            panel = wx.Panel(notebook)
            editor = editor_class(panel)
            notebook.AddPage(panel, name)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(editor, flag=wx.EXPAND, proportion=1)
            panel.SetSizer(sizer)
            self.event_data.append((data_id, editor))
        return notebook
     
    def _btn_ok_on_click(self, evt):
        self.controller.create_or_update_event()

    def _clear_dialog(self):
        for data_id, editor in self.event_data:
            editor.clear_data()
        
    def _chb_period_on_checkbox(self, e):
        self._show_to_time(e.IsChecked())

    def _chb_show_time_on_checkbox(self, e):
        self.dtp_start.show_time(e.IsChecked())
        self.dtp_end.show_time(e.IsChecked())

    def _chb_fuzzy_on_checkbox(self, e):
        pass

    def _chb_locked_on_checkbox(self, e):
        pass

    def _lst_category_on_choice(self, e):
        new_selection_index = e.GetSelection()
        if new_selection_index > self.last_real_category_index:
            self.lst_category.SetSelection(self.current_category_selection)
            if new_selection_index == self.add_category_item_index:
                self._add_category()
            elif new_selection_index == self.edit_categoris_item_index:
                self._edit_categories()
        else:
            self.current_category_selection = new_selection_index

    def _add_category(self):
        def create_category_editor():
            return CategoryEditor(self, _("Add Category"), self.timeline, None)
        def handle_success(dialog):
            if dialog.GetReturnCode() == wx.ID_OK:
                try:
                    self._update_categories(dialog.get_edited_category())
                except TimelineIOError, e:
                    gui_utils.handle_db_error_in_dialog(self, e)
        gui_utils.show_modal(create_category_editor,
                             gui_utils.create_dialog_db_error_handler(self),
                             handle_success)

    def _edit_categories(self):
        def create_categories_editor():
            return CategoriesEditor(self, self.timeline)
        def handle_success(dialog):
            try:
                prev_index = self.lst_category.GetSelection()
                prev_category = self.lst_category.GetClientData(prev_index)
                self._update_categories(prev_category)
            except TimelineIOError, e:
                gui_utils.handle_db_error_in_dialog(self, e)
        gui_utils.show_modal(create_categories_editor,
                             gui_utils.create_dialog_db_error_handler(self),
                             handle_success)

    def _show_to_time(self, show=True):
        self.lbl_to.Show(show)
        self.dtp_end.Show(show)
        
    def _fill_chb_show_time_control_with_data(self, event, start, end):
        if event == None:
            self.chb_show_time.SetValue(False)
        if start != None and end != None:
            time_period = TimePeriod(self.timeline.get_time_type(), start, end)
            has_nonzero_type = time_period.has_nonzero_time()
            self.chb_show_time.SetValue(has_nonzero_type)
        self.dtp_start.show_time(self.chb_show_time.IsChecked())
        self.dtp_end.show_time(self.chb_show_time.IsChecked())

    def _update_categories(self, select_category):
        # We can not do error handling here since this method is also called
        # from the constructor (and then error handling is done by the code
        # calling the constructor).
        self.lst_category.Clear()
        self.lst_category.Append("", None) # The None-category
        selection_set = False
        current_item_index = 1
        for cat in sort_categories(self.timeline.get_categories()):
            self.lst_category.Append(cat.name, cat)
            if cat == select_category:
                self.lst_category.SetSelection(current_item_index)
                selection_set = True
            current_item_index += 1
        self.last_real_category_index = current_item_index - 1
        self.add_category_item_index = self.last_real_category_index + 2
        self.edit_categoris_item_index = self.last_real_category_index + 3
        self.lst_category.Append("", None)
        self.lst_category.Append(_("Add new"), None)
        self.lst_category.Append(_("Edit categories"), None)
        if not selection_set:
            self.lst_category.SetSelection(0)
        self.current_category_selection = self.lst_category.GetSelection()

    def _set_initial_focus(self):
        self.dtp_start.SetFocus()

    def _close(self):
        """
        Close the dialog.

        Make sure that no events are selected after the dialog is closed.
        """
        # TODO: Replace with EventRuntimeData
        #self.timeline.reset_selected_events()
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
        description = wx.StaticText(self, label=_("Images will be scaled to fit inside a %ix%i box.") % self.MAX_SIZE)
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


class EventEditorController(object):

    def __init__(self, view, db, start, end, event):
        self.view = view
        self.db = db
        self.start = start
        self.end = end
        self.name = ""
        self.category = None
        self.event = event
        self.fuzzy = False
        self.locked = False
        
    def initialize(self):
        if self.event != None:
            self.start = self.event.time_period.start_time
            self.end = self.event.time_period.end_time
            self.name = self.event.text
            self.category = self.event.category
            self.view.set_event_data(self.event.data)
            self.fuzzy = self.event.fuzzy
            self.locked = self.event.locked
        self.view.set_start(self.start)
        self.view.set_end(self.end)
        self.view.set_name(self.name)
        self.view.set_category(self.category)
        self.view.set_show_period(self.end > self.start)
        self.view.set_show_time(self._event_has_nonzero_time())
        self.view.set_show_add_more(self.event == None)
        self.view.set_fuzzy(self.fuzzy)
        self.view.set_locked(self.locked)

    def create_or_update_event(self):
        try:
            self.start = self._validate_and_save_start(self.view.get_start())
            self.end = self._validate_and_save_end(self.view.get_end())
            self.name = self._validate_and_save_name(self.view.get_name())
            self.fuzzy = self.view.get_fuzzy()
            self.locked = self.view.get_locked()
            self.category = self.view.get_category()
            if self.event == None:
                self.event = Event(self.db, self.start, self.end, self.name, 
                                   self.category, self.fuzzy, self.locked)
            else:
                self.event.update(self.start, self.end, self.name, 
                                  self.category, self.fuzzy, self.locked)
            self.event.data = self.view.get_event_data()
            self._save_event_to_db()
            self.view.close_or_clear_dialog()
        except ValueError, ex:
            return
        
    def clear(self):
        self.name = ""
        self.event = None
        self.view.set_name(self.name)

    def _validate_and_save_start(self, start):
        if start == None:
            raise ValueError()
        return start

    def _validate_and_save_end(self, end):
        if end == None:
            raise ValueError()
        if end < self.start:
            self.view.display_invalid_end(_("End must be > Start"))
            raise ValueError()
        return end

    def _validate_and_save_name(self, name):
        if name == "":
            self.view.display_invalid_name(_("Field '%s' can't be empty.") % _("Text"))
            raise ValueError()
        return name
        
    def _save_event_to_db(self):
        try:
            self.db.save_event(self.event)
        except Exception, e:
            self.view.display_exception(e)
        
    def _event_has_nonzero_time(self):
        try:
            time_period = TimePeriod(self.db.get_time_type(), self.start, self.end)
            return time_period.has_nonzero_time()
        except Exception:
            return False
