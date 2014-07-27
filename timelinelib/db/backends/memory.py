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


"""
Implementation of timeline database that stores all data in memory.

MemoryDB can be used as a base class for other timeline databases that wish to
store all data in memory and also want to save the data to persistent storage
whenever it changes in memory. Initially data can be read from persistent
storage into memory.

MemoryDB is not suitable as a base class for timeline databases that need to
query persistent storage to retrieve data.
"""


from timelinelib.db.exceptions import TimelineIOError
from timelinelib.db.objects import Category
from timelinelib.db.objects import Container
from timelinelib.db.objects import Event
from timelinelib.utilities.observer import Observable
from timelinelib.utilities.observer import STATE_CHANGE_ANY
from timelinelib.utilities.observer import STATE_CHANGE_CATEGORY
from timelinelib.db.search import generic_event_search
from timelinelib.db.utils import IdCounter
from timelinelib.db.objects.event import clone_event_list
from timelinelib.db.objects.category import clone_categories_list
from timelinelib.db.undo.undohandler import UndoHandler


class MemoryDB(Observable):

    def __init__(self):
        Observable.__init__(self)
        self.path = ""
        self.categories = []
        self.category_id_counter = IdCounter()
        self.events = []
        self.event_id_counter = IdCounter()
        self.displayed_period = None
        self.hidden_categories = []
        self.save_disabled = False
        from timelinelib.time.gregoriantime import GregorianTimeType
        self.time_type = GregorianTimeType()
        self.readonly = False
        self.importing = False
        self._undo_handler = UndoHandler(self)

    def get_time_type(self):
        return self.time_type

    def is_read_only(self):
        return self.readonly

    def set_readonly(self):
        self.readonly = True
        
    def supported_event_data(self):
        return ["description", "icon", "alert", "hyperlink", "progress"]

    def search(self, search_string):
        return generic_event_search(self.events, search_string)

    def get_events(self, time_period):
        def include_event(event):
            if not event.inside_period(time_period):
                return False
            return True
        return [e for e in self.events if include_event(e)]

    def get_all_events(self):
        return list(self.events)

    def get_first_event(self):
        if len(self.events) == 0:
            return None
        e = min(self.events, key=lambda e: e.time_period.start_time)
        return e

    def get_last_event(self):
        if len(self.events) == 0:
            return None
        e = max(self.events, key=lambda e: e.time_period.end_time)
        return e

    def save_event(self, event):
        if (event.category is not None and
            event.category not in self.categories):
            raise TimelineIOError("Event's category not in db.")
        if event not in self.events:
            if event.has_id():
                raise TimelineIOError("Event with id %s not found in db." %
                                      event.id)
            self.events.append(event)
            event.set_id(self.event_id_counter.get_next())
            if event.is_subevent():
                self._register_subevent(event)
        self._save_if_not_disabled()
        self._notify(STATE_CHANGE_ANY)

    def _register_subevent(self, subevent):
        container_events = [event for event in self.events
                            if event.is_container()]
        containers = {}
        for container in container_events:
            key = container.cid()
            containers[key] = container
        try:
            container = containers[subevent.cid()]
            container.register_subevent(subevent)
        except:
            id = subevent.cid()
            if id == 0:
                id = self._get_max_container_id(container_events) + 1
                subevent.set_cid(id)
            name = "[%d]Container" % id
            container = Container(subevent.time_type,
                                  subevent.time_period.start_time,
                                  subevent.time_period.end_time, name)
            self.save_event(container)
            self._register_subevent(subevent)
            pass

    def _get_max_container_id(self, container_events):
        id = 0
        for event in container_events:
            if id < event.cid():
                id = event.cid()
        return id

    def _unregister_subevent(self, subevent):
        container_events = [event for event in self.events
                            if event.is_container()]
        containers = {}
        for container in container_events:
            containers[container.cid()] = container
        try:
            container = containers[subevent.cid()]
            container.unregister_subevent(subevent)
            if len(container.events) == 0:
                self.events.remove(container)
        except:
            pass

    def delete_event(self, event_or_id, save=True):
        if isinstance(event_or_id, Event):
            event = event_or_id
        else:
            event = self.find_event_with_id(event_or_id)
        if event in self.events:
            if event.is_subevent():
                self._unregister_subevent(event)
            if event.is_container():
                for subevent in event.events:
                    self.events.remove(subevent)
            self.events.remove(event)
            event.set_id(None)
            if save:
                self._save_if_not_disabled()
                self._notify(STATE_CHANGE_ANY)

    def get_categories(self):
        return list(self.categories)

    def get_containers(self):
        containers = [event for event in self.events
                      if event.is_container()]
        return containers

    def save_category(self, category):
        if (category.parent is not None and
            category.parent not in self.categories):
            raise TimelineIOError("Parent category not in db.")
        self._ensure_no_circular_parent(category)
        if not category in self.categories:
            if self.importing:
                if not self._category_name_exists(category):
                    self._append_category(category)
            else:
                self._append_category(category)
        self._save_if_not_disabled()
        self._notify(STATE_CHANGE_CATEGORY)

    def loaded(self):
        self._undo_handler.enable(True)
        self._undo_handler.save()

    def _category_name_exists(self, category):
        return self._get_category_by_name(category) is not None
        
    def _append_category(self, category):
        if category.has_id():
            raise TimelineIOError("Category with id %s not found in db." %
                                  category.id)
        self.categories.append(category)
        category.set_id(self.event_id_counter.get_next())
        
    def _get_category_by_name(self, category):
        for cat in self.categories:
            if cat.name == category.name:
                return cat

    def delete_category(self, category_or_id):
        if isinstance(category_or_id, Category):
            category = category_or_id
        else:
            category = self._find_category_with_id(category_or_id)
        if category in self.categories:
            if category in self.hidden_categories:
                self.hidden_categories.remove(category)
            self.categories.remove(category)
            category.set_id(None)
            # Loop to update parent attribute on children
            for cat in self.categories:
                if cat.parent == category:
                    cat.parent = category.parent
            # Loop to update category for events
            for event in self.events:
                if event.category == category:
                    event.category = category.parent
            self._save_if_not_disabled()
            self._notify(STATE_CHANGE_CATEGORY)
        else:
            raise TimelineIOError("Category not in db.")

    def load_view_properties(self, view_properties):
        view_properties.displayed_period = self.displayed_period
        for cat in self.categories:
            visible = cat not in self.hidden_categories
            view_properties.set_category_visible(cat, visible)

    def save_view_properties(self, view_properties):
        if view_properties.displayed_period is not None:
            if not view_properties.displayed_period.is_period():
                raise TimelineIOError(_("Displayed period must be > 0."))
            self.displayed_period = view_properties.displayed_period
        self.hidden_categories = []
        for cat in self.categories:
            if not view_properties.is_category_visible(cat):
                self.hidden_categories.append(cat)
        self._save_if_not_disabled()

    def disable_save(self):
        self.save_disabled = True

    def enable_save(self, call_save=True):
        if self.save_disabled == True:
            self.save_disabled = False
            if call_save == True:
                self._save_if_not_disabled()

    def place_event_after_event(self, event_to_place, target_event):
        if (event_to_place == target_event):
            return
        self.events.remove(event_to_place)
        new_index = self.events.index(target_event) + 1
        self.events.insert(new_index, event_to_place)

    def place_event_before_event(self, event_to_place, target_event):
        if (event_to_place == target_event):
            return
        self.events.remove(event_to_place)
        new_index = self.events.index(target_event)
        self.events.insert(new_index, event_to_place)

    def undo(self):
        if self._undo_handler.undo():
            self.categories, self.events = self._undo_handler.get_data()
            self._save_if_not_disabled()
            self._notify(STATE_CHANGE_ANY)
            self._undo_handler.enable(True)

    def redo(self):
        if self._undo_handler.redo():
            self.categories, self.events = self._undo_handler.get_data()
            self._save_if_not_disabled()
            self._notify(STATE_CHANGE_ANY)
            self._undo_handler.enable(True)    

    def _ensure_no_circular_parent(self, cat):
        parent = cat.parent
        while parent is not None:
            if parent == cat:
                raise TimelineIOError("Circular category parent.")
            else:
                parent = parent.parent

    def find_event_with_id(self, id):
        for e in self.events:
            if e.id == id:
                return e
        return None

    def _find_category_with_id(self, id):
        for c in self.categories:
            if c.id == id:
                return c
        return None

    def _save_if_not_disabled(self):
        if self.save_disabled == False:
            self._save()
        self._undo_handler.save()

    def _get_displayed_period(self):
        """
        Inheritors can call this method to get the displayed period used in
        load_view_properties and save_view_properties.
        """
        return self.displayed_period

    def _set_displayed_period(self, period):
        """
        Inheritors can call this method to set the displayed period used in
        load_view_properties and save_view_properties.
        """
        self.displayed_period = period

    def _get_hidden_categories(self):
        """
        Inheritors can call this method to get the hidden categories used in
        load_view_properties and save_view_properties.
        """
        return self.hidden_categories

    def _set_hidden_categories(self, hidden_categories):
        """
        Inheritors can call this method to set the hidden categories used in
        load_view_properties and save_view_properties.
        """
        self.hidden_categories = []
        for cat in hidden_categories:
            if cat not in self.categories:
                raise ValueError("Category '%s' not in db." % cat.name)
            self.hidden_categories.append(cat)

    def _save(self):
        """
        Inheritors can override this method to save this db to persistent
        storage.

        Called whenever this db changes.
        """
        pass


def clone_data(categories, events):
    categories, catclones = clone_categories_list(categories)
    events = clone_event_list(events)
    for event in events:
        try:
            event.category = catclones[event.category]
        except KeyError:
            event.category = None
    return categories, events
    
