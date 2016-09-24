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


from timelinelib.time.timeline import TimeDelta


class TimePeriod(object):
    """
    Represents a period in time using a start and end time.

    This is used both to store the time period for an event and for storing the
    currently displayed time period in the GUI.
    """

    def __init__(self, start_time, end_time):
        self.start_time, self.end_time = self._update(start_time, end_time)

    def clone(self):
        return TimePeriod(self.start_time, self.end_time)

    def __eq__(self, other):
        return (isinstance(other, TimePeriod) and
                self.start_time == other.start_time and
                self.end_time == other.end_time)

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return "TimePeriod<%s, %s>" % (self.start_time, self.end_time)

    def get_start_time(self):
        return self.start_time

    def get_end_time(self):
        return self.end_time

    def set_start_time(self, time):
        return self.update(time, self.end_time)

    def set_end_time(self, time):
        return self.update(self.start_time, time)

    def start_to_start(self, time_period):
        return TimePeriod(self.start_time, time_period.get_start_time())

    def start_to_end(self, time_period):
        return TimePeriod(self.start_time, time_period.get_end_time())

    def end_to_start(self, time_period):
        return TimePeriod(self.end_time, time_period.get_start_time())

    def end_to_end(self, time_period):
        return TimePeriod(self.end_time, time_period.get_end_time())

    def update(self, start_time, end_time,
               start_delta=None, end_delta=None):
        new_start, new_end = self._update(start_time, end_time, start_delta, end_delta)
        return TimePeriod(new_start, new_end)

    def _update(self, start_time, end_time, start_delta=None, end_delta=None):
        """
        Change the time period data.

        Optionally add the deltas to the times like this: time + delta.

        If data is invalid, it will not be set, and a ValueError will be raised
        instead. Data is invalid if or if the start time is larger than the end
        time.
        """
        new_start = self._calc_new_time(start_time, start_delta)
        new_end = self._calc_new_time(end_time, end_delta)
        self._assert_period_is_valid(new_start, new_end)
        return (new_start, new_end)

    def _assert_period_is_valid(self, new_start, new_end):
        self._assert_start_gt_end(new_start, new_end)

    def _assert_start_gt_end(self, new_start, new_end):
        if new_start > new_end:
            raise ValueError(_("Start time can't be after end time"))

    def inside(self, time):
        """
        Return True if the given time is inside this period or on the border,
        otherwise False.
        """
        return time >= self.start_time and time <= self.end_time

    def distance_to(self, time_period):
        if time_period.starts_after(self.end_time):
            return self.end_to_start(time_period).delta()
        elif time_period.ends_before(self.start_time):
            return time_period.end_to_start(self).delta()
        else:
            return TimeDelta(0)

    def inside_period(self, time_period):
        return not (time_period.ends_before(self.start_time) or
                    time_period.starts_after(self.end_time))

    def starts_after(self, time):
        return self.start_time > time

    def ends_before(self, time):
        return self.end_time < time

    def ends_at(self, time):
        return self.end_time == time

    def is_period(self):
        """
        Return True if this time period is longer than just a point in time,
        otherwise False.
        """
        return self.start_time != self.end_time

    def mean_time(self):
        """
        Return the time in the middle if this time period is longer than just a
        point in time, otherwise the point in time for this time period.
        """
        return self.start_time + (self.delta() / 2)

    def zoom(self, times, ratio=0.5):
        start_delta = self.delta() * (times * ratio / 5.0)
        end_delta = self.delta() * (-times * (1.0 - ratio) / 5.0)
        return self.update(self.start_time, self.end_time, start_delta, end_delta)

    def move(self, direction):
        """
        Move this time period one 10th to the given direction.

        Direction should be -1 for moving to the left or 1 for moving to the
        right.
        """
        delta = self.delta() * (direction / 10.0)
        return self.move_delta(delta)

    def move_delta(self, delta):
        return self.update(self.start_time, self.end_time, delta, delta)

    def delta(self):
        """Return the length of this time period as a timedelta object."""
        return self.end_time - self.start_time

    def center(self, time):
        return self.move_delta(time - self.mean_time())

    def _calc_new_time(self, time, delta):
        if delta is None:
            return time
        return time + delta


class TimeOutOfRangeLeftError(ValueError):
    pass


class TimeOutOfRangeRightError(ValueError):
    pass


def time_period_center(time, length):
    """
    TimePeriod factory method.

    Return a time period with the given length (represented as a timedelta)
    centered around `time`.
    """
    half_length = length * 0.5
    start_time = time - half_length
    end_time = time + half_length
    return TimePeriod(start_time, end_time)
