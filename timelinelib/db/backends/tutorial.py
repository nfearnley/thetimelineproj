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


from datetime import datetime
from datetime import timedelta

from timelinelib.db.objects import Category
from timelinelib.db.objects import Event
from timelinelib.db.objects import TimePeriod
from timelinelib.db.backends.memory import MemoryDB
from timelinelib.time.gregorian import gregorian_to_timeline_date_time
from timelinelib.time.gregorian import Gregorian
from timelinelib.time.timeline import TimelineDelta
from timelinelib.time.gregoriantime import GregorianTimeType


def create_in_memory_tutorial_db():
    tutcreator = TutorialTimelineCreator()
    tutcreator.add_category(_("Welcome"), (255, 80, 80), (0, 0, 0))
    tutcreator.add_event(
        _("Welcome to Timeline"),
        "",
        tutcreator.get_days_delta(4))
    tutcreator.add_category(_("Intro"), (250, 250, 20), (0, 0, 0))
    tutcreator.add_event(
        _("Hover me!"),
        _("Hovering events with a triangle shows the event description."),
        tutcreator.get_days_delta(5))
    tutcreator.add_category(_("Features"), (100, 100, 250), (250, 250, 20))
    tutcreator.add_event(
        _("Scroll"),
        _("Left click somewhere on the timeline and start dragging."
          "\n\n"
          "You can also use the mouse wheel."
          "\n\n"
          "You can also middle click with the mouse to center around that point."),
        tutcreator.get_days_delta(5),
        tutcreator.get_days_delta(10))
    tutcreator.add_event(
        _("Zoom"),
        _("Hold down Ctrl while scrolling the mouse wheel."
          "\n\n"
          "Hold down Shift while dragging with the mouse."),
        tutcreator.get_days_delta(6),
        tutcreator.get_days_delta(11))
    tutcreator.add_event(
        _("Create event"),
        _("Double click somewhere on the timeline."
          "\n\n"
          "Hold down Ctrl while dragging the mouse to select a period."),
        tutcreator.get_days_delta(12),
        tutcreator.get_days_delta(18))
    tutcreator.add_event(
        _("Edit event"),
        _("Double click on an event."),
        tutcreator.get_days_delta(12),
        tutcreator.get_days_delta(18))
    tutcreator.add_event(
        _("Select event"),
        _("Click on it."
          "\n\n"
          "Hold down Ctrl while clicking events to select multiple."),
        tutcreator.get_days_delta(20),
        tutcreator.get_days_delta(25))
    tutcreator.add_event(
        _("Delete event"),
        _("Select events to be deleted and press the Del key."),
        tutcreator.get_days_delta(19),
        tutcreator.get_days_delta(24))
    tutcreator.add_event(
        _("Resize and move me!"),
        _("First select me and then drag the handles."),
        tutcreator.get_days_delta(11),
        tutcreator.get_days_delta(19))
    tutcreator.add_category(_("Saving"), (50, 200, 50), (0, 0, 0))
    tutcreator.add_event(
        _("Saving"),
        _("This timeline is stored in memory and modifications to it will not "
          "be persisted between sessions."
          "\n\n"
          "Choose File/New/File Timeline to create a timeline that is saved on "
          "disk."),
        tutcreator.get_days_delta(23))
    return tutcreator.get_db()


class TutorialTimelineCreator(object):

    def __init__(self):
        self.db = MemoryDB()
        #self.db.time_type = GregorianTimeType()
        now = datetime.now()
        self.start = self.get_time(now.year, now.month, 1)
        self.end = self.start + self.get_days_delta(30)
        self.db._set_displayed_period(TimePeriod(self.db.get_time_type(),
                                                 self.start, self.end))
        self.last_cat = None

    def add_category(self, name, color, font_color, make_last_added_parent=False):
        if make_last_added_parent:
            parent = self.last_cat
        else:
            parent = None
        self.last_cat = Category(name, color, font_color, True, parent)
        self.db.save_category(self.last_cat)

    def add_event(self, text, description, start_add, end_add=None):
        start = self.start + start_add
        end   = start
        if end_add is not None:
            end = self.start + end_add
        evt = Event(self.db.get_time_type(), start, end, text, self.last_cat)
        if description:
            evt.set_data("description", description)
        self.db.save_event(evt)

    def get_db(self):
        return self.db

    def get_days_delta(self, days):
        if self.db.get_time_type().get_name() == u"pytime":
            return timedelta(days=days)
        if self.db.get_time_type().get_name() == u"gregoriantime":
            return TimelineDelta(days * 24 * 60 * 60)

    def get_time(self, year, month, day):
        if self.db.get_time_type().get_name() == u"pytime":
            return datetime(year, month, day, 0, 0, 0)
        if self.db.get_time_type().get_name() == u"gregoriantime":
            return gregorian_to_timeline_date_time(Gregorian(year, month, day, 0, 0, 0))
