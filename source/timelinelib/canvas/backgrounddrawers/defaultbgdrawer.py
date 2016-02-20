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


import wx


class DefaultBackgroundDrawer(object):

    def draw(self, drawer, dc, scene, timeline, weekend_colour):
        self.drawer = drawer
        self._erase_background(dc)
        self._draw_eras(dc, scene, timeline)
        self._draw_weekend_days(dc, drawer, scene, weekend_colour)

    def _erase_background(self, dc):
        w, h = dc.GetSizeTuple()
        self._set_color(dc, wx.WHITE)
        dc.DrawRectangle(0, 0, w, h)

    def _draw_weekend_days(self, dc, drawer, scene, weekend_colour):
        def draw_day_backgrounds(h):
            for strip_period in scene.minor_strip_data:
                if strip_period.start_time.is_weekend_day():
                    self._draw_weekend_rect(strip_period, h, weekend_colour)

        _, h = dc.GetSizeTuple()
        if drawer.time_type.is_date_time_type():
            if scene.minor_strip_is_day():
                draw_day_backgrounds(h)

    def _draw_eras(self, dc, scene, timeline):
        _, h = dc.GetSizeTuple()
        for era in timeline.get_all_periods():
            if self.drawer.period_is_visible(era.get_time_period()):
                self._draw_era(era, h)

    def _draw_era(self, era, h):
        self._draw_era_rect(era, h)
        self._draw_era_name_in_center_of_visible_era(era, h)

    def _draw_era_rect(self, era, h):
        self._draw_timeperiod_rect(era.get_time_period(), h, era.get_color(), 0)

    def _draw_weekend_rect(self, timeperiod, h, weekend_colour):
        OFFSET = 15
        self._draw_timeperiod_rect(timeperiod, h, weekend_colour, OFFSET)

    def _draw_timeperiod_rect(self, timeperiod, h, colour, Offset):
        x, width = self._get_timeperiod_measures(timeperiod)
        self._draw_backgound_rect(x, h, width, colour, Offset)

    def _draw_backgound_rect(self, x, h, width, colour, Offset):
        self._set_color(self.drawer.dc, colour)
        self.drawer.dc.DrawRectangle(x, Offset, width, h - 2 * Offset)

    def _draw_era_name_in_center_of_visible_era(self, era, h):
        x, width = self._get_timeperiod_measures(era.get_time_period())
        wt, ht = self.drawer.dc.GetTextExtent(era.get_name())
        self.drawer.dc.DrawText(era.get_name(), x + width / 2 - wt / 2, h - ht)

    def _get_timeperiod_measures(self, time_period):
        x1, x2 = self.drawer.get_period_xpos(time_period)
        return x1, x2 - x1

    def _set_color(self, dc, color):
        dc.SetPen(wx.Pen(color))
        dc.SetBrush(wx.Brush(color))
