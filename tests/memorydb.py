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


from datetime import datetime
import unittest

from mock import Mock

from timelinelib.db.interface import TimelineIOError
from timelinelib.db.objects import Category
from timelinelib.db.objects import Event
from timelinelib.db.objects import TimePeriod
from timelinelib.db.backends.memory import MemoryDB


class TestMemoryDB(unittest.TestCase):

    def setUp(self):
        self.db = MemoryDB()
        self.db_listener = Mock()
        self.c1 = Category("work", (255, 0, 0), True)
        self.c2 = Category("private", (0, 255, 0), True)
        self.e1 = Event(datetime(2010, 2, 13), datetime(2010, 2, 13), "holiday")
        self.e2 = Event(datetime(2010, 2, 14), datetime(2010, 2, 14), "work starts")
        self.db.register(self.db_listener)

    def testInitialState(self):
        db = MemoryDB()
        self.assertEquals(db.path, "")
        self.assertEquals(db.is_read_only(), False)
        self.assertEquals(db.supported_event_data(), ["description", "icon"])
        self.assertEquals(db.search(""), [])
        self.assertEquals(db.get_first_event(), None)
        self.assertEquals(db.get_last_event(), None)
        self.assertEquals(db.get_categories(), [])
        # Ensure these don't raise exceptions (they should not nothing)
        db.load_view_properties(None)
        db.save_view_properties(None)

    def testSaveNewCategory(self):
        self.db.save_category(self.c1)
        self.assertTrue(self.c1.has_id())
        self.assertEqual(self.db.get_categories(), [self.c1])
        self.assertEqual(self.db_listener.call_count, 1)

    def testSaveExistingCategory(self):
        self.db.save_category(self.c1)
        id_before = self.c1.id
        self.c1.name = "Work"
        self.c1.color = (1, 2, 3)
        self.db.save_category(self.c1)
        self.assertEqual(id_before, self.c1.id)
        self.assertEqual(self.db.get_categories(), [self.c1])
        self.assertEqual(self.db_listener.call_count, 2) # 2 save

    def testDeleteExistingCategory(self):
        self.db.save_category(self.c1)
        self.db.save_category(self.c2)
        # Assert both categories in db
        categories = self.db.get_categories()
        self.assertEquals(len(categories), 2)
        self.assertTrue(self.c1 in categories)
        self.assertTrue(self.c2 in categories)
        # Remove first (by category)
        self.db.delete_category(self.c1)
        categories = self.db.get_categories()
        self.assertEquals(len(categories), 1)
        self.assertTrue(self.c2 in categories)
        self.assertFalse(self.c1.has_id())
        # Remove second (by id)
        self.db.delete_category(self.c2.id)
        categories = self.db.get_categories()
        self.assertEquals(len(categories), 0)
        self.assertFalse(self.c2.has_id())
        # Check events
        self.assertEqual(self.db_listener.call_count, 4) # 2 save, 2 delete

    def testDeleteNonExistingCategory(self):
        self.assertRaises(TimelineIOError, self.db.delete_category, self.c1)

    def testSaveNewEventUnknownCategory(self):
        self.e1.category = self.c1
        self.assertRaises(TimelineIOError, self.db.save_event, self.e1)

    def testSaveNewEvent(self):
        self.db.save_event(self.e1)
        tp = TimePeriod(datetime(2010, 2, 12), datetime(2010, 2, 14))
        self.assertTrue(self.e1.has_id())
        self.assertEqual(self.db.get_events(tp), [self.e1])
        self.assertEqual(self.db_listener.call_count, 1) # 1 save

    def testSaveExistingEvent(self):
        self.db.save_event(self.e1)
        id_before = self.e1.id
        self.e1.text = "Holiday!!"
        self.db.save_event(self.e1)
        tp = TimePeriod(datetime(2010, 2, 12), datetime(2010, 2, 14))
        self.assertEqual(id_before, self.e1.id)
        self.assertEqual(self.db.get_events(tp), [self.e1])
        self.assertEqual(self.db_listener.call_count, 2) # 1 save

    def testDeleteExistingEvent(self):
        tp = TimePeriod(datetime(2010, 2, 12), datetime(2010, 2, 15))
        self.db.save_event(self.e1)
        self.db.save_event(self.e2)
        # Assert both in db
        self.assertEquals(len(self.db.get_events(tp)), 2)
        self.assertTrue(self.e1 in self.db.get_events(tp))
        self.assertTrue(self.e2 in self.db.get_events(tp))
        # Delete first (by event)
        self.db.delete_event(self.e1)
        self.assertFalse(self.e1.has_id())
        self.assertEquals(len(self.db.get_events(tp)), 1)
        self.assertTrue(self.e2 in self.db.get_events(tp))
        # Delete second (by id)
        self.db.delete_event(self.e2.id)
        self.assertFalse(self.e2.has_id())
        self.assertEquals(len(self.db.get_events(tp)), 0)
        # Check events
        self.assertEqual(self.db_listener.call_count, 4) # 2 save, 2 delete

    def testDeleteNonExistingEvent(self):
        self.assertRaises(TimelineIOError, self.db.delete_event, self.e1)
