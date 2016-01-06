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


DividerPositionChangedEvent, EVT_DIVIDER_POSITION_CHANGED = wx.lib.newevent.NewEvent()
HintEvent, EVT_HINT = wx.lib.newevent.NewEvent()
TimelineRedrawnEvent, EVT_TIMELINE_REDRAWN = wx.lib.newevent.NewEvent()


def create_divider_position_changed_event():
    return DividerPositionChangedEvent()


def create_hint_event(text):
    return HintEvent(text=text)


def create_timeline_redrawn_event():
    return TimelineRedrawnEvent()