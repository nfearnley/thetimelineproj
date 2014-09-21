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


from specs.utils import a_category_with
from specs.utils import an_event
from specs.utils import an_event_with
from specs.utils import TestCase
from timelinelib.data.events import InvalidOperationError
from timelinelib.data import Events


class EventsTestCase(TestCase):

    def setUp(self):
        self.events = Events()


class describe_cloning(EventsTestCase):

    def test_categories_are_cloned(self):
        self.events.save_category(a_category_with(name="work"))
        self.events.save_category(a_category_with(name="football"))
        self.events.save_category(a_category_with(
            name="meetings",
            parent=self.events.get_category_by_name("work")))
        clone = self.events.clone()
        self.assertListIsCloneOf(clone.get_categories(),
                                 self.events.get_categories())
        self.assertIsCloneOf(clone.get_category_by_name("meetings").get_parent(),
                             self.events.get_category_by_name("work"))


class describe_saving_categories(EventsTestCase):

    def test_can_save(self):
        category = a_category_with(name="work")
        self.events.save_category(category)
        self.assertEqual(self.events.get_categories(), [category])

    def test_can_update(self):
        self.events.save_category(a_category_with(name="work"))
        updated_category = self.events.get_categories()[0]
        updated_category.set_color((50, 100, 150))
        self.events.save_category(updated_category)
        self.assertEqual(self.events.get_categories(), [updated_category])

    def test_fails_if_new_category_has_existing_name(self):
        self.events.save_category(a_category_with(name="work"))
        self.assertRaises(InvalidOperationError,
                          self.events.save_category,
                          a_category_with(name="work"))

    def test_fails_if_category_has_existing_name(self):
        self.events.save_category(a_category_with(name="work"))
        self.events.save_category(a_category_with(name="sports"))
        updated_category = self.events.get_category_by_name("work")
        updated_category.set_name("sports")
        self.assertRaises(InvalidOperationError,
                          self.events.save_category, updated_category)

    def test_fails_if_parent_is_not_in_db(self):
        self.assertRaises(InvalidOperationError,
                          self.events.save_category,
                          a_category_with(name="work",
                                          parent=a_category_with(name="parent")))

    def test_fails_if_parent_relationship_is_circular(self):
        self.events.save_category(
            a_category_with(name="root",
                            parent=None))
        self.events.save_category(
            a_category_with(name="child",
                            parent=self.events.get_category_by_name("root")))
        self.events.save_category(
            a_category_with(name="grandchild",
                            parent=self.events.get_category_by_name("child")))
        grandchild = self.events.get_category_by_name("grandchild")
        child = self.events.get_category_by_name("child")
        child.set_parent(grandchild)
        self.assertRaises(InvalidOperationError,
                          self.events.save_category, child)

    def test_fails_if_existing_category_does_not_seem_to_be_found(self):
        category = a_category_with(name="work")
        category.set_id(15)
        self.assertRaises(InvalidOperationError,
                          self.events.save_category,
                          category)


class describe_saving_events(EventsTestCase):

    def test_can_save(self):
        event = an_event()
        self.events.save_event(event)
        self.assertEqual(self.events.get_all(), [event])

    def test_can_update(self):
        self.events.save_event(an_event())
        event = self.events.get_first()
        event.set_text("I'm the first event")
        self.events.save_event(event)
        self.assertEqual(self.events.get_all(), [event])

    def test_fails_if_category_does_not_exist(self):
        self.assertRaises(InvalidOperationError,
                          self.events.save_event,
                          an_event_with(category=a_category_with(name="work")))


    def test_fails_if_existing_event_does_not_seem_to_be_found(self):
        event = an_event()
        event.set_id(15)
        self.assertRaises(InvalidOperationError,
                          self.events.save_event, event)
