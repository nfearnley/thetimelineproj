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


from timelinelib.repositories.dbwrapper import DbWrapperEventRepository
from timelinelib.wxgui.dialogs.editcontainerdialog.editcontainerdialog import EditContainerDialog
from timelinelib.wxgui.dialogs.editeventdialog.editeventdialogcontroller import EditEventDialogController
from timelinelib.wxgui.framework import Dialog
from timelinelib.wxgui.utils import _set_focus_and_select
import timelinelib.wxgui.utils as gui_utils

import wx


class EditEventDialog(Dialog):

    """
    <BoxSizerVertical>
        <StaticBoxSizerVertical label="$(properties_label)" border="ALL" proportion="1">
            <FlexGridSizer columns="2" growableColumns="1" border="ALL">
                <StaticText align="ALIGN_CENTER_VERTICAL" label="$(when_label)" />
                <BoxSizerHorizontal>
                    <TimePicker
                        name="start_time"
                        time_type="$(time_type)"
                        config="$(config)"
                    />
                    <Spacer />
                    <StaticText
                        label="$(to_label)"
                        name="to_label"
                        align="ALIGN_CENTER_VERTICAL"
                    />
                    <Spacer />
                    <TimePicker
                        name="end_time"
                        time_type="$(time_type)"
                        config="$(config)"
                    />
                </BoxSizerHorizontal>
                <StaticText align="ALIGN_CENTER_VERTICAL" label="" />
                <FlexGridSizer rows="1">
                    <CheckBox
                        name="period_checkbox"
                        event_EVT_CHECKBOX="on_period_checkbox_changed"
                        label="$(period_checkbox_text)" />
                    <CheckBox
                        name="show_time_checkbox"
                        event_EVT_CHECKBOX="on_show_time_checkbox_changed"
                        label="$(show_time_checkbox_text)"
                    />
                    <CheckBox
                        name="fuzzy_checkbox"
                        label="$(fuzzy_checkbox_text)"
                    />
                    <CheckBox
                        name="locked_checkbox"
                        event_EVT_CHECKBOX="on_locked_checkbox_changed"
                        label="$(locked_checkbox_text)"
                    />
                    <CheckBox
                        name="ends_today_checkbox"
                        label="$(ends_today_checkbox_text)"
                    />
                </FlexGridSizer>
                <StaticText align="ALIGN_CENTER_VERTICAL" label="$(text_label)" />
                <TextCtrl name="name" />
                <StaticText align="ALIGN_CENTER_VERTICAL" label="$(category_label)" />
                <CategoryChoice
                    name="category_choice"
                    allow_add="True"
                    allow_edit="True"
                    timeline="$(db)"
                    align="ALIGN_LEFT"
                />
                <StaticText align="ALIGN_CENTER_VERTICAL" label="$(container_label)" />
                <Choice
                    name="containers_choice"
                    event_EVT_CHOICE="on_container_changed"
                    align="ALIGN_LEFT"
                />
            </FlexGridSizer>
            <Notebook name="notebook" style="BK_DEFAULT" border="LEFT|RIGHT|BOTTOM" proportion="1">
                <DescriptionEditor
                    name="description"
                    notebookLabel="$(page_description)"
                    editor="$(self)"
                    proportion="1"
                />
                <IconEditor
                    name="icon"
                    notebookLabel="$(page_icon)"
                    editor="$(self)"
                    proportion="1"
                />
                <AlertEditor
                    name="alert"
                    notebookLabel="$(page_alert)"
                    editor="$(self)"
                    proportion="1"
                />
                <HyperlinkEditor
                    name="hyperlink"
                    notebookLabel="$(page_hyperlink)"
                    editor="$(self)"
                    proportion="1"
                />
                <ProgressEditor
                    name="progress"
                    notebookLabel="$(page_progress)"
                    editor="$(self)"
                    proportion="1"
                />
            </Notebook>
        </StaticBoxSizerVertical>
        <CheckBox
            name="add_more_checkbox"
            label="$(add_more_label)"
            border="LEFT|RIGHT"
        />
        <DialogButtonsOkCancelSizer
            event_EVT_BUTTON__ID_OK="on_ok_clicked"
            border="ALL"
        />
    </BoxSizerVertical>
    """

    def __init__(self, parent, config, title, db, start=None, end=None, event=None):
        self.timeline = db
        self.config = config
        self.start = start
        self.event = event
        Dialog.__init__(self, EditEventDialogController, parent, {
            "self": self,
            "db": db,
            "time_type": db.get_time_type(),
            "config": config,
            "properties_label": _("Event Properties"),
            "when_label": _("When:"),
            "period_checkbox_text": _("Period"),
            "show_time_checkbox_text": _("Show time"),
            "fuzzy_checkbox_text": _("Fuzzy"),
            "locked_checkbox_text": _("Locked"),
            "ends_today_checkbox_text": _("Ends today"),
            "to_label": _("to"),
            "text_label": _("Text:"),
            "category_label": _("Category:"),
            "container_label": _("Container:"),
            "page_description": _("Description"),
            "page_icon": _("Icon"),
            "page_alert": _("Alert"),
            "page_hyperlink": _("Hyperlink"),
            "page_progress": _("Progress"),
            "add_more_label": _("Add more events after this one"),
        }, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        self.controller.on_init(
            config,
            db.get_time_type(),
            DbWrapperEventRepository(db),
            db,
            start,
            end,
            event)
        self.SetMinSize((800, -1))
        self.Fit()
        self.SetMinSize(self.GetSize())

    def GetStart(self):
        return self.start_time.get_value()

    def SetStart(self, value):
        self.start_time.set_value(value)

    def GetEnd(self):
        return self.end_time.get_value()

    def SetEnd(self, value):
        self.end_time.set_value(value)

    def GetShowPeriod(self):
        return self.period_checkbox.GetValue()

    def SetShowPeriod(self, value):
        self.period_checkbox.SetValue(value)
        self.ShowToTime(value)

    def ShowToTime(self, show):
        self.to_label.Show(show)
        self.end_time.Show(show)

    def GetShowTime(self):
        return self.show_time_checkbox.GetValue()

    def SetShowTime(self, value):
        self.show_time_checkbox.SetValue(value)
        self.start_time.show_time(value)
        self.end_time.show_time(value)

    def GetFuzzy(self):
        return self.fuzzy_checkbox.GetValue()

    def SetFuzzy(self, value):
        self.fuzzy_checkbox.SetValue(value)

    def GetLocked(self):
        return self.locked_checkbox.GetValue()

    def SetLocked(self, value):
        self.locked_checkbox.SetValue(value)

    def GetEndsToday(self):
        return self.ends_today_checkbox.GetValue()

    def SetEndsToday(self, value):
        self.ends_today_checkbox.SetValue(value)

    def GetName(self):
        return self.name.GetValue().strip()

    def SetName(self, value):
        self.name.SetValue(value)

    def GetCategory(self):
        return self.category_choice.GetSelectedCategory()

    def SetCategory(self, value):
        self.category_choice.Populate(select=value)

    def GetContainer(self):
        selection = self.containers_choice.GetSelection()
        if selection != -1:
            container = self.containers_choice.GetClientData(selection)
        else:
            container = None
        return container

    def SetContainer(self, value):
        self._fill_containers_listbox(value)

    def GetEventData(self):
        event_data = {}
        for data_id, editor in self._get_event_data():
            data = editor.get_data()
            if data is not None:
                event_data[data_id] = editor.get_data()
        return event_data

    def SetEventData(self, event_data):
        for data_id, editor in self._get_event_data():
            if data_id in event_data:
                data = event_data[data_id]
                if data is not None:
                    editor.set_data(data)

    def ClearEventData(self):
        for _, editor in self._get_event_data():
            editor.clear_data()

    def IsAddMoreChecked(self):
        return self.add_more_checkbox.GetValue()

    def SetShowAddMoreCheckbox(self, value):
        self.add_more_checkbox.Show(value)
        self.add_more_checkbox.SetValue(False)
        self.SetSizerAndFit(self.GetSizer())

    def SetFocusOnFirstControl(self):
        _set_focus_and_select(self.start_time)

    def DisplayInvalidStart(self, message):
        self._display_invalid_input(message, self.start_time)

    def DisplayInvalidEnd(self, message):
        self._display_invalid_input(message, self.end_time)

    def _display_invalid_input(self, message, control):
        self.DisplayErrorMessage(message)
        _set_focus_and_select(control)

    def _fill_containers_listbox(self, select_container):
        # We can not do error handling here since this method is also called
        # from the constructor (and then error handling is done by the code
        # calling the constructor).
        self.containers_choice.Clear()
        self.containers_choice.Append("", None)  # The None-container
        selection_set = False
        current_item_index = 1
        if select_container is not None and select_container not in self.timeline.get_containers():
            self.containers_choice.Append(select_container.text, select_container)
            self.containers_choice.SetSelection(current_item_index)
            current_item_index += 1
            selection_set = True
        for container in self.timeline.get_containers():
            self.containers_choice.Append(container.text, container)
            if not selection_set:
                if container == select_container:
                    self.containers_choice.SetSelection(current_item_index)
                    selection_set = True
            current_item_index += 1
        self.last_real_container_index = current_item_index - 1
        self.add_container_item_index = self.last_real_container_index + 2
        self.edit_container_item_index = self.last_real_container_index + 3
        self.containers_choice.Append("", None)
        self.containers_choice.Append(_("Add new"), None)
        if not selection_set:
            self.containers_choice.SetSelection(0)
        self.current_container_selection = self.containers_choice.GetSelection()
        self._enable_disable_checkboxes()

    def _enable_disable_checkboxes(self):
        self._enable_disable_ends_today()
        self._enable_disable_locked()

    def _enable_disable_ends_today(self):
        enable = (self._container_not_selected() and
                  not self.locked_checkbox.GetValue() and
                  self.controller.start_is_in_history())
        self.ends_today_checkbox.Enable(enable)

    def _enable_disable_locked(self):
        enable = self._container_not_selected()
        self.locked_checkbox.Enable(enable)

    def _container_not_selected(self):
        index = self.containers_choice.GetSelection()
        return (index == 0)

    def _get_event_data(self):
        return [
            ("description", self.description),
            ("alert", self.alert),
            ("icon", self.icon),
            ("hyperlink", self.hyperlink),
            ("progress", self.progress),
        ]

    def _lst_containers_on_choice(self, e):
        new_selection_index = e.GetSelection()
        if new_selection_index > self.last_real_container_index:
            self.containers_choice.SetSelection(self.current_container_selection)
            if new_selection_index == self.add_container_item_index:
                self._add_container()
        else:
            self.current_container_selection = new_selection_index
        self._enable_disable_checkboxes()

    def _add_container(self):
        def create_container_editor():
            return EditContainerDialog(self, _("Add Container"), self.timeline, None)
        def handle_success(dialog):
            if dialog.GetReturnCode() == wx.ID_OK:
                try:
                    self._fill_containers_listbox(dialog.GetEditedContainer())
                except TimelineIOError, e:
                    gui_utils.handle_db_error_in_dialog(self, e)
        gui_utils.show_modal(create_container_editor,
                             gui_utils.create_dialog_db_error_handler(self),
                             handle_success)
