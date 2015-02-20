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


import wx

from timelinelib.plugin.plugins.defaulteventboxdrawer import DefaultEventBoxDrawer
from timelinelib.drawing.utils import darken_color
from timelinelib.drawing.utils import lighten_color


class GradientEventBoxDrawer(DefaultEventBoxDrawer):

    def display_name(self):
        return _("Gradient Event box drawer")

    def run(self, dc, rect, event):
        dc.SetBrush(wx.GREEN_BRUSH)
        dc.SetPen(wx.Pen(self._get_border_color(event), 1, wx.SOLID))
        dc.DrawRectangleRect(rect)
        inner_rect = wx.Rect(rect.x + 1, rect.y + 1, rect.width - 2, rect.height - 2)
        dc.GradientFillLinear(inner_rect, self._get_light_color(event), self._get_dark_color(event), wx.SOUTH)

    def _get_light_color(self, event):
        return lighten_color(self._get_base_color(event))

    def _get_dark_color(self, event):
        return darken_color(self._get_base_color(event), factor=0.8)
