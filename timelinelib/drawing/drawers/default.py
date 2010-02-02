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
Implements a Drawer that draws the default timeline view.
"""


import math
import calendar
from datetime import timedelta
from datetime import datetime
import os.path

import wx

from timelinelib.drawing.interface import Drawer
from timelinelib.drawing.utils import Metrics
from timelinelib.drawing.utils import get_default_font
from timelinelib.drawing.utils import darken_color
from timelinelib.gui.utils import sort_categories
from timelinelib.db.objects import TimePeriod
from timelinelib.db.utils import local_to_unicode
from timelinelib.paths import ICONS_DIR
import timelinelib.config as config


OUTER_PADDING = 5      # Space between event boxes (pixels)
INNER_PADDING = 3      # Space inside event box to text (pixels)
BASELINE_PADDING = 15  # Extra space to move events away from baseline (pixels)
PERIOD_THRESHOLD = 20  # Periods smaller than this are drawn as events (pixels)
BALLOON_RADIUS = 12
DATA_INDICATOR_SIZE = 10


class Strip(object):
    """
    An interface for strips.

    The different strips are implemented in subclasses below.

    The timeline is divided in major and minor strips. The minor strip might
    for example be days, and the major strip months. Major strips are divided
    with a solid line and minor strips with dotted lines. Typically maximum
    three major strips should be shown and the rest will be minor strips.
    """

    def label(self, time, major=False):
        """
        Return the label for this strip at the given time when used as major or
        minor strip.
        """

    def start(self, time):
        """
        Return the start time for this strip and the given time.

        For example, if the time is 2008-08-31 and the strip is month, the
        start would be 2008-08-01.
        """

    def increment(self, time):
        """
        Increment the given time so that it points to the start of the next
        strip.
        """


class StripDecade(Strip):

    def label(self, time, major=False):
        if major:
            # TODO: This only works for English. Possible to localize?
            return str(self._decade_start_year(time.year)) + "s"
        return ""

    def start(self, time):
        return datetime(self._decade_start_year(time.year), 1, 1)

    def increment(self, time):
        return time.replace(year=time.year+10)

    def _decade_start_year(self, year):
        return (int(year) / 10) * 10


class StripYear(Strip):

    def label(self, time, major=False):
        return str(time.year)

    def start(self, time):
        return datetime(time.year, 1, 1)

    def increment(self, time):
        return time.replace(year=time.year+1)


class StripMonth(Strip):

    def label(self, time, major=False):
        if major:
            return "%s %s" % (local_to_unicode(calendar.month_abbr[time.month]),                              time.year)
        return calendar.month_abbr[time.month]

    def start(self, time):
        return datetime(time.year, time.month, 1)

    def increment(self, time):
        return time + timedelta(calendar.monthrange(time.year, time.month)[1])


class StripWeek(Strip):

    def label(self, time, major=False):
        if major:
            # Example: Week 23 (1-7 Jan 2009)
            first_weekday = self.start(time)
            next_first_weekday = self.increment(first_weekday)
            last_weekday = next_first_weekday - timedelta(days=1)
            range_string = self._time_range_string(first_weekday, last_weekday)
            if config.global_config.week_start == "monday":
                return (_("Week") + " %s (%s)") % (time.isocalendar()[1], range_string)
            else:
                # It is sunday (don't know what to do about week numbers here)
                return range_string
        # This strip should never be used as minor
        return ""

    def start(self, time):
        stripped_date = datetime(time.year, time.month, time.day)
        if config.global_config.week_start == "monday":
            days_to_subtract = stripped_date.weekday()
        else:
            # It is sunday
            days_to_subtract = (stripped_date.weekday() + 1) % 7
        return stripped_date - timedelta(days=days_to_subtract)

    def increment(self, time):
        return time + timedelta(7)

    def _time_range_string(self, time1, time2):
        """
        Examples:

        * 1-7 Jun 2009
        * 28 Jun-3 Jul 2009
        * 28 Jun 08-3 Jul 2009
        """
        if time1.year == time2.year:
            if time1.month == time2.month:
                return "%s-%s %s %s" % (time1.day, time2.day,
                                        local_to_unicode(calendar.month_abbr[time1.month]),
                                        time1.year)
            return "%s %s-%s %s %s" % (time1.day,
                                       local_to_unicode(calendar.month_abbr[time1.month]),
                                       time2.day,
                                       local_to_unicode(calendar.month_abbr[time2.month]),
                                       time1.year)
        return "%s %s %s-%s %s %s" % (time1.day,
                                      local_to_unicode(calendar.month_abbr[time1.month]),
                                      time1.year,
                                      time2.day,
                                      local_to_unicode(calendar.month_abbr[time2.month]),
                                      time2.year)


class StripDay(Strip):

    def label(self, time, major=False):
        if major:
            return "%s %s %s" % (time.day, local_to_unicode(calendar.month_abbr[time.month]),
                                 time.year)
        return str(time.day)

    def start(self, time):
        return datetime(time.year, time.month, time.day)

    def increment(self, time):
        return time + timedelta(1)


class StripWeekday(Strip):

    def label(self, time, major=False):
        if major:
            return "%s %s %s %s" % (local_to_unicode(calendar.day_abbr[time.weekday()]),
                                    time.day,
                                    local_to_unicode(calendar.month_abbr[time.month]),
                                    time.year)
        return str(calendar.day_abbr[time.weekday()])

    def start(self, time):
        return datetime(time.year, time.month, time.day)

    def increment(self, time):
        return time + timedelta(1)


class StripHour(Strip):

    def label(self, time, major=False):
        if major:
            return "%s %s %s %s" % (time.day, local_to_unicode(calendar.month_abbr[time.month]),
                                    time.year, time.hour)
        return str(time.hour)

    def start(self, time):
        return datetime(time.year, time.month, time.day, time.hour)

    def increment(self, time):
        return time + timedelta(hours=1)


class DefaultDrawingAlgorithm(Drawer):

    def __init__(self):
        # Fonts and pens we use when drawing
        self.header_font = get_default_font(12, True)
        self.small_text_font = get_default_font(8)
        self.small_text_font_bold = get_default_font(8, True)
        self.red_solid_pen = wx.Pen(wx.Color(255,0, 0), 1, wx.SOLID)
        self.black_solid_pen = wx.Pen(wx.Color(0, 0, 0), 1, wx.SOLID)
        self.darkred_solid_pen = wx.Pen(wx.Color(200, 0, 0), 1, wx.SOLID)
        self.black_dashed_pen = wx.Pen(wx.Color(200, 200, 200), 1, wx.USER_DASH)
        self.black_dashed_pen.SetDashes([2, 2])
        self.black_dashed_pen.SetCap(wx.CAP_BUTT)
        self.grey_solid_pen = wx.Pen(wx.Color(200, 200, 200), 1, wx.SOLID)
        self.white_solid_brush = wx.Brush(wx.Color(255, 255, 255), wx.SOLID)
        self.black_solid_brush = wx.Brush(wx.Color(0, 0, 0), wx.SOLID)
        self.lightgrey_solid_brush = wx.Brush(wx.Color(230, 230, 230), wx.SOLID)
        self.DATA_ICON_WIDTH = 5

    def event_is_period(self, time_period):
        ew = self.metrics.calc_width(time_period)
        return ew > PERIOD_THRESHOLD

    def draw(self, dc, timeline, view_properties):
        """
        Implement the drawing interface.

        The drawing is done in a number of steps: First positions of all events
        and strips are calculated and then they are drawn. Positions can also
        be used later to answer questions like what event is at position (x, y).
        """
        def include_event(event):
            if (event.category is not None and not
                view_properties.category_visible(event.category)):
                return False
            return True
        # Store data so we can use it in other functions
        self.dc = dc
        self.time_period = view_properties.displayed_period
        self.metrics = Metrics(dc, self.time_period, view_properties.divider_position)
        # Data
        self.event_data = []       # List of tuples (event, rect)
        self.major_strip_data = [] # List of time_period
        self.minor_strip_data = [] # List of time_period
        self.balloon_data = []     # List of (event, rect)
        # Calculate stuff later used for drawing
        events = [event for event in timeline.get_events(self.time_period)
                  if include_event(event)]
        self._calc_rects(events)
        self._calc_strips()
        # Perform the actual drawing
        if view_properties.period_selection:
            self._draw_period_selection(view_properties.period_selection)
        self._draw_bg()
        self._draw_events(view_properties)
        if view_properties.show_legend:
            self._draw_legend(self._extract_categories())
        self._draw_ballons(view_properties)
        # Make sure to delete this one
        del self.dc

    def snap(self, time, snap_region=10):
        major_strip, minor_strip = self._choose_strip()
        time_x = self.metrics.calc_exact_x(time)
        left_strip_time = minor_strip.start(time)
        right_strip_time = minor_strip.increment(left_strip_time)
        left_diff = abs(time_x - self.metrics.calc_exact_x(left_strip_time))
        right_diff = abs(time_x - self.metrics.calc_exact_x(right_strip_time))
        if left_diff < snap_region:
            return left_strip_time
        elif right_diff < snap_region:
            return right_strip_time
        else:
            return time

    def snap_selection(self, period_selection):
        start, end = period_selection
        return (self.snap(start), self.snap(end))

    def event_at(self, x, y):
        for (event, rect) in self.event_data:
            if rect.Contains(wx.Point(x, y)):
                return event
        return None

    def event_with_rect_at(self, x, y):
        for (event, rect) in self.event_data:
            if rect.Contains(wx.Point(x, y)):
                return (event, rect)
        return None

    def event_rect(self, evt):
        for (event, rect) in self.event_data:
            if evt == event:
                return rect
        return None

    def balloon_at(self, x, y):
        event = None
        for (event_in_list, rect) in self.balloon_data:
            if rect.Contains(wx.Point(x, y)): 
                event = event_in_list
        return event

    def _calc_rects(self, events):
        """
        Calculate rectangles for all events.

        The rectangles define the areas in which the events can draw
        themselves.

        During the calculations, the outer padding is part of the rectangles to
        make the calculations easier. Outer padding is removed in the end.
        """
        self.dc.SetFont(self.small_text_font)
        for event in events:
            tw, th = self.dc.GetTextExtent(event.text)
            ew = self.metrics.calc_width(event.time_period)
            if ew > PERIOD_THRESHOLD:
                # Treat as period (periods are placed below the baseline, with
                # indicates length of period)
                rw = ew + 2 * OUTER_PADDING
                rh = th + 2 * INNER_PADDING + 2 * OUTER_PADDING
                rx = (self.metrics.calc_x(event.time_period.start_time) -
                      OUTER_PADDING)
                ry = self.metrics.half_height + BASELINE_PADDING
                movedir = 1
            else:
                # Treat as event (events are placed above the baseline, with
                # indicates length of text)
                rw = tw + 2 * INNER_PADDING + 2 * OUTER_PADDING
                rh = th + 2 * INNER_PADDING + 2 * OUTER_PADDING
                if event.has_data():
                    rw += DATA_INDICATOR_SIZE / 3
                rx = self.metrics.calc_x(event.mean_time()) - rw / 2
                ry = self.metrics.half_height - rh - BASELINE_PADDING
                movedir = -1
            rect = wx.Rect(rx, ry, rw, rh)
            self._prevent_overlap(rect, movedir)
            self.event_data.append((event, rect))
        for (event, rect) in self.event_data:
            # Remove outer padding
            rect.Deflate(OUTER_PADDING, OUTER_PADDING)
            # Make sure rectangle is not far outside the screen. MARGIN must be
            # big enough to hide borders end selection markers.
            MARGIN = 10
            if rect.X < -MARGIN:
                move = -rect.X - MARGIN
                rect.X += move
                rect.Width -= move
            right_edge_x = rect.X + rect.Width
            if right_edge_x > self.metrics.width + MARGIN:
                rect.Width -= right_edge_x - self.metrics.width - MARGIN

    def _prevent_overlap(self, rect, movedir):
        """
        Prevent rect from overlapping with any rectangle by moving it.
        """
        while True:
            h = self._intersection_height(rect)
            if h > 0:
                rect.Y += movedir * h
            else:
                break
            # Don't prevent overlap if rect is outside screen
            if movedir == 1 and rect.Y > self.metrics.height:
                break
            if movedir == -1 and (rect.Y + rect.Height) < 0:
                break

    def _intersection_height(self, rect):
        """
        Calculate height of first intersection with rectangle.
        """
        for (event, r) in self.event_data:
            if rect.Intersects(r):
                # Calculate height of intersection only if there is any
                r_copy = wx.Rect(*r) # Because `Intersect` modifies rect
                intersection = r_copy.Intersect(rect)
                return intersection.Height
        return 0

    def _calc_strips(self):
        """Fill the two arrays `minor_strip_data` and `major_strip_data`."""
        def fill(list, strip):
            """Fill the given list with the given strip."""
            current_start = strip.start(self.time_period.start_time)
            while current_start < self.time_period.end_time:
                next_start = strip.increment(current_start)
                list.append(TimePeriod(current_start, next_start))
                current_start = next_start
        major_strip, minor_strip = self._choose_strip()
        fill(self.major_strip_data, major_strip)
        fill(self.minor_strip_data, minor_strip)

    def _choose_strip(self):
        """
        Return a tuple (major_strip, minor_strip) for current time period and
        window size.
        """
        today = datetime.now()
        tomorrow = today + timedelta(days=1)
        day_period = TimePeriod(today, tomorrow)
        one_day_width = self.metrics.calc_exact_width(day_period)
        if one_day_width > 600:
            return (StripDay(), StripHour())
        elif one_day_width > 45:
            return (StripWeek(), StripWeekday())
        elif one_day_width > 25:
            return (StripMonth(), StripDay())
        elif one_day_width > 1.5:
            return (StripYear(), StripMonth())
        elif one_day_width > 0.12:
            return (StripDecade(), StripYear())
        else:
            return (StripDecade(), StripDecade())

    def _draw_period_selection(self, period_selection):
        start, end = period_selection
        start_x = self.metrics.calc_x(start)
        end_x = self.metrics.calc_x(end)
        self.dc.SetBrush(self.lightgrey_solid_brush)
        self.dc.SetPen(wx.TRANSPARENT_PEN)
        self.dc.DrawRectangle(start_x, 0,
                              end_x - start_x + 1, self.metrics.height)

    def _draw_bg(self):
        """
        Draw major and minor strips, lines to all event boxes and baseline.

        Both major and minor strips have divider lines and labels.
        """
        major_strip, minor_strip = self._choose_strip()
        # Minor strips
        self.dc.SetPen(self.black_dashed_pen)
        for tp in self.minor_strip_data:
            # Chose font
            if (isinstance(minor_strip, StripDay) and
                tp.start_time.weekday() in (5, 6)):
                self.dc.SetFont(self.small_text_font_bold)
            else:
                self.dc.SetFont(self.small_text_font)
            # Divider line
            x = self.metrics.calc_x(tp.end_time)
            self.dc.DrawLine(x, 0, x, self.metrics.height)
            # Label
            label = minor_strip.label(tp.start_time)
            (tw, th) = self.dc.GetTextExtent(label)
            middle = self.metrics.calc_x(tp.mean_time())
            middley = self.metrics.half_height
            self.dc.DrawText(label, middle - tw / 2, middley - th)
        # Major strips
        self.dc.SetFont(self.header_font)
        self.dc.SetPen(self.grey_solid_pen)
        for tp in self.major_strip_data:
            # Divider line
            x = self.metrics.calc_x(tp.end_time)
            self.dc.DrawLine(x, 0, x, self.metrics.height)
            # Label
            label = major_strip.label(tp.start_time, True)
            (tw, th) = self.dc.GetTextExtent(label)
            x = self.metrics.calc_x(tp.mean_time()) - tw / 2
            # If the label is not visible when it is positioned in the middle
            # of the period, we move it so that as much of it as possible is
            # visible without crossing strip borders.
            if x - INNER_PADDING < 0:
                x = INNER_PADDING
                right = self.metrics.calc_x(tp.end_time)
                if x + tw + INNER_PADDING > right:
                    x = right - tw - INNER_PADDING
            elif x + tw + INNER_PADDING > self.metrics.width:
                x = self.metrics.width - tw - INNER_PADDING
                left = self.metrics.calc_x(tp.start_time)
                if x < left:
                    x = left + INNER_PADDING
            self.dc.DrawText(label, x, INNER_PADDING)
        # Main divider line
        self.dc.SetPen(self.black_solid_pen)
        self.dc.DrawLine(0, self.metrics.half_height, self.metrics.width,
                         self.metrics.half_height)
        # Lines to all events
        self.dc.SetBrush(self.black_solid_brush)
        for (event, rect) in self.event_data:
            if rect.Y < self.metrics.half_height:
                x = self.metrics.calc_x(event.mean_time())
                y = rect.Y + rect.Height / 2
                self.dc.DrawLine(x, y, x, self.metrics.half_height)
                self.dc.DrawCircle(x, self.metrics.half_height, 2)
        # Now line
        now_time = datetime.now()
        if self.time_period.inside(now_time):
            self.dc.SetPen(self.darkred_solid_pen)
            x = self.metrics.calc_x(now_time)
            self.dc.DrawLine(x, 0, x, self.metrics.height)

    def _extract_categories(self):
        categories = []
        for (event, rect) in self.event_data:
            cat = event.category
            if cat and not cat in categories:
                categories.append(cat)
        return sort_categories(categories)

    def _draw_legend(self, categories):
        """
        Draw legend for the given categories.

        Box in lower left corner:

          +----------+
          | Name   O |
          | Name   O |
          +----------+
        """
        num_categories = len(categories)
        if num_categories == 0:
            return
        def calc_sizes(dc):
            """Return (width, height, item_height)."""
            width = 0
            height = INNER_PADDING
            item_heights = 0
            for cat in categories:
                tw, th = self.dc.GetTextExtent(cat.name)
                height = height + th + INNER_PADDING
                item_heights += th
                if tw > width:
                    width = tw
            item_height = item_heights / num_categories
            return (width + 4 * INNER_PADDING + item_height, height,
                    item_height)
        self.dc.SetFont(self.small_text_font)
        self.dc.SetTextForeground((0, 0, 0))
        width, height, item_height = calc_sizes(self.dc)
        # Draw big box
        self.dc.SetBrush(self.white_solid_brush)
        self.dc.SetPen(self.black_solid_pen)
        box_rect = (OUTER_PADDING,
                    self.metrics.height - height - OUTER_PADDING,
                    width, height)
        self.dc.DrawRectangleRect(box_rect)
        # Draw text and color boxes
        cur_y = self.metrics.height - height - OUTER_PADDING + INNER_PADDING
        for cat in categories:
            base_color = cat.color
            border_color = darken_color(base_color)
            self.dc.SetBrush(wx.Brush(base_color, wx.SOLID))
            self.dc.SetPen(wx.Pen(border_color, 1, wx.SOLID))
            color_box_rect = (OUTER_PADDING + width - item_height -
                              INNER_PADDING,
                              cur_y, item_height, item_height)
            self.dc.DrawRectangleRect(color_box_rect)
            self.dc.DrawText(cat.name, OUTER_PADDING + INNER_PADDING, cur_y)
            cur_y = cur_y + item_height + INNER_PADDING

    def _draw_events(self, view_properties):
        """Draw all event boxes and the text inside them."""
        self.dc.SetFont(self.small_text_font)
        self.dc.SetTextForeground((0, 0, 0))
        for (event, rect) in self.event_data:
            # Ensure that we can't draw outside rectangle
            self.dc.DestroyClippingRegion()
            self.dc.SetClippingRect(rect)
            # Draw the box
            self.dc.SetBrush(self._get_box_brush(event))
            self.dc.SetPen(self._get_box_pen(event))
            self.dc.DrawRectangleRect(rect)
            # Ensure that we can't draw content outside inner rectangle
            self.dc.DestroyClippingRegion()
            rect_copy = wx.Rect(*rect)
            rect_copy.Deflate(INNER_PADDING, INNER_PADDING)
            self.dc.SetClippingRect(rect_copy)
            if rect_copy.Width > 0:
                # Draw the text (if there is room for it)
                text_x = rect.X + INNER_PADDING
                text_y = rect.Y + INNER_PADDING
                if text_x < INNER_PADDING:
                    text_x = INNER_PADDING
                self.dc.DrawText(event.text, text_x, text_y)
            # Draw data contents indicator
            self.dc.DestroyClippingRegion()
            self.dc.SetClippingRect(rect)
            if event.has_data():
                self._draw_contents_indicator(event, rect)
            # Draw selection and handles
            if view_properties.is_selected(event):
                small_rect = wx.Rect(*rect)
                small_rect.Deflate(1, 1)
                border_color = self._get_border_color(event)
                border_color = darken_color(border_color)
                pen = wx.Pen(border_color, 1, wx.SOLID)
                self.dc.SetBrush(wx.TRANSPARENT_BRUSH)
                self.dc.SetPen(pen)
                self.dc.DrawRectangleRect(small_rect)
                self._draw_handles(rect)
        # Reset this when we are done
        self.dc.DestroyClippingRegion()

    def _draw_handles(self, rect):
        SIZE = 4
        big_rect = wx.Rect(rect.X - SIZE, rect.Y - SIZE, rect.Width + 2 * SIZE, rect.Height + 2 * SIZE)
        self.dc.DestroyClippingRegion()
        self.dc.SetClippingRect(big_rect)
        y = rect.Y + rect.Height/2 - SIZE/2
        x = rect.X - SIZE / 2
        west_rect   = wx.Rect(x + 1             , y, SIZE, SIZE)
        center_rect = wx.Rect(x + rect.Width / 2, y, SIZE, SIZE)
        east_rect   = wx.Rect(x + rect.Width - 1, y, SIZE, SIZE)
        self.dc.SetBrush(wx.Brush("BLACK", wx.SOLID))
        self.dc.SetPen(wx.Pen("BLACK", 1, wx.SOLID))
        self.dc.DrawRectangleRect(east_rect)
        self.dc.DrawRectangleRect(west_rect)
        self.dc.DrawRectangleRect(center_rect)
        
    def _draw_contents_indicator(self, event, rect):
        """
        The data contents indicator is a small triangle drawn in the upper
        right corner of the event rectangle.
        """
        corner_x = rect.X + rect.Width
        if corner_x > self.metrics.width:
            corner_x = self.metrics.width
        points = (
            wx.Point(corner_x - DATA_INDICATOR_SIZE, rect.Y),
            wx.Point(corner_x, rect.Y),
            wx.Point(corner_x, rect.Y + DATA_INDICATOR_SIZE),
        )
        self.dc.SetBrush(self._get_box_indicator_brush(event))
        self.dc.SetPen(wx.TRANSPARENT_PEN)
        self.dc.DrawPolygon(points)

    def _get_base_color(self, event):
        if event.category:
            base_color = event.category.color
        else:
            base_color = (200, 200, 200)
        return base_color

    def _get_border_color(self, event):
        base_color = self._get_base_color(event)
        border_color = darken_color(base_color)
        return border_color

    def _get_box_pen(self, event):
        border_color = self._get_border_color(event)
        pen = wx.Pen(border_color, 1, wx.SOLID)
        return pen

    def _get_box_brush(self, event):
        base_color = self._get_base_color(event)
        brush = wx.Brush(base_color, wx.SOLID)
        return brush

    def _get_box_indicator_brush(self, event):
        base_color = self._get_base_color(event)
        darker_color = darken_color(base_color, 0.6)
        brush = wx.Brush(darker_color, wx.SOLID)
        return brush

    def _get_selected_box_brush(self, event):
        border_color = self._get_border_color(event)
        brush = wx.Brush(border_color, wx.BDIAGONAL_HATCH)
        return brush

    def _draw_ballons(self, view_properties):
        """Draw ballons on selected events that has 'description' data."""
        top_event = None
        top_rect = None
        for (event, rect) in self.event_data:
            if (event.get_data("description") != None or
                event.get_data("icon") != None):
                sticky = view_properties.event_has_sticky_balloon(event) 
                if (view_properties.event_is_hovered(event) or sticky):
                    if not sticky:
                        top_event, top_rect = event, rect
                    self._draw_ballon(event, rect, sticky)
        # Make the unsticky balloon appear on top            
        if top_event is not None:
            self._draw_ballon(top_event, top_rect, False)

    def _draw_ballon(self, event, event_rect, sticky):
        """Draw one ballon on a selected event that has 'description' data."""
        # Constants
        MAX_TEXT_WIDTH = 200
        MIN_WIDTH = 100
        inner_rect_w = 0
        inner_rect_h = 0
        # Icon
        (iw, ih) = (0, 0)
        icon = event.get_data("icon")
        if icon != None:
            (iw, ih) = icon.Size
            inner_rect_w = iw
            inner_rect_h = ih
        # Text
        self.dc.SetFont(get_default_font(8))
        font_h = self.dc.GetCharHeight()
        (tw, th) = (0, 0)
        description = event.get_data("description")
        lines = None
        if description != None:
            lines = break_text(description, self.dc, MAX_TEXT_WIDTH)
            th = len(lines) * self.dc.GetCharHeight()
            for line in lines:
                (lw, lh) = self.dc.GetTextExtent(line)
                tw = max(lw, tw)
            if icon != None:
                inner_rect_w += BALLOON_RADIUS
            inner_rect_w += min(tw, MAX_TEXT_WIDTH)
            inner_rect_h = max(inner_rect_h, th)
        inner_rect_w = max(MIN_WIDTH, inner_rect_w)
        bounding_rect, x, y = self._draw_balloon_bg(
            self.dc, (inner_rect_w, inner_rect_h),
            (event_rect.X + event_rect.Width / 2,
            event_rect.Y),
            True, sticky)
        if icon != None:
            self.dc.DrawBitmap(icon, x, y, False)
            x += iw + BALLOON_RADIUS
        if lines != None:
            ty = y
            for line in lines:
                self.dc.DrawText(line, x, ty)
                ty += font_h
            x += tw
        # Write data so we know where the balloon was drawn
        # Following two lines can be used when debugging the rectangle
        #self.dc.SetBrush(wx.TRANSPARENT_BRUSH)
        #self.dc.DrawRectangleRect(bounding_rect)
        self.balloon_data.append((event, bounding_rect))

    def _draw_balloon_bg(self, dc, inner_size, tip_pos, above, sticky):
        """
        Draw the balloon background leaving inner_size for content.

        tip_pos determines where the tip of the ballon should be.

        above determines if the balloon should be above the tip (True) or below
        (False). This is not currently implemented.

                    W
           |----------------|
             ______________           _
            /              \          |             R = Corner Radius
           |                |         |            AA = Left Arrow-leg angle
           |  W_ARROW       |         |  H     MARGIN = Text margin
           |     |--|       |         |             * = Starting point
            \____    ______/          _
                /  /                  |
               /_/                    |  H_ARROW
              *                       -
           |----|
           ARROW_OFFSET
    
        Calculation of points starts at the tip of the arrow and continues
        clockwise around the ballon.

        Return (bounding_rect, x, y) where x and y is at top of inner region.
        """
        # Prepare path object
        gc = wx.GraphicsContext.Create(self.dc)
        path = gc.CreatePath()
        # Calculate path
        R = BALLOON_RADIUS
        W = 1 * R + inner_size[0]
        H = 1 * R + inner_size[1]
        H_ARROW = 14
        W_ARROW = 15
        W_ARROW_OFFSET = R + 25
        AA = 20
        # Starting point at the tip of the arrow
        (tipx, tipy) = tip_pos
        p0 = wx.Point(tipx, tipy)
        path.MoveToPoint(p0.x, p0.y)
        # Next point is the left base of the arrow
        p1 = wx.Point(p0.x + H_ARROW * math.tan(math.radians(AA)),
                      p0.y - H_ARROW)
        path.AddLineToPoint(p1.x, p1.y)
        # Start of lower left rounded corner
        p2 = wx.Point(p1.x - W_ARROW_OFFSET + R, p1.y)
        bottom_y = p2.y
        path.AddLineToPoint(p2.x, p2.y)
        # The lower left rounded corner. p3 is the center of the arc
        p3 = wx.Point(p2.x, p2.y - R)
        path.AddArc(p3.x, p3.y, R, math.radians(90), math.radians(180))
        # The left side
        p4 = wx.Point(p3.x - R, p3.y - H + R)
        left_x = p4.x
        path.AddLineToPoint(p4.x, p4.y)
        # The upper left rounded corner. p5 is the center of the arc
        p5 = wx.Point(p4.x + R, p4.y)
        path.AddArc(p5.x, p5.y, R, math.radians(180), math.radians(-90))
        # The upper side
        p6 = wx.Point(p5.x + W - R, p5.y - R)
        top_y = p6.y
        path.AddLineToPoint(p6.x, p6.y)
        # The upper right rounded corner. p7 is the center of the arc
        p7 = wx.Point(p6.x, p6.y + R)
        path.AddArc(p7.x, p7.y, R, math.radians(-90), math.radians(0))
        # The right side
        p8 = wx.Point(p7.x + R , p7.y + H - R)
        right_x = p8.x
        path.AddLineToPoint(p8.x, p8.y)
        # The lower right rounded corner. p9 is the center of the arc
        p9 = wx.Point(p8.x - R, p8.y)
        path.AddArc(p9.x, p9.y, R, math.radians(0), math.radians(90))
        # The lower side
        p10 = wx.Point(p9.x - W + W_ARROW +  W_ARROW_OFFSET, p9.y + R)
        path.AddLineToPoint(p10.x, p10.y)
        path.CloseSubpath()
        # Draw sharp lines on GTK which uses Cairo
        # See: http://www.cairographics.org/FAQ/#sharp_lines
        gc.Translate(0.5, 0.5)
        # Draw the ballon
        BORDER_COLOR = wx.Color(127, 127, 127)
        BG_COLOR = wx.Color(255, 255, 231)
        PEN = wx.Pen(BORDER_COLOR, 1, wx.SOLID)
        BRUSH = wx.Brush(BG_COLOR, wx.SOLID)
        gc.SetPen(PEN)
        gc.SetBrush(BRUSH)
        gc.DrawPath(path)
        # Draw the pin
        if sticky:
            pin = wx.Bitmap(os.path.join(ICONS_DIR, "stickypin.png"))
        else:
            pin = wx.Bitmap(os.path.join(ICONS_DIR, "unstickypin.png"))
        self.dc.DrawBitmap(pin, p7.x -5, p6.y + 5, True)
                
        # Return
        bx = left_x
        by = top_y
        bw = W + R + 1
        bh = H + R + H_ARROW + 1
        bounding_rect = wx.Rect(bx, by, bw, bh)
        return (bounding_rect, left_x + BALLOON_RADIUS, top_y + BALLOON_RADIUS)


def break_text(text, dc, max_width_in_px):
    """ Break the text into lines so that they fits within the given width."""
    sentences = text.split("\n")
    lines = []
    for sentence in sentences:
        w, h = dc.GetTextExtent(sentence)
        if w <= max_width_in_px:
            lines.append(sentence)
        # The sentence is too long. Break it.
        else:
            break_sentence(dc, lines, sentence, max_width_in_px);
    return lines


def break_sentence(dc, lines, sentence, max_width_in_px):
    """Break a sentence into lines."""
    line = []
    max_word_len_in_ch = get_max_word_length(dc, max_width_in_px)
    words = break_line(dc, sentence, max_word_len_in_ch)
    for word in words:
        w, h = dc.GetTextExtent("".join(line) + word + " ")
        # Max line length reached. Start a new line
        if w > max_width_in_px:
            lines.append("".join(line))
            line = []
        line.append(word + " ")
        # Word edning with '-' is a broken word. Start a new line
        if word.endswith('-'):
            lines.append("".join(line))
            line = []
    if len(line) > 0:
        lines.append("".join(line))


def break_line(dc, sentence, max_word_len_in_ch):
    """Break a sentence into words."""
    words = sentence.split(" ")
    new_words = []
    for word in words:
        broken_words = break_word(dc, word, max_word_len_in_ch)
        for broken_word in broken_words:
            new_words.append(broken_word)
    return new_words


def break_word(dc, word, max_word_len_in_ch):
    """
    Break words if they are too long.

    If a single word is too long to fit we have to break it.
    If not we just return the word given.
    """
    words = []
    while len(word) > max_word_len_in_ch:
        word1 = word[0:max_word_len_in_ch] + "-"
        word =  word[max_word_len_in_ch:]
        words.append(word1)
    words.append(word)
    return words


def get_max_word_length(dc, max_width_in_px):
    TEMPLATE_CHAR = 'K'
    word = [TEMPLATE_CHAR]
    w, h = dc.GetTextExtent("".join(word))
    while w < max_width_in_px:
        word.append(TEMPLATE_CHAR)
        w, h = dc.GetTextExtent("".join(word))
    return len(word) - 1
