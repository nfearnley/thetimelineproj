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


from mock import Mock

from timelinelib.calendar.gregorian.datetimepicker import CalendarPopup
from timelinelib.calendar.gregorian.datetimepicker import CalendarPopupController
from timelinelib.calendar.gregorian.datetimepicker import GregorianDateTimePickerController
from timelinelib.calendar.gregorian.datetimepicker import GregorianTimePicker
from timelinelib.calendar.gregorian.gregorian import Gregorian, GregorianUtils
from timelinelib.calendar.gregorian.timetype import GregorianTimeType
from timelinelib.test.cases.unit import UnitTestCase
from timelinelib.time.timeline import delta_from_days
from timelinelib.wxgui.components.gregoriandatepicker import GregorianDatePicker


class AGregorianDateTimePicker(UnitTestCase):

    def setUp(self):
        self.date_picker = Mock(GregorianDatePicker)
        self.time_picker = Mock(GregorianTimePicker)
        self.now_fn = Mock()
        self.controller = GregorianDateTimePickerController(
            self.date_picker, self.time_picker, self.now_fn, None)

    def testDateControlIsAssignedDatePartFromSetValue(self):
        self.controller.set_value(Gregorian(2010, 11, 20, 15, 33, 0).to_time())
        self.date_picker.SetGregorianDate.assert_called_with((2010, 11, 20))

    # TODO: Is this really GregorianDateTimePicker's responsibility?
    def testDateControlIsAssignedCurrentDateIfSetWithValueNone(self):
        self.now_fn.return_value = Gregorian(2010, 8, 31, 0, 0, 0).to_time()
        self.controller.set_value(None)
        self.date_picker.SetGregorianDate.assert_called_with((2010, 8, 31))

    def testTimeControlIsAssignedTimePartFromSetValue(self):
        self.controller.set_value(Gregorian(2010, 11, 20, 15, 33, 0).to_time())
        self.time_picker.SetGregorianTime.assert_called_with((15, 33, 0))

    # TODO: Is this really GregorianDateTimePicker's responsibility?
    def testTimeControlIsAssignedCurrentTimeIfSetWithValueNone(self):
        self.now_fn.return_value = Gregorian(2010, 8, 31, 12, 15, 0).to_time()
        self.controller.set_value(None)
        self.time_picker.SetGregorianTime.assert_called_with((12, 15, 0))

    def testGetValueWhenTimeIsShownShouldReturnDateWithTime(self):
        self.time_picker.IsShown.return_value = True
        self.time_picker.GetGregorianTime.return_value = (14, 30, 0)
        self.date_picker.GetGregorianDate.return_value = (2010, 8, 31)
        self.assertEqual(Gregorian(2010, 8, 31, 14, 30, 0).to_time(), self.controller.get_value())

    def testGetValueWhenTimeIsHiddenShouldReturnDateWithoutTime(self):
        self.time_picker.IsShown.return_value = False
        self.time_picker.GetGregorianTime.return_value = (14, 30, 0)
        self.date_picker.GetGregorianDate.return_value = (2010, 8, 31)
        self.assertEqual(Gregorian(2010, 8, 31, 0, 0, 0).to_time(), self.controller.get_value())

    def testControllerCanConverDateTupleToWxDate(self):
        wx_date = self.controller.date_tuple_to_wx_date((2010, 8, 31))
        self.assertEqual((2010, 8, 31), (wx_date.Year, wx_date.Month + 1, wx_date.Day))

    def testControllerCanConverWxdateToDateTuple(self):
        wx_date = self.controller.date_tuple_to_wx_date((2010, 8, 31))
        year, month, day = self.controller.wx_date_to_date_tuple(wx_date)
        self.assertEqual((2010, 8, 31), (year, month, day))


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


def get_min_time_string():
    year, month, day = GregorianUtils.from_time(GregorianTimeType().get_min_time()[0]).to_date_tuple()
    return "%d-%02d-%02d" % (year, month, day)


def get_max_time_string():
    # max_time is not a valid date so we must decrease with one day
    year, month, day = GregorianUtils.from_time(GregorianTimeType().get_max_time()[0] - delta_from_days(1)).to_date_tuple()
    return "%d-%02d-%02d" % (year, month, day)
