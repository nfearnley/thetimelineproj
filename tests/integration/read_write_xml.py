# -*- coding: utf-8 -*-
# Copyright (C) 2009, 2010  Rickard Lindberg, Roger Lindberg
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


"""
Tests that XmlTimeline correctly writes and reads data.
"""


import tempfile
import os
import os.path
import shutil
import unittest
from datetime import datetime

from timelinelib.drawing.interface import ViewProperties
from timelinelib.db.objects import Event
from timelinelib.db.objects import Category
from timelinelib.db.objects import TimePeriod
from timelinelib.db.backends.xmlfile import XmlTimeline


class TestXmlTimelineWriteRead(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp(prefix="timeline-test")
        self.tmp_path = os.path.join(self.tmp_dir, "test.timeline")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def testWriteReadCycle(self):
        self._create_db()
        db_re_read = XmlTimeline(self.tmp_path)
        self._assert_re_read_db_same(db_re_read)

    def _create_db(self):
        db = XmlTimeline(self.tmp_path)
        # Create categories
        cat1 = Category("Category 1", (255, 0, 0), True)
        db.save_category(cat1)
        cat2 = Category("Category 2", (0, 255, 0), True, parent=cat1)
        db.save_category(cat2)
        cat3 = Category("Category 3", (0, 0, 255), True, parent=cat2)
        db.save_category(cat3)
        # Create events
        ev1 = Event(db, datetime(2010, 3, 3), datetime(2010, 3, 6),
                    "Event 1", cat1)
        ev1.set_data("description", u"The <b>first</b> event åäö.")
        db.save_event(ev1)
        # Create view properties
        vp = ViewProperties()
        start = datetime(2010, 3, 1)
        end = datetime(2010, 4, 1)
        vp.displayed_period = TimePeriod(start, end)
        vp.set_category_visible(cat3, False)
        db.save_view_properties(vp)

    def _assert_re_read_db_same(self, db):
        # Assert event correctly loaded
        events = db.get_all_events()
        self.assertEquals(len(events), 1)
        event = events[0]
        self.assertEquals(event.text, "Event 1")
        self.assertEquals(event.time_period.start_time, datetime(2010, 3, 3))
        self.assertEquals(event.time_period.end_time, datetime(2010, 3, 6))
        self.assertEquals(event.category.name, "Category 1")
        self.assertEquals(event.get_data("description"), u"The <b>first</b> event åäö.")
        self.assertEquals(event.get_data("icon"), None)
        # Assert that correct view properties are loaded (category visibility
        # checked later)
        vp = ViewProperties()
        db.load_view_properties(vp)
        self.assertEquals(vp.displayed_period.start_time, datetime(2010, 3, 1))
        self.assertEquals(vp.displayed_period.end_time, datetime(2010, 4, 1))
        # Assert categories correctly loaded
        categories = db.get_categories()
        self.assertEquals(len(categories), 3)
        for cat in categories:
            self.assertTrue(cat.has_id())
            if cat.name == "Category 1":
                self.assertEquals(cat.color, (255, 0, 0))
                self.assertTrue(vp.category_visible(cat))
                self.assertEquals(cat.parent, None)
            elif cat.name == "Category 2":
                self.assertEquals(cat.color, (0, 255, 0))
                self.assertTrue(vp.category_visible(cat))
                self.assertEquals(cat.parent.name, "Category 1")
            elif cat.name == "Category 3":
                self.assertEquals(cat.color, (0, 0, 255))
                self.assertFalse(vp.category_visible(cat))
                self.assertEquals(cat.parent.name, "Category 2")
            else:
                self.fail("Unknown category.")
