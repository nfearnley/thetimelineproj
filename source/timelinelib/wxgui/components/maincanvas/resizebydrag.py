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


import wx

from timelinelib.wxgui.components.maincanvas.scrollbase import ScrollViewInputHandler


class ResizeByDragInputHandler(ScrollViewInputHandler):

    def __init__(self, state, timeline_canvas, status_bar, main_frame, event, direction):
        ScrollViewInputHandler.__init__(self, timeline_canvas)
        self._state = state
        self._main_frame = main_frame
        self.timeline_canvas = timeline_canvas
        self.status_bar = status_bar
        self.event = event
        self.direction = direction
        self.timer_running = False

    def mouse_moved(self, x, y, alt_down=False):
        ScrollViewInputHandler.mouse_moved(self, x, y, alt_down)
        self._resize_event()

    def left_mouse_up(self):
        ScrollViewInputHandler.left_mouse_up(self)
        self._clear_status_text()
        if self.timeline_canvas.GetDb() is not None:
            self.timeline_canvas.GetDb()._save_if_not_disabled()
        self._state.change_to_no_op()
        self._main_frame.edit_ends()

    def view_scrolled(self):
        self._resize_event()

    def _resize_event(self):
        if self.event.get_locked():
            return
        new_time = self.timeline_canvas.GetTimeAt(self.last_x)
        new_snapped_time = self.timeline_canvas.Snap(new_time)
        if self.direction == wx.LEFT:
            new_start = new_snapped_time
            new_end = self.event.get_time_period().end_time
            if new_start > new_end:
                new_start = new_end
        else:
            new_start = self.event.get_time_period().start_time
            new_end = new_snapped_time
            if new_end < new_start:
                new_end = new_start
        self.event.update_period(new_start, new_end)
        self._clear_status_text()
        if self.event.is_container():
            self._adjust_container_edges()
        self.timeline_canvas.Redraw()

    def _adjust_container_edges(self):
        self.event.strategy._set_time_period()

    def _clear_status_text(self):
        self.status_bar.set_text("")
