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


import timelinelib.time.timeline as timeline


class Bosparanian(object):

    def __init__(self, year, month, day, hour, minute, second):
        if not is_valid(year, month, day):
            raise ValueError("Invalid bosparanian date %s-%s-%s" % (year, month, day))
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second

    def replace(self, year=None, month=None):
        if year is None:
            year = self.year
        if month is None:
            month = self.month
        return Bosparanian(year, month, self.day,
                         self.hour, self.minute, self.second)

    def days_in_month(self):
        return days_in_month(self.month)

    def to_tuple(self):
        return (self.year, self.month, self.day, self.hour, self.minute,
                self.second)

    def to_date_tuple(self):
        return (self.year, self.month, self.day)

    def to_time_tuple(self):
        return (self.hour, self.minute, self.second)

    def to_time(self):
        days = to_bosparanian_day(self.year, self.month, self.day)
        seconds = self.hour * 60 * 60 + self.minute * 60 + self.second
        return timeline.Time(days, seconds)

    def is_praios_first(self):
        return (self.month == 1 and
                self.day == 1 and
                self.hour == 0 and
                self.minute == 0 and
                self.second == 0)

    def is_first_of_month(self):
        return (self.day == 1 and
                self.hour == 0 and
                self.minute == 0 and
                self.second == 0)

    def __eq__(self, other):
        return (isinstance(other, Bosparanian) and
                self.to_tuple() == other.to_tuple())

    def __repr__(self):
        return "Bosparanian<%d-%02d-%02d %02d:%02d:%02d>" % self.to_tuple()


def is_valid(year, month, day):
    return (month >= 1 and month <= 13 and day >= 1 and day <= days_in_month(month))


def is_valid_time(hour, minute, second):
    return (hour >= 0 and hour < 24 and minute >= 0 and minute < 60 and second >= 0 and second < 60)


def days_in_month(month):
    if month in [13]:
        return 5
    return 30

def from_bosparanian_day(bosparanian_day):
    """
    Converts a day number, counted from 1st PRA, 0 BF to standard bosparanian calendar date
    """
    bosp_day=bosparanian_day-(365*100*73)+3 # shift by 73 centuries and align week
    year = bosp_day // 365
    d = bosp_day - (year * 365)
    if d >= 360:
        month = 13
        day = d-359
        return (year,month,day)
    month = d // 30 + 1
    day = d % 30 + 1
    return (year,month,day)


def to_bosparanian_day(year, month, day):
    """
    Converts a bosparanian date given as year, month, and day, to a day number counted from 1st PRA 0 BF
    """
    bosp_day = year * 365
    bosp_day += ((month - 1) // 13) * 365
    m = (month - 1) % 13 
    bosp_day += m * 30
    bosp_day += day - 1
    bosparanian_day=bosp_day+(365*100*73)-3 # shift by 73 centuries and align week
    return bosparanian_day


def bosparanian_week(time):
    """
    returns number of week in year
    """
    def windsday_week_1(year):
        pra_4 = from_date(year, 1, 4).to_time()
        return pra_4 - timeline.delta_from_days(pra_4.get_day_of_week())
    def days_between(end, start):
        return end.julian_day - start.julian_day
    def days_since_windsday_week_1(time):
        year = from_time(time).year
        diff = days_between(end=time, start=windsday_week_1(year + 1))
        if diff >= 0:
            return diff
        diff = days_between(end=time, start=windsday_week_1(year))
        if diff >= 0:
            return diff
        diff = days_between(end=time, start=windsday_week_1(year - 1))
        if diff >= 0:
            return diff
        raise ValueError("should not end up here")
    return days_since_windsday_week_1(time) / 7 + 1


def from_time(time):
    (year, month, day) = from_bosparanian_day(time.julian_day)
    (hour, minute, second) = time.get_time_of_day()
    return Bosparanian(year, month, day, hour, minute, second)


def from_date(year, month, day):
    return Bosparanian(year, month, day, 0, 0, 0)
