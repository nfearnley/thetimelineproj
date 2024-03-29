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
import humblewx

from timelinelib.calendar.pharaonic.dateformatter import PharaonicDateFormatter
from timelinelib.calendar.pharaonic.timepicker.period import PharaonicPeriodPicker
from timelinelib.calendar.pharaonic.timepicker.period import PharaonicPeriodPickerController
from timelinelib.calendar.pharaonic.timetype import PharaonicTimeType
from timelinelib.config.dotfile import Config
from timelinelib.test.cases.unit import UnitTestCase
from timelinelib.test.pharaonic_utils import pharaonic_period
from timelinelib.test.pharaonic_utils import human_time_to_pharaonic
from timelinelib.wxgui.framework import Dialog


class TestPharaonicPeriodPicker(UnitTestCase):

    def test_show_manual_test_dialog(self):
        self.show_dialog(PharaonicPeriodPickerTestDialog)

    def test_get_value(self):
        view = Mock(PharaonicPeriodPicker)
        view.GetStartValue.return_value = human_time_to_pharaonic("1 I Akhet 2016")
        view.GetEndValue.return_value = human_time_to_pharaonic("2 I Akhet 2016")
        controller = PharaonicPeriodPickerController(view)
        self.assertEqual(
            controller.get_value(),
            pharaonic_period("1 I Akhet 2016", "2 I Akhet 2016")
        )


class PharaonicPeriodPickerTestDialog(Dialog):

    """
    <BoxSizerVertical>
        <FlexGridSizer columns="1" border="ALL">
            <Button label="before" />
            <PeriodPicker
                time_type="$(time_type)"
                name="period_picker"
                config="$(config)"
            />
            <Button label="after" />
        </FlexGridSizer>
    </BoxSizerVertical>
    """

    def __init__(self):
        Dialog.__init__(self, humblewx.Controller, None, {
            "time_type": PharaonicTimeType(),
            "config": self._create_mock_config(),
        })
        self.period_picker.SetValue(
            pharaonic_period("1 I Akhet 2016", "4 I Akhet 2016")
        )

    def _create_mock_config(self):
        config = Mock(Config)
        config.get_date_formatter.return_value = PharaonicDateFormatter()
        return config
