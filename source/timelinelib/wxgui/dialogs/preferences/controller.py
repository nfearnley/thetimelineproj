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


import os

import wx

from timelinelib.wxgui.components.font import deserialize_font
from timelinelib.wxgui.framework import Controller
from timelinelib.config.paths import EVENT_ICONS_DIR


class PreferencesDialogController(Controller):

    def on_init(self, config, experimental_features):
        self.config = config
        self.experimental_features = experimental_features
        self.weeks_map = ((0, "monday"), (1, "sunday"))
        self._set_initial_values()

    def on_close(self):
        self.config.minor_strip_divider_line_colour = str(self.view.GetMinorStripColor())
        self.config.major_strip_divider_line_colour = str(self.view.GetMajorStripColor())
        self.config.now_line_colour = str(self.view.GetNowLineColor())

    def on_open_recent_change(self, event):
        self.config.set_open_recent_at_startup(event.IsChecked())

    def on_inertial_scrolling_changed(self, event):
        self.config.set_use_inertial_scrolling(event.IsChecked())

    def on_never_period_point_changed(self, event):
        self.config.set_never_show_period_events_as_point_events(event.IsChecked())

    def on_center_text_changed(self, event):
        self.config.set_center_event_texts(event.IsChecked())

    def on_week_start_changed(self, event):
        self.config.set_week_start(self._index_week(event.GetSelection()))

    def on_uncheck_time_for_new_events(self, event):
        self.config.uncheck_time_for_new_events = event.IsChecked()

    def on_tab_order_click(self, event):
        self.view.ShowSelectTabOrderDialog(self.config)

    def on_major_strip_click(self, event):
        font = deserialize_font(self.config.major_strip_font)
        if self.view.ShowEditFontDialog(font):
            self.config.major_strip_font = font.serialize()

    def on_minor_strip_click(self, event):
        font = deserialize_font(self.config.minor_strip_font)
        if self.view.ShowEditFontDialog(font):
            self.config.minor_strip_font = font.serialize()

    def on_legend_click(self, event):
        font = deserialize_font(self.config.legend_font)
        if self.view.ShowEditFontDialog(font):
            self.config.legend_font = font.serialize()

    def on_experimental_changed(self, event):
        self.experimental_features.set_active_state_on_feature_by_name(
            event.GetEventObject().GetLabel(), event.IsChecked())
        self.config.experimental_features = str(self.experimental_features)

    def on_fuzzy_icon_changed(self, event):
        self.config.set_fuzzy_icon(event.GetString())
        self.view.DisplayIcons()

    def on_locked_icon_changed(self, event):
        self.config.set_locked_icon(event.GetString())
        self.view.DisplayIcons()

    def on_hyperlink_icon_changed(self, event):
        self.config.set_hyperlink_icon(event.GetString())
        self.view.DisplayIcons()

    def _set_initial_values(self):
        self.view.SetOpenRecentCheckboxValue(self.config.get_open_recent_at_startup())
        self.view.SetInertialScrollingCheckboxValue(self.config.get_use_inertial_scrolling())
        self.view.SetNeverPeriodPointCheckboxValue(self.config.get_never_show_period_events_as_point_events())
        self.view.SetCenterTextCheckboxValue(self.config.get_center_event_texts())
        self.view.SetWeekStartSelection(self._week_index(self.config.get_week_start()))
        self.view.AddExperimentalFeatures(self.experimental_features.get_all_features())
        self.view.SetUncheckTimeForNewEventsCheckboxValue(self.config.uncheck_time_for_new_events)
        self.view.SetMinorStripColor(wx.Colour(*self.config.minor_strip_divider_line_colour))
        self.view.SetMajorStripColor(wx.Colour(*self.config.major_strip_divider_line_colour))
        self.view.SetNowLineColor(wx.Colour(*self.config.now_line_colour))
        choices = [f for f in os.listdir(EVENT_ICONS_DIR) if f.endswith(".png")]
        self.view.SetIconsChoices(choices)
        self.view.SetFuzzyIcon(self.config.get_fuzzy_icon())
        self.view.SetLockedIcon(self.config.get_locked_icon())
        self.view.SetHyperlinkIcon(self.config.get_hyperlink_icon())
        self.view.DisplayIcons()

    def _week_index(self, week):
        for (i, w) in self.weeks_map:
            if w == week:
                return i
        raise ValueError("Unknown week '%s'." % week)

    def _index_week(self, index):
        for (i, w) in self.weeks_map:
            if i == index:
                return w
        raise ValueError("Unknown week index '%s'." % index)
