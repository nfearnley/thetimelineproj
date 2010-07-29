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


"""
Utilities used by drawers.
"""


from datetime import timedelta

import wx


# To save computation power (used by `delta_to_microseconds`)
US_PER_SEC = 1000000
US_PER_DAY = 24 * 60 * 60 * US_PER_SEC


class Metrics(object):
    """
    Convert between pixel coordinates and time coordinates.
    """

    def __init__(self, size, time_period, divider_line_slider):
        self.width, self.height = size
        self.half_width = self.width / 2
        self.half_height = self.height / 2
        self.half_height = int(round(divider_line_slider * self.height))
        self.time_period = time_period

    def calc_exact_x(self, time):
        """Return the x position in pixels as a float for the given time."""
        delta1 = div_timedeltas(time - self.time_period.start_time,
                                self.time_period.delta())
        float_res = self.width * delta1
        return float_res

    def calc_x(self, time):
        """Return the x position in pixels as an integer for the given time."""
        return int(round(self.calc_exact_x(time)))

    def calc_exact_width(self, time_period):
        """Return the with in pixels as a float for the given time_period."""
        return (self.calc_exact_x(time_period.end_time) -
                self.calc_exact_x(time_period.start_time))

    def calc_width(self, time_period):
        """Return the with in pixels as an integer for the given time_period."""
        return (self.calc_x(time_period.end_time) -
                self.calc_x(time_period.start_time)) + 1

    def get_time(self, x):
        """Return the time at pixel `x`."""
        microsecs = delta_to_microseconds(self.time_period.delta())
        microsecs = microsecs * float(x) / self.width
        return self.time_period.start_time + microseconds_to_delta(microsecs)

    def get_difftime(self, x1, x2):
        """Return the time length between two x positions."""
        return self.get_time(x1) - self.get_time(x2)
    

def get_default_font(size, bold=False):
    if bold:
        weight = wx.FONTWEIGHT_BOLD
    else:
        weight = wx.FONTWEIGHT_NORMAL
    return wx.Font(size, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, weight)


def darken_color(color, factor=0.7):
    r, g, b = color
    new_r = int(r * factor)
    new_g = int(g * factor)
    new_b = int(b * factor)
    return (new_r, new_g, new_b)


def delta_to_microseconds(delta):
    """Return the number of microseconds that the timedelta represents."""
    return (delta.days * US_PER_DAY +
            delta.seconds * US_PER_SEC +
            delta.microseconds)


def microseconds_to_delta(microsecs):
    """Return a timedelta representing the given number of microseconds."""
    return timedelta(microseconds=microsecs)


def mult_timedelta(delta, num):
    """Return a new timedelta that is `num` times larger than `delta`."""
    days = delta.days * num
    seconds = delta.seconds * num
    microseconds = delta.microseconds * num
    return timedelta(days, seconds, microseconds)


def div_timedeltas(delta1, delta2):
    """Return how many times delta2 fit in delta1."""
    # Since Python can handle infinitely large numbers, this solution works. It
    # might however not be optimal. If you are clever, you should be able to
    # treat the different parts individually. But this is simple.
    total_us1 = delta_to_microseconds(delta1)
    total_us2 = delta_to_microseconds(delta2)
    # Make sure that the result is a floating point number
    return total_us1 / float(total_us2)
