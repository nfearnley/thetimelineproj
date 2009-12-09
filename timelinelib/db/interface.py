# Copyright (C) 2009  Rickard Lindberg, Roger Lindberg
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
Definition of interface that timeline databases should adhere to.

Actual implementations of timeline databases are in the backends package.
"""


from timelinelib.observer import Observable


# A category was added, edited, or deleted
STATE_CHANGE_CATEGORY = 1
# Something happened that changed the state of the timeline
STATE_CHANGE_ANY = 2


class TimelineDB(Observable):
    """
    Read (and write) timeline data from persistent storage.

    All methods that modify timeline data should automatically write it to
    persistent storage.

    A TimelineIOError should be raised if reading or writing fails. After such
    a failure the database it not guarantied to return correct data. (Read and
    write errors are however very rare.)

    A timeline database is observable so that GUI components can update
    themselves when data changes. The two types of state changes are given as
    constants above.

    Future considerations: If databases get large it might be inefficient to
    save to persistent storage every time we modify the database. A solution is
    to add an explicit save method and have all the other methods just modify
    the database in memory.
    """

    def __init__(self, path):
        Observable.__init__(self)
        self.path = path

    def is_read_only(self):
        """
        Return True if you can only read from this database and False if you
        can both read and write.
        """
        raise NotImplementedError()

    def supported_event_data(self):
        """
        Return a list of event data that we can read and write.

        Event data is represented by a string id. See event.set_data for
        information what string id map to what data.
        """
        raise NotImplementedError()

    def get_events(self, time_period):
        """
        Return a list of events visible within the time period.

        An event is visible if its associated category is visible or of it does
        not belong to a category.
        """
        raise NotImplementedError()

    def get_first_event(self):
        """Return the event with the lowest start time"""
        raise NotImplementedError()
        
    def get_last_event(self):
        """Return the event with the highest end time"""
        raise NotImplementedError()
        
    def save_event(self, event):
        """
        Make sure that the given event is saved to persistent storage.

        If the event is new it is given a new unique id. Otherwise the
        information in the database is just updated.
        """
        raise NotImplementedError()

    def delete_event(self, event_or_id):
        """
        Delete the event (or the event with the given id) from the database.
        """
        raise NotImplementedError()

    def get_categories(self):
        """
        Return a list of all available categories.
        """
        raise NotImplementedError()

    def save_category(self, category):
        """
        Make sure that the given category is saved to persistent storage.

        If the category is new it is given a new unique id. Otherwise the
        information in the database is just updated.
        """
        raise NotImplementedError()

    def delete_category(self, category_or_id):
        """
        Delete the category (or the category with the given id) from the
        database.
        """
        raise NotImplementedError()

    def get_preferred_period(self):
        """Return the preferred period to display of this timeline."""
        raise NotImplementedError()

    def set_preferred_period(self, period):
        """Set the preferred period to display of this timeline."""
        raise NotImplementedError()


class TimelineIOError(Exception):
    """
    Raised from a TimelineDB if a read/write error occurs.

    The constructor and any of the public methods can raise this exception.

    Also raised by the get_timeline method if loading of a timeline failed.
    """
    pass
