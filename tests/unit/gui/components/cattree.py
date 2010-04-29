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


import unittest

from mock import Mock

from timelinelib.gui.components.cattree import CategoriesTreeController
from timelinelib.db.interface import TimelineIOError
from timelinelib.db.objects import Category


class TestCategoiresTreeController(unittest.TestCase):

    def setUp(self):
        # Setup mock for db with this category configuration:
        # foo
        #   foofoo
        # bar
        self.db = Mock()
        self.foo = Category("foo", (255, 0, 0), True, parent=None)
        self.foofoo = Category("foofoo", (255, 0, 0), True, parent=self.foo)
        self.bar = Category("bar", (255, 0, 0), True, parent=None)
        self.db.get_categories.return_value = [self.foo, self.foofoo, self.bar]
        # Setup mock for view
        self.view = Mock()
        # Setup mock for timeline view
        self.timeline_view = Mock()
        self.timeline_view.timeline = self.db
        self.timeline_view.view_properties = Mock()
        # Setup mock for error fn
        self.fn_handle_db_error = Mock()

    def testInitFromDb(self):
        controller = CategoriesTreeController(self.view,
                                              self.fn_handle_db_error)
        controller.initialize_from_db(self.db)
        self.view.set_category_tree.assert_called_with([
            (self.bar, []),
            (self.foo, [
                (self.foofoo, []),
            ])
        ], None)

    def testInitFromTimelineView(self):
        controller = CategoriesTreeController(self.view,
                                              self.fn_handle_db_error)
        controller.initialize_from_timeline_view(self.timeline_view)
        self.view.set_category_tree.assert_called_with([
            (self.bar, []),
            (self.foo, [
                (self.foofoo, []),
            ])
        ], self.timeline_view.view_properties)
