# Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018  Rickard Lindberg, Roger Lindberg
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


from mock import Mock

from timelinelib.calendar.pharaonic.pharaonic import PharaonicDateTime
from timelinelib.calendar.pharaonic.timepicker.date import PharaonicDatePicker
from timelinelib.calendar.pharaonic.timepicker.datetime import CalendarPopup
from timelinelib.calendar.pharaonic.timepicker.datetime import CalendarPopupController
from timelinelib.calendar.pharaonic.timepicker.datetime import PharaonicDateTimePicker
from timelinelib.calendar.pharaonic.timepicker.datetime import PharaonicDateTimePickerController
from timelinelib.calendar.pharaonic.timepicker.datetime import PharaonicTimePicker
from timelinelib.test.cases.unit import UnitTestCase


class APharaonicDateTimePicker(UnitTestCase):

    def setUp(self):
        self.view = Mock(PharaonicDateTimePicker)
        self.date_picker = Mock(PharaonicDatePicker)
        self.time_picker = Mock(PharaonicTimePicker)
        self.now_fn = Mock()
        self.controller = PharaonicDateTimePickerController(
            self.view, self.date_picker, self.time_picker, self.now_fn, None)

    def testDateControlIsAssignedDatePartFromSetValue(self):
        self.controller.set_value(PharaonicDateTime(2010, 11, 20, 15, 33, 0).to_time())
        self.date_picker.SetPharaonicDate.assert_called_with((2010, 11, 20))

    # TODO: Is this really PharaonicDateTimePicker's responsibility?
    def testDateControlIsAssignedCurrentDateIfSetWithValueNone(self):
        self.now_fn.return_value = PharaonicDateTime(2010, 8, 30, 0, 0, 0).to_time()
        self.controller.set_value(None)
        self.date_picker.SetPharaonicDate.assert_called_with((2010, 8, 30))

    def testTimeControlIsAssignedTimePartFromSetValue(self):
        self.controller.set_value(PharaonicDateTime(2010, 11, 20, 15, 33, 0).to_time())
        self.time_picker.SetPharaonicTime.assert_called_with((15, 33, 0))

    # TODO: Is this really PharaonicDateTimePicker's responsibility?
    def testTimeControlIsAssignedCurrentTimeIfSetWithValueNone(self):
        self.now_fn.return_value = PharaonicDateTime(2010, 8, 30, 12, 15, 0).to_time()
        self.controller.set_value(None)
        self.time_picker.SetPharaonicTime.assert_called_with((12, 15, 0))

    def testGetValueWhenTimeIsShownShouldReturnDateWithTime(self):
        self.time_picker.IsShown.return_value = True
        self.time_picker.GetPharaonicTime.return_value = (14, 30, 0)
        self.date_picker.GetPharaonicDate.return_value = (2010, 8, 30)
        self.assertEqual(PharaonicDateTime(2010, 8, 30, 14, 30, 0).to_time(), self.controller.get_value())

    def testGetValueWhenTimeIsHiddenShouldReturnDateWithoutTime(self):
        self.time_picker.IsShown.return_value = False
        self.time_picker.GetPharaonicTime.return_value = (14, 30, 0)
        self.date_picker.GetPharaonicDate.return_value = (2010, 8, 30)
        self.assertEqual(PharaonicDateTime(2010, 8, 30, 0, 0, 0).to_time(), self.controller.get_value())

    def testControllerCanConverDateTupleToWxDate(self):
        wx_date = self.controller.date_tuple_to_wx_date((2010, 8, 30))
        self.assertEqual((2010, 8, 30), (wx_date.Year, wx_date.Month + 1, wx_date.Day))

    def testControllerCanConverWxdateToDateTuple(self):
        wx_date = self.controller.date_tuple_to_wx_date((2010, 8, 30))
        year, month, day = self.controller.wx_date_to_date_tuple(wx_date)
        self.assertEqual((2010, 8, 30), (year, month, day))


class ACalendarPopup(UnitTestCase):

    def setUp(self):
        self.calendar_popup = Mock(CalendarPopup)
        self.controller = CalendarPopupController(self.calendar_popup)

    def testStaysOpenOnMonthChange(self):
        self._simulateMonthChange()
        self.assertTrue(self.calendar_popup.Popup.called)

    def testStaysOpenOnDayChange(self):
        self._simulateDateChange()
        self.assertTrue(self.calendar_popup.Popup.called)

    def testPopupCallAllowedJustOnce(self):
        self._simulateMonthChange()
        self.assertTrue(self.calendar_popup.Popup.called)
        self.calendar_popup.reset_mock()
        self._simulateMonthChange()
        self.assertFalse(self.calendar_popup.Popup.called)

    def _simulateMonthChange(self):
        self.controller.on_month()
        self.controller.on_dismiss()

    def _simulateDateChange(self):
        self.controller.on_day()
        self.controller.on_dismiss()
