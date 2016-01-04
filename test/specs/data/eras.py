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


from timelinelib.data.eras import InvalidOperationError
from timelinelib.data import Eras
from timelinelib.test.cases.unit import UnitTestCase
from timelinelib.test.utils import a_gregorian_era
from timelinelib.test.utils import a_gregorian_era_with
from timelinelib.test.utils import a_numeric_era_with
from timelinelib.test.utils import gregorian_period
from timelinelib.test.utils import numeric_period


class ErasTestCase(UnitTestCase):

    def test_default_has_an_empty_list(self):
        self.assertEqual([], self.eras.get_all())

    def setUp(self):
        self.color1 = (128, 255, 255)
        self.color2 = (255, 0, 255)
        self.color3 = (255, 128, 255)
        self.eras = Eras()


class describe_cloning(ErasTestCase):

    def test_eras_are_cloned(self):
        self.eras.save_era(a_gregorian_era())
        self.eras.save_era(a_gregorian_era())
        clone = self.eras.clone()
        self.assertListIsCloneOf(clone.get_all(), self.eras.get_all())


class describe_saving_eras(ErasTestCase):

    def test_can_save(self):
        era = a_gregorian_era()
        self.eras.save_era(era)
        self.assertEqual(self.eras.get_all(), [era])

    def test_can_update(self):
        era = a_gregorian_era()
        self.eras.save_era(era)
        era.set_name("I'm the first era")
        self.eras.save_era(era)
        self.assertEqual(self.eras.get_all(), [era])

    def test_fails_if_existing_era_does_not_seem_to_be_found(self):
        era = a_gregorian_era()
        era.set_id(15)
        self.assertRaises(InvalidOperationError, self.eras.save_era, era)


class describe_overlapping_eras(ErasTestCase):
    """
    All Eras are sorted by start_time. That is...
       Era(n).start_time <= Era(n+1).start_time.
    Two adjacent Eras are overlapping if..
        Era(n+1).start_time < Era(n).end_time
    There are 6 different overlapping situations to handle:
        1.  o---(e1)---o
                o---(e2)---o

        2.  o---(e1)---o
            o---(e2)-------o

        Total ecplise....

        3.  o---(e1)-------o
            o---(e2)----o

        4.  o---(e1)----o
            o---(e2)----o

        5.  o------(e1)----o
               o---(e2)----o

        6.  o------(e1)----o
               o---(e2)---o
    """
    def test_eras_are_returned_sorted_when_list_is_unsorted(self):
        self.given_two_overlapping_eras_type_1()
        self.assertEqual(self.era1, self.eras.get_all()[0])

    def test_eras_can_detect_overlapping_type1(self):
        self.given_two_overlapping_eras_type_1()
        eras = self.eras.get_all()
        self.assertEqual(1, eras[0].overlapping(eras[1]))

    def test_eras_can_detect_overlapping_type2(self):
        self.given_two_overlapping_eras_type_2()
        eras = self.eras.get_all()
        self.assertEquals(eras[0], self.era1)
        self.assertEqual(2, eras[0].overlapping(eras[1]))

    def test_eras_can_detect_overlapping_type3(self):
        self.given_two_overlapping_eras_type_3()
        eras = self.eras.get_all()
        self.assertEquals(eras[0], self.era1)
        self.assertEqual(3, eras[0].overlapping(eras[1]))

    def test_eras_can_detect_overlapping_type4(self):
        self.given_two_overlapping_eras_type_4()
        eras = self.eras.get_all()
        self.assertEquals(eras[0], self.era1)
        self.assertEqual(4, eras[0].overlapping(eras[1]))

    def test_eras_can_detect_overlapping_type5(self):
        self.given_two_overlapping_eras_type_5()
        eras = self.eras.get_all()
        self.assertEquals(eras[0], self.era1)
        self.assertEqual(5, eras[0].overlapping(eras[1]))

    def test_eras_can_detect_overlapping_type6(self):
        self.given_two_overlapping_eras_type_6()
        eras = self.eras.get_all()
        self.assertEquals(eras[0], self.era1)
        self.assertEqual(6, eras[0].overlapping(eras[1]))

    def test_eras_can_return_a_list_with_added_overlapping_type1_eras(self):
        self.given_two_overlapping_eras_type_1()
        periods = self.eras.get_all_periods()
        self.assertEqual(3, len(periods))
        self.assertEqual([periods[0].get_time_period().start_time,
                          periods[1].get_time_period().start_time,
                          periods[2].get_time_period().start_time], [e.get_time_period().start_time for e in periods])
        self.assertEqual([self.color1,
                          self.mix_colors(self.color1, self.color2),
                          self.color2], [e.color for e in periods])

    def test_eras_can_return_a_list_with_added_overlapping_type2_eras(self):
        self.given_two_overlapping_eras_type_2()
        periods = self.eras.get_all_periods()
        self.assertEqual(2, len(periods))
        self.assertEqual([periods[0].get_time_period().start_time,
                          periods[1].get_time_period().start_time], [e.get_time_period().start_time for e in periods])
        self.assertEqual([self.mix_colors(self.color1, self.color2),
                          self.color2], [e.color for e in periods])

    def test_eras_can_return_a_list_with_added_overlapping_type3_eras(self):
        self.given_two_overlapping_eras_type_3()
        periods = self.eras.get_all_periods()
        self.assertEqual(2, len(periods))
        self.assertEqual([periods[0].get_time_period().start_time,
                          periods[1].get_time_period().start_time], [e.get_time_period().start_time for e in periods])
        self.assertEqual([self.mix_colors(self.color1, self.color2),
                          self.color1], [e.color for e in periods])

    def test_eras_can_return_a_list_with_added_overlapping_type4_eras(self):
        self.given_two_overlapping_eras_type_4()
        periods = self.eras.get_all_periods()
        self.assertEqual(1, len(periods))
        self.assertEqual([periods[0].get_time_period().start_time], [e.get_time_period().start_time for e in periods])
        self.assertEqual([self.mix_colors(self.color1, self.color2)], [e.color for e in periods])

    def test_eras_can_return_a_list_with_added_overlapping_type5_eras(self):
        self.given_two_overlapping_eras_type_5()
        periods = self.eras.get_all_periods()
        self.assertEqual(2, len(periods))
        self.assertEqual([periods[0].get_time_period().start_time,
                          periods[1].get_time_period().start_time], [e.get_time_period().start_time for e in periods])
        self.assertEqual([self.color1,
                          self.mix_colors(self.color1, self.color2)], [e.color for e in periods])

    def test_eras_can_return_a_list_with_added_overlapping_type6_eras(self):
        self.given_two_overlapping_eras_type_6()
        periods = self.eras.get_all_periods()
        self.assertEqual(3, len(periods))
        self.assertEqual([periods[0].get_time_period().start_time,
                          periods[1].get_time_period().start_time,
                          periods[2].get_time_period().start_time], [e.get_time_period().start_time for e in periods])
        self.assertEqual([self.color1,
                          self.mix_colors(self.color1, self.color2),
                          self.color1], [e.color for e in periods])

    def test_eras_can_return_a_list_with_3_overlapping_eras(self):
        """
        o-------(e1)-------o
              o-----(e2)----------o
           o--------(e3)------o
        """
        self.given_three_overlapping_eras()
        periods = self.eras.get_all_periods()
        self.assertEqual(5, len(periods))
        self.assertEqual([periods[0].get_time_period().start_time,
                          periods[1].get_time_period().start_time,
                          periods[2].get_time_period().start_time,
                          periods[3].get_time_period().start_time,
                          periods[4].get_time_period().start_time], [e.get_time_period().start_time for e in periods])
        self.assertEqual([self.color1,
                          self.mix_colors(self.color1, self.color3),
                          self.mix_3colors(self.color3, self.color1, self.color2),
                          self.mix_colors(self.color2, self.color3),
                          self.color2], [e.color for e in periods])

    def mix_colors(self, c0, c1):
        return ((c0[0] + c1[0]) / 2, (c0[1] + c1[1]) / 2, (c0[2] + c1[2]) / 2)

    def mix_3colors(self, c1, c2, c3):
        return self.mix_colors(self.mix_colors(c1, c2), c3)

    def given_two_overlapping_eras_type_1(self):
        self.era1 = a_gregorian_era_with(start="1 Dec 2015", end="1 Jan 2016", color=self.color1)
        self.era2 = a_gregorian_era_with(start="15 Dec 2015", end="1 Feb 2016", color=self.color2)
        self.eras.save_era(self.era2)
        self.eras.save_era(self.era1)

    def given_two_overlapping_eras_type_2(self):
        self.era1 = a_gregorian_era_with(start="1 Dec 2015", end="1 Jan 2016", color=self.color1)
        self.era2 = a_gregorian_era_with(start="1 Dec 2015", end="1 Feb 2016", color=self.color2)
        self.eras.save_era(self.era1)
        self.eras.save_era(self.era2)

    def given_two_overlapping_eras_type_3(self):
        self.era1 = a_gregorian_era_with(start="1 Dec 2015", end="1 Jan 2016", color=self.color1)
        self.era2 = a_gregorian_era_with(start="1 Dec 2015", end="15 Dec 2015", color=self.color2)
        self.eras.save_era(self.era1)
        self.eras.save_era(self.era2)

    def given_two_overlapping_eras_type_4(self):
        self.era1 = a_gregorian_era_with(start="1 Dec 2015", end="1 Jan 2016", color=self.color1)
        self.era2 = a_gregorian_era_with(start="1 Dec 2015", end="1 Jan 2016", color=self.color2)
        self.eras.save_era(self.era1)
        self.eras.save_era(self.era2)

    def given_two_overlapping_eras_type_5(self):
        self.era1 = a_gregorian_era_with(start="1 Dec 2015", end="1 Jan 2016", color=self.color1)
        self.era2 = a_gregorian_era_with(start="15 Dec 2015", end="1 Jan 2016", color=self.color2)
        self.eras.save_era(self.era2)
        self.eras.save_era(self.era1)

    def given_two_overlapping_eras_type_6(self):
        self.era1 = a_gregorian_era_with(start="1 Dec 2015", end="30 Jan 2016", color=self.color1)
        self.era2 = a_gregorian_era_with(start="15 Dec 2015", end="15 Jan 2016", color=self.color2)
        self.eras.save_era(self.era2)
        self.eras.save_era(self.era1)

    def given_three_overlapping_eras(self):
        self.era1 = a_gregorian_era_with(start="1 Jan 2016", end="30 Mar 2016", color=self.color1)
        self.era2 = a_gregorian_era_with(start="1 Feb 2016", end="30 Apr 2016", color=self.color2)
        self.era3 = a_gregorian_era_with(start="15 Jan 2016", end="15 Apr 2016", color=self.color3)
        self.eras.save_era(self.era1)
        self.eras.save_era(self.era2)
        self.eras.save_era(self.era3)


class describe_numeric_era_sublisting(ErasTestCase):

    def test_can_return_eras_visible_in_a_period(self):
        era1 = a_numeric_era_with(start=1, end=2)
        era2 = a_numeric_era_with(start=4, end=6)
        era3 = a_numeric_era_with(start=8, end=10)
        self.eras.save_era(era1)
        self.eras.save_era(era2)
        self.eras.save_era(era3)
        visible_eras = self.eras.get_in_period(numeric_period(3, 9))
        self.assertEquals([era2, era3], visible_eras)


class describe_gregorian_era_sublisting(ErasTestCase):

    def test_can_return_eras_visible_in_a_period(self):
        era1 = a_gregorian_era_with(start="1 Jan 2014", end="10 Jan 2014")
        era2 = a_gregorian_era_with(start="12 Jan 2014", end="16 Jan 2014")
        era3 = a_gregorian_era_with(start="18 Jan 2014", end="30 Jan 2014")
        self.eras.save_era(era1)
        self.eras.save_era(era2)
        self.eras.save_era(era3)
        visible_eras = self.eras.get_in_period(gregorian_period("16 Jan 2014", "20 Jan 2014"))
        self.assertEquals([era2, era3], visible_eras)
