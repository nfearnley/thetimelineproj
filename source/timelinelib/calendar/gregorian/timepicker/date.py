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

from timelinelib.calendar.gregorian.gregorian import GregorianUtils
from timelinelib.calendar.gregorian.timepicker.datecontroller import GregorianDatePickerController
from timelinelib.calendar.gregorian.timetype import GregorianTimeType
from timelinelib.canvas.data.internaltime import delta_from_days


class GregorianDatePicker(wx.Panel):

    def __init__(self, parent, date_formatter, name=None):
        wx.Panel.__init__(self, parent)
        self.controller = GregorianDatePickerController(self)
        self._create_gui()
        self.controller.on_init(
            date_formatter,
            DateModifier()
        )

    def _create_gui(self):
        self._create_date_text()
        self._create_bc_button()
        self._layout()

    def _create_date_text(self):
        self.date_text = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
        self.date_text.Bind(wx.EVT_CHAR, self.controller.on_char)
        self.date_text.Bind(wx.EVT_TEXT, self.controller.on_text)

    def _create_bc_button(self):
        label = _("BC")
        self.bc_button = wx.ToggleButton(self, label=label)
        (label_width, label_height) = self.bc_button.GetTextExtent(label)
        self.bc_button.SetMinSize((label_width + 20, -1))

    def _layout(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.date_text, flag=wx.EXPAND, proportion=1)
        sizer.Add(self.bc_button, flag=wx.EXPAND)
        self.SetSizer(sizer)

    def GetGregorianDate(self):
        return self.controller.get_gregorian_date()

    def SetGregorianDate(self, date):
        self.controller.set_gregorian_date(date)

    def GetText(self):
        return self.date_text.GetValue()

    def SetText(self, text):
        x = self.date_text.GetInsertionPoint()
        self.date_text.SetValue(text)
        self.date_text.SetInsertionPoint(x)

    def SetSelection(self, pos_lenght_tuple):
        (pos, lenght) = pos_lenght_tuple
        self.date_text.SetSelection(pos, pos+lenght)

    def GetCursorPosition(self):
        return self.date_text.GetInsertionPoint()

    def GetIsBc(self):
        return self.bc_button.GetValue()

    def SetIsBc(self, is_bc):
        self.bc_button.SetValue(is_bc)

    def SetBackgroundColour(self, colour):
        self.date_text.SetBackgroundColour(colour)
        self.date_text.Refresh()


class DateModifier(object):

    def increment_year(self, date):
        max_year = GregorianUtils.from_time(GregorianTimeType().get_max_time()).year
        year, month, day = date
        if year < max_year - 1:
            return self._set_valid_day(year + 1, month, day)
        return date

    def increment_month(self, date):
        max_year = GregorianUtils.from_time(GregorianTimeType().get_max_time()).year
        year, month, day = date
        if month < 12:
            return self._set_valid_day(year, month + 1, day)
        elif year < max_year - 1:
            return self._set_valid_day(year + 1, 1, day)
        return date

    def increment_day(self, date):
        year, month, day = date
        time = GregorianUtils.from_date(year, month, day).to_time()
        if time <  GregorianTimeType().get_max_time() - delta_from_days(1):
            return GregorianUtils.from_time(time + delta_from_days(1)).to_date_tuple()
        return date

    def decrement_year(self, date):
        year, month, day = date
        if year > GregorianUtils.from_time(GregorianTimeType().get_min_time()).year:
            return self._set_valid_day(year - 1, month, day)
        return date

    def decrement_month(self, date):
        year, month, day = date
        if month > 1:
            return self._set_valid_day(year, month - 1, day)
        elif year > GregorianUtils.from_time(GregorianTimeType().get_min_time()).year:
            return self._set_valid_day(year - 1, 12, day)
        return date

    def decrement_day(self, date):
        year, month, day = date
        if day > 1:
            return self._set_valid_day(year, month, day - 1)
        elif month > 1:
            return self._set_valid_day(year, month - 1, 31)
        elif year > GregorianUtils.from_time(GregorianTimeType().get_min_time()).year:
            return self._set_valid_day(year - 1, 12, 31)
        return date

    def _set_valid_day(self, new_year, new_month, new_day):
        done = False
        while not done:
            try:
                date = GregorianUtils.from_date(new_year, new_month, new_day)
                done = True
            except Exception:
                new_day -= 1
        return date.to_date_tuple()