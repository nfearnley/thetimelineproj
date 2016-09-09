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


import random

from datetime import date
from datetime import datetime
from datetime import timedelta
from os.path import abspath

from icalendar import Calendar

from timelinelib.calendar.gregorian import Gregorian, GregorianUtils
from timelinelib.canvas.data.db import MemoryDB
from timelinelib.canvas.data.exceptions import TimelineIOError
from timelinelib.canvas.data import Event
from timelinelib.canvas.data import Category
from timelinelib.utils import ex_msg
from timelinelib.time.timeline import TimeDelta


class IcsLoader(object):

    def load(self, db, path, options):
        (self.add_location_to_description,
         self.use_trigger_as_start_date,
         self.use_trigger_as_alert) = options
        self.events = []
        self.categories = []
        self.category_names = []
        file_contents = self._read_file_content(path)
        cal = self._read_calendar_object(file_contents)
        self._load_events(cal, db)
        self._load_todos(cal, db)
        self._save_data_in_db(db)

    def _load_events(self, cal, db):
        for vevent in cal.walk("VEVENT"):
            self._load_vevent(db, vevent)
            self._load_categories(vevent)

    def _load_todos(self, cal, db):
        for vtodo in cal.walk("VTODO"):
            self._load_vtodo(db, vtodo)
            self._load_categories(vtodo)

    def _load_vtodo(self, db, vtodo):
        try:
            start, end = self._extract_todo_start_end(vtodo)
            txt = self._get_event_name(vtodo)
            event = Event(start, end, txt)
            event.set_description(self._extract_todo_description(vtodo))
            event.set_alert(self._extract_todo_alert(vtodo))
            self.events.append(event)
        except KeyError:
            pass

    def _extract_todo_start_end(self, vtodo):
        end = self._extract_todo_end(vtodo)
        if self.use_trigger_as_start_date:
            start = self._extract_todo_start(vtodo)
            if start is None:
                start = end
        else:
            start = end
        return start, end

    def _extract_todo_end(self, vtodo):
        end = self._get_value(vtodo, "due")
        if end:
            return self._convert_to_datetime(end)
        else:
            raise KeyError("Start time not found")

    def _extract_todo_start(self, vtodo):
        valarm = self._get_first_subelement(vtodo, "VALARM")
        if valarm:
            start = self._get_value(valarm, "trigger")
            if start:
                return self._convert_to_datetime(start)

    def _extract_todo_description(self, vtodo):
        if self.add_location_to_description:
            if "location" in vtodo:
                return "%s: %s" % (_("Location"), vtodo["location"])
            else:
                return None
        else:
            return None

    def _extract_todo_alert(self, vtodo):
        if self.use_trigger_as_alert:
            start = self._extract_todo_start(vtodo)
            if start is not None:
                return (start, "")

    def _read_calendar_object(self, file_contents):
        try:
            return Calendar.from_ical(file_contents)
        except Exception, pe:
            msg1 = _("Unable to read calendar data.")
            msg2 = "\n\n" + ex_msg(pe)
            raise TimelineIOError(msg1 + msg2)

    def _read_file_content(self, path):
        ics_file = None
        try:
            ics_file = open(path, "rb")
            return ics_file.read()
        except IOError, e:
            msg = _("Unable to read from file '%s'.")
            whole_msg = (msg + "\n\n%s") % (abspath(path), e)
            raise TimelineIOError(whole_msg)
        finally:
            if ics_file is not None:
                ics_file.close()

    def _save_data_in_db(self, db):
        for event in self.events:
            db.save_event(event)
        for category in self.categories:
            db.save_category(category)

    def _load_vevent(self, db, vevent):
        start, end = self._extract_start_end(vevent)
        txt = self._get_event_name(vevent)
        event = Event(start, end, txt)
        event.set_description(self._get_description(vevent))
        self.events.append(event)

    def _load_categories(self, vevent):
        if "categories" in vevent:
            categories_names = set([cat.strip() for cat in vevent["categories"].split(",") if len(cat.strip()) > 0])
            for category_name in categories_names:
                if category_name not in self.category_names:
                    self.categories.append(Category(category_name, self._get_random_color(), None))
                    self.category_names.append(category_name)

    def _get_random_color(self):
        return (random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255))

    def _get_event_name(self, vevent):
        return self._get_first_value(vevent, ["summary", "description"], "")

    def _get_description(self, vevent):
        if self.add_location_to_description:
            if "location" in vevent:
                sep = ""
                if "description" in vevent:
                    sep = "\n\n"
                return "%s%s%s: %s" % (self._get_value(vevent, "description", ""),
                                      sep,
                                      _("Location"),
                                      self._get_value(vevent, "location", ""))
            else:
                return self._get_value(vevent, "description", None)
        else:
            return self._get_value(vevent, "description", None)

    def _get_first_value(self, element, key_list, not_found_value=None):
        for key in key_list:
            if key in element:
                return element[key]
        return not_found_value

    def _get_value(self, element, key, not_found_value=None):
        if key in element:
            return element.decoded(key)
        return not_found_value

    def _extract_start_end(self, vevent):
        start = self._convert_to_datetime(vevent.decoded("dtstart"))
        if "dtend" in vevent:
            end = self._convert_to_datetime(vevent.decoded("dtend"))
        elif "duration" in vevent:
            end = start + self._convert_to_timedelta(vevent.decoded("duration"))
        else:
            end = self._convert_to_datetime(vevent.decoded("dtstart"))
        return (start, end)

    def _convert_to_timedelta(self, t):
        if isinstance(t, timedelta):
            return TimeDelta(t.seconds)
        else:
            return TimeDelta(0)

    def _convert_to_datetime(self, d):
        if isinstance(d, datetime):
            return Gregorian(d.year, d.month, d.day, d.hour, d.minute, d.second).to_time()
        elif isinstance(d, date):
            return GregorianUtils.from_date(d.year, d.month, d.day).to_time()
        else:
            raise TimelineIOError("Unknown date.")

    def _get_first_subelement(self, parent, subelement_name):
        subelements = self._get_subelements(parent, subelement_name)
        if len(subelements) > 0:
            return subelements[0]

    def _get_subelements(self, parent, subelement_name):
        return parent.walk(subelement_name)


def import_db_from_ics(path, options_dialog=None, options=None):
    global events
    events = []
    if options is None:
        options = [False, False, False]
    db = MemoryDB()
    db.set_readonly()
    if options_dialog is not None:
        dlg = options_dialog()
        dlg.ShowModal()
        options = (dlg.get_import_location(),
                   dlg.get_trigger_as_start_time(),
                   dlg.get_trigger_as_alarm())
        dlg.Destroy()
    IcsLoader().load(db, path, options)
    return db
