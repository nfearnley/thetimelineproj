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

from timelinelib.calendar.gregorian import Gregorian
from timelinelib.calendar.monthnames import ABBREVIATED_ENGLISH_MONTH_NAMES
from timelinelib.data import Category
from timelinelib.data import Container
from timelinelib.data import Era
from timelinelib.data import Event
from timelinelib.data import Subevent
from timelinelib.data import TimePeriod
from timelinelib.time.gregoriantime import GregorianTimeType
from timelinelib.time.numtime import NumTimeType
from timelinelib.time.timeline import delta_from_days
from timelinelib.time.timeline import TimeDelta


ANY_TIME = "1 Jan 2010"
ANY_NUM_TIME = 10


def gregorian_period(start, end):
    return TimePeriod(GregorianTimeType(), human_time_to_gregorian(start), human_time_to_gregorian(end))


def numeric_period(start, end):
    return TimePeriod(NumTimeType(), start, end)


def human_time_to_gregorian(human_time):
    (year, month, day, hour, minute) = human_time_to_ymdhm(human_time)
    return Gregorian(year, month, day, hour, minute, 0).to_time()


def a_time_period():
    year = random.randint(1, 4000)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    end_year = year + random.randint(1, 5)
    end_month = random.randint(1, 12)
    end_day = random.randint(1, 28)
    return TimePeriod(GregorianTimeType(),
                      Gregorian(year, month, day, 0, 0, 0).to_time(),
                      Gregorian(end_year, end_month, end_day, 0, 0, 0).to_time())


def human_time_to_ymdhm(human_time):
    parts = human_time.split(" ")
    day_part, month_part, year_part = parts[0], parts[1], parts[2]
    day = int(day_part)
    month = ABBREVIATED_ENGLISH_MONTH_NAMES.index(month_part) + 1
    year = int(year_part)
    if len(parts) == 4:
        hour = int(parts[3][:2])
        minute = int(parts[3][3:5])
    else:
        hour = 0
        minute = 0
    return (year, month, day, hour, minute)


def an_event():
    return an_event_with(time=ANY_TIME)


def an_event_with(start=None, end=None, time=ANY_TIME, text="foo", fuzzy=False,
                  locked=False, ends_today=False, category=None):
    if start and end:
        start = human_time_to_gregorian(start)
        end = human_time_to_gregorian(end)
    else:
        start = human_time_to_gregorian(time)
        end = human_time_to_gregorian(time)
    return Event(
        GregorianTimeType(), start, end, text, category=category,
        fuzzy=fuzzy, locked=locked, ends_today=ends_today)


def a_subevent():
    return a_subevent_with()


def a_subevent_with(start=None, end=None, time=ANY_TIME, text="sub", category=None, container=None, cid=-1):
    if start and end:
        start = human_time_to_gregorian(start)
        end = human_time_to_gregorian(end)
    else:
        start = human_time_to_gregorian(time)
        end = human_time_to_gregorian(time)
    return Subevent(GregorianTimeType(), start, end, text, category=category, container=container, cid=cid)


def a_container(name, category, sub_events):
    cid = 99
    start = human_time_to_gregorian(ANY_TIME)
    end = human_time_to_gregorian(ANY_TIME)
    container = Container(GregorianTimeType(), start, end, name,
                          category=category, cid=cid)
    all_events = []
    all_events.append(container)
    for (name, category) in sub_events:
        all_events.append(Subevent(GregorianTimeType(), start, end, name,
                                   category=category, container=container))
    return all_events


def a_container_with(text="container", category=None, cid=-1):
    start = human_time_to_gregorian(ANY_TIME)
    end = human_time_to_gregorian(ANY_TIME)
    container = Container(GregorianTimeType(), start, end, text, category=category, cid=cid)
    return container


def a_category():
    return a_category_with(name="category")


def a_category_with(name, color=(255, 0, 0), font_color=(0, 255, 255),
                    parent=None):
    return Category(name=name, color=color, font_color=font_color,
                    parent=parent)


def a_gregorian_era():
    return a_gregorian_era_with()


def a_gregorian_era_with(start=None, end=None, time=ANY_TIME, name="foo", color=(128, 128, 128), time_type=GregorianTimeType()):
    if start and end:
        start = human_time_to_gregorian(start)
        end = human_time_to_gregorian(end)
    else:
        start = human_time_to_gregorian(time)
        end = human_time_to_gregorian(time)
    return Era(GregorianTimeType(), start, end, name, color)


def a_numeric_era():
    return a_numeric_era_with()


def a_numeric_era_with(start=None, end=None, time=ANY_NUM_TIME, name="foo", color=(128, 128, 128)):
    if not (start or end):
        start = time
        end = time
    return Era(NumTimeType(), start, end, name, color)


def inc(number):
    if number is None:
        return 8
    else:
        return number + 1


def new_cat(event):
    if event.get_category() is None:
        return a_category_with(name="new category")
    else:
        return a_category_with(name="was: %s" % event.get_category().get_name())


def new_parent(category):
    if category._get_parent() is None:
        return a_category_with(name="new category")
    else:
        return a_category_with(name="was: %s" % category._get_parent().get_name())


def new_time_type(event):
    if event.get_time_type() is None:
        return GregorianTimeType()
    else:
        return None


def new_progress(event):
    if event.get_progress() is None:
        return 8
    else:
        return (event.get_progress() + 1) % 100


def modifier_change_ends_today(event):
    if event.get_locked():
        event.set_locked(False)
        event.set_ends_today(not event.get_ends_today())
        event.set_locked(True)
    else:
        event.set_ends_today(not event.get_ends_today())
    return event


EVENT_MODIFIERS = [
    ("change time type", lambda event:
        event.set_time_type(new_time_type(event))),
    ("change fuzzy", lambda event:
        event.set_fuzzy(not event.get_fuzzy())),
    ("change locked", lambda event:
        event.set_locked(not event.get_locked())),
    ("change ends today", modifier_change_ends_today),
    ("change id", lambda event:
        event.set_id(inc(event.get_id()))),
    ("change time period", lambda event:
        event.set_time_period(event.get_time_period().move_delta(delta_from_days(1)))),
    ("change text", lambda event:
        event.set_text("was: %s" % event.get_text())),
    ("change category", lambda event:
        event.set_category(new_cat(event))),
    ("change icon", lambda event:
        event.set_icon("was: %s" % event.get_icon())),
    ("change description", lambda event:
        event.set_description("was: %s" % event.get_description())),
    ("change hyperlink", lambda event:
        event.set_hyperlink("was: %s" % event.get_hyperlink())),
    ("change progress", lambda event:
        event.set_progress(new_progress(event))),
    ("change alert", lambda event:
        event.set_alert("was: %s" % event.get_alert())),
]


SUBEVENT_MODIFIERS = [
    ("change container id", lambda event:
        event.set_container_id(event.get_container_id() + 1)),
] + EVENT_MODIFIERS


CONTAINER_MODIFIERS = [
    ("change container id", lambda event:
        event.set_cid(event.cid() + 1)),
] + EVENT_MODIFIERS


CATEGORY_MODIFIERS = [
    ("change name", lambda category:
        category.set_name("was: %s" % category.get_name())),
    ("change id", lambda category:
        category.set_id(inc(category.get_id()))),
    ("change color", lambda category:
        category.set_color(category.get_color() + (1, 0, 3))),
    ("change font color", lambda category:
        category.set_font_color(category.get_font_color() + (1, 0, 3))),
    ("change parent", lambda category:
        category.set_parent(new_parent(category))),
]


TIME_PERIOD_MODIFIERS = [
    ("zoom", lambda time_period:
        time_period.zoom(-1)),
    ("extend left", lambda time_period:
        time_period.update(time_period.start_time - time_period.time_type.get_min_zoom_delta()[0],
                           time_period.end_time)),
    ("extend right", lambda time_period:
        time_period.update(time_period.start_time,
                           time_period.end_time + time_period.time_type.get_min_zoom_delta()[0])),
]


ERA_MODIFIERS = [
    ("change time type", lambda era: era.set_time_type(new_time_type(era))),
    ("change id", lambda era: era.set_id(inc(era.get_id()))),
    ("change time period", lambda era: era.set_time_period(era.get_time_period().move_delta(delta_from_days(1)))),
    ("change text", lambda era: era.set_name("was: %s" % era.get_name())),
    ("change color", lambda era: era.set_color(tuple([x + 1 for x in era.get_color()])))
]

NUM_ERA_MODIFIERS = [
    ("change time type", lambda era: era.set_time_type(new_time_type(era))),
    ("change id", lambda era: era.set_id(inc(era.get_id()))),
    ("change time period", lambda era: era.set_time_period(era.get_time_period().move_delta(1))),
    ("change text", lambda era: era.set_name("was: %s" % era.get_name())),
    ("change color", lambda era: era.set_color(tuple([x + 1 for x in era.get_color()])))
]


TIME_MODIFIERS = [
    ("add", lambda time: time + TimeDelta(1)),
]


class ObjectWithTruthValue(object):

    def __init__(self, truth_value):
        self.truth_value = truth_value

    def __nonzero__(self):
        return self.truth_value


def select_language(language):
    import platform
    from timelinelib.config.paths import LOCALE_DIR
    from timelinelib.meta.about import APPLICATION_NAME
    if platform.system() == "Windows":
        import gettext
        import os
        os.environ['LANG'] = language
        gettext.install(APPLICATION_NAME.lower(), LOCALE_DIR, unicode=True)
