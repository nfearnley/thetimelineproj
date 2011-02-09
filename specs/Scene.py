# Copyright (C) 2009, 2010, 2011  Rickard Lindberg, Roger Lindberg
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


import datetime
import unittest

from timelinelib.db.backends.memory import MemoryDB
from timelinelib.db.objects import Category
from timelinelib.db.objects import Event
from timelinelib.db.objects import TimePeriod
from timelinelib.drawing.interface import ViewProperties
from timelinelib.drawing.scene import TimelineScene
from timelinelib.monthnames import ABBREVIATED_ENGLISH_MONTH_NAMES
from timelinelib.time.pytime import PyTimeType


class SceneSpec(unittest.TestCase):

    def test_has_no_hidden_events_when_all_events_belong_to_visible_categories(self):
        self.given_displayed_period("1 Jan 2010", "10 Jan 2010")
        self.given_visible_event_at("5 Jan 2010")
        self.when_scene_is_created()
        self.assertEquals(0, self.scene.get_hidden_event_count())

    def test_has_hidden_events_for_all_events_belonging_to_hidden_categories(self):
        self.given_displayed_period("1 Jan 2010", "10 Jan 2010")
        self.given_visible_event_at("5 Jan 2010")
        self.given_hidden_event_at("5 Jan 2010")
        self.when_scene_is_created()
        self.assertEquals(1, self.scene.get_hidden_event_count())

    def test_considers_events_outside_screen_hidden(self):
        self.given_displayed_period("1 Jan 2010", "10 Jan 2010")
        self.given_number_of_events_stackable_is(5)
        for i in range(6):
            self.given_visible_event_at("5 Jan 2010")
        self.when_scene_is_created()
        self.assertEquals(1, self.scene.get_hidden_event_count())

    def setUp(self):
        self.db = MemoryDB()
        self.view_properties = ViewProperties()
        self.given_number_of_events_stackable_is(5)

    def get_text_size_fn(self, text):
        return (len(text), self.event_height)

    def given_number_of_events_stackable_is(self, number):
        self.event_height = 10
        self.size = (100, 2*self.event_height*number)
        self.view_properties.divider_position = 0.5
        self.outer_padding = 0
        self.inner_padding = 0
        self.baseline_padding = 0

    def given_displayed_period(self, start, end):
        self.view_properties.displayed_period = py_period(start, end)

    def given_visible_event_at(self, time):
        self.given_event_at(time, visible=True)

    def given_hidden_event_at(self, time):
        self.given_event_at(time, visible=False)

    def given_event_at(self, time, visible):
        category = Category("category", (0, 0, 0), visible)
        event = Event(self.db, human_time_to_py(time), human_time_to_py(time), "event", category)
        self.db.save_category(category)
        self.db.save_event(event)
        self.view_properties.set_category_visible(category, visible)

    def when_scene_is_created(self):
        self.scene = TimelineScene(
            self.size, self.db, self.view_properties, self.get_text_size_fn)
        self.scene.set_outer_padding(self.outer_padding)
        self.scene.set_inner_padding(self.inner_padding)
        self.scene.set_baseline_padding(self.baseline_padding)
        self.scene.create()


def py_period(start, end):
    return TimePeriod(PyTimeType(), human_time_to_py(start), human_time_to_py(end))


def human_time_to_py(human_time):
    (year, month, day) = human_time_to_ymd(human_time)
    return py_time(year, month, day)


def human_time_to_ymd(human_time):
    day_part, month_part, year_part = human_time.split(" ")
    day = int(day_part)
    month = ABBREVIATED_ENGLISH_MONTH_NAMES.index(month_part) + 1
    year = int(year_part)
    return (year, month, day)


def py_time(year, month, day, hour=15, minute=30, second=5):
    return datetime.datetime(year, month, day, hour, minute, second)
