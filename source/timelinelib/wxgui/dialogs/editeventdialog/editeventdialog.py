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


from timelinelib.wxgui.dialogs.editeventdialog.editeventdialogcontroller import EditEventDialogController
from timelinelib.wxgui.framework import Dialog

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
                    <CheckBox label="$(period_checkbox_text)" />
                    <CheckBox label="$(show_time_checkbox_text)" />
                    <CheckBox label="$(fuzzy_checkbox_text)" />
                    <CheckBox label="$(locked_checkbox_text)" />
                    <CheckBox label="$(ends_today_checkbox_text)" />
                </FlexGridSizer>
                <StaticText align="ALIGN_CENTER_VERTICAL" label="$(text_label)" />
                <TextCtrl />
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
                    align="ALIGN_LEFT"
                />
            </FlexGridSizer>
            <Notebook name="notebook" style="BK_DEFAULT" border="LEFT|RIGHT|BOTTOM" proportion="1">
                <DescriptionEditor notebookLabel="$(page_description)" editor="$(self)" proportion="1" />
                <IconEditor notebookLabel="$(page_icon)" editor="$(self)" proportion="1" />
                <AlertEditor notebookLabel="$(page_alert)" editor="$(self)" proportion="1" />
                <HyperlinkEditor notebookLabel="$(page_hyperlink)" editor="$(self)" proportion="1" />
                <ProgressEditor notebookLabel="$(page_progress)" editor="$(self)" proportion="1" />
            </Notebook>
        </StaticBoxSizerVertical>
        <CheckBox label="$(add_more_label)" border="LEFT|RIGHT" />
        <DialogButtonsOkCancelSizer border="ALL" />
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
        self.controller.on_init()
        self.category_choice.Populate()
        self.SetMinSize((800, -1))
        self.Fit()
        self.SetMinSize(self.GetSize())
