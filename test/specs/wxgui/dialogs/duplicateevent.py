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

from timelinelib.calendar.gregorian import GregorianUtils
from timelinelib.data.db import MemoryDB
from timelinelib.data import Event
from timelinelib.data import TimePeriod
from timelinelib.db.exceptions import TimelineIOError
from timelinelib.time.gregoriantime import GregorianTimeType
from timelinelib.wxgui.dialogs.duplicateevent.controller import BACKWARD
from timelinelib.wxgui.dialogs.duplicateevent.controller import BOTH
from timelinelib.wxgui.dialogs.duplicateevent.controller import DuplicateEventDialogController
from timelinelib.wxgui.dialogs.duplicateevent.controller import FORWARD
from timelinelib.wxgui.dialogs.duplicateevent.view import DuplicateEventDialog
from timelinetest import UnitTestCase
from timelinetest.utils import create_dialog
from timelinetest.utils import select_language


#select_language("sv")


class describe_DuplicateEventDialog(UnitTestCase):

    #
    # Construction
    #
    def test_it_can_be_created(self):
        with create_dialog(DuplicateEventDialog, None, MemoryDB(), None) as dialog:
            if self.HALT_GUI:
                dialog.ShowModal()

    def test_number_of_duplicates_should_be_1(self):
        self.view.SetCount.assert_called_with(1)

    def test_first_period_should_be_selected(self):
        self.view.SelectMovePeriodFnAtIndex.assert_called_with(0)

    def test_frequency_should_be_one(self):
        self.view.SetFrequency.assert_called_with(1)

    def test_direction_should_be_forward(self):
        self.view.SetDirection.assert_called_with(FORWARD)

    #
    # when_duplicating_event_with_default_settings
    #
    def test_one_new_event_is_saved(self):
        self._duplicate_with(count=1, freq=1, direction=FORWARD)
        self.assertEqual(1, self.db.save_events.call_count)

    def test_the_new_event_gets_period_from_move_period_fn(self):
        self._duplicate_with(count=1, freq=1, direction=FORWARD)
        new_events = self.db.save_events.call_args[0][0]
        new_period = new_events[0].get_time_period()
        expected_period = TimePeriod(
            GregorianTimeType(),
            GregorianUtils.from_date(2010, 8, 1).to_time(),
            GregorianUtils.from_date(2010, 8, 1).to_time())
        self.assertEqual(expected_period, new_period)

    def test_the_new_event_should_not_be_the_same_as_the_existing(self):
        self._duplicate_with(count=1, freq=1, direction=FORWARD)
        new_events = self.db.save_events.call_args[0][0]
        self.assertNotEquals(self.event, new_events[0])

    def test_the_dialog_should_close(self):
        self._duplicate_with(count=1, freq=1, direction=FORWARD)
        self.assertTrue(self.view.Close.assert_called)

    #
    # when_saving_duplicated_event_fails
    #
    def test_the_failure_is_handled(self):
        self.db.save_events.side_effect = TimelineIOError
        self._duplicate_with(count=1, freq=1, direction=FORWARD)
        self.assertTrue(self.view.HandleDbError.called)

    def test_the_dialog_is_not_closed(self):
        self.db.save_events.side_effect = TimelineIOError
        self._duplicate_with(count=1, freq=1, direction=FORWARD)
        self.assertFalse(self.view.Close.called)

    #
    # when_event_can_not_be_duplicated
    #
    def test_None_period_failure_is_handled(self):
        self.move_period_fn.return_value = None
        self._duplicate_with(count=1, freq=1, direction=FORWARD)
        self.view.HandleDateErrors.assert_called_with(1)

    def test_the_dialog_is_closed(self):
        self.move_period_fn.return_value = None
        self._duplicate_with(count=1, freq=1, direction=FORWARD)
        self.assertTrue(self.view.Close.called)

    #
    # a_diloag_with_different_settings
    #
    def _assert_move_period_called_with(self, num_list):
        self.assertEqual(
            [((self.event.get_time_period(), num), {}) for num in num_list],
            self.move_period_fn.call_args_list)

    def test_count_1_freq_1_direction_forward(self):
        self._duplicate_with(count=1, freq=1, direction=FORWARD)
        self._assert_move_period_called_with([1])

    def test_count_1_freq_1_direction_backward(self):
        self._duplicate_with(count=1, freq=1, direction=BACKWARD)
        self._assert_move_period_called_with([-1])

    def test_count_1_freq_1_direction_both(self):
        self._duplicate_with(count=1, freq=1, direction=BOTH)
        self._assert_move_period_called_with([-1, 1])
 
    def test_count_2_freq_1_direction_forward(self):
        self._duplicate_with(count=2, freq=1, direction=FORWARD)
        self._assert_move_period_called_with([1, 2])

    def test_count_2_freq_1_direction_backward(self):
        self._duplicate_with(count=2, freq=1, direction=BACKWARD)
        self._assert_move_period_called_with([-2, -1])

    def test_count_2_freq_1_direction_both(self):
        self._duplicate_with(count=2, freq=1, direction=BOTH)
        self._assert_move_period_called_with([-2, -1, 1, 2])

    def test_count_1_freq_2_direction_forward(self):
        self._duplicate_with(count=1, freq=2, direction=FORWARD)
        self._assert_move_period_called_with([2])

    def test_count_1_freq_2_direction_backward(self):
        self._duplicate_with(count=1, freq=2, direction=BACKWARD)
        self._assert_move_period_called_with([-2])

    def test_count_1_freq_2_direction_both(self):
        self._duplicate_with(count=1, freq=2, direction=BOTH)
        self._assert_move_period_called_with([-2, 2])

    #
    # Setup
    #
    def setUp(self):
        self.db = Mock(MemoryDB)
        self.db.get_time_type.return_value = GregorianTimeType()
        self.view = Mock(DuplicateEventDialog)
        self.view.GetMovePeriodFn.return_value = self._create_move_period_fn_mock()
        self.event = Event(
            self.db.get_time_type(),
            GregorianUtils.from_date(2010, 1, 1).to_time(),
            GregorianUtils.from_date(2010, 1, 1).to_time(),
            "foo",
            category=None)
        self.controller = DuplicateEventDialogController(self.view)
        self.controller.on_init(self.db, self.event)

    def _create_move_period_fn_mock(self):
        self.move_period_fn = Mock()
        self.move_period_fn.return_value = TimePeriod(
            GregorianTimeType(),
            GregorianUtils.from_date(2010, 8, 1).to_time(),
            GregorianUtils.from_date(2010, 8, 1).to_time())
        return self.move_period_fn

    def _duplicate_with(self, count, freq, direction):
        self.view.GetCount.return_value = count
        self.view.GetFrequency.return_value = freq
        self.view.GetDirection.return_value = direction
        self.controller.create_duplicates_and_save()