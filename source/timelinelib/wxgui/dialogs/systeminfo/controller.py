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


from sys import version as python_version
import locale
import platform
import wx

from timelinelib.wxgui.framework import Controller
from timelinelib.features.experimental.experimentalfeaturedateformatting import create_locale_sample_date


class SystemInfoDialogController(Controller):

    def on_init(self):
        self.view.SetSystemVersion(self._get_system_version())
        self.view.SetPythonVersion(self._get_python_version())
        self.view.SetWxPythonVersion(self._get_wxpython_version())
        self.view.SetLocaleSetting(self._get_locale_setting())
        self.view.SetDateFormat(self._create_locale_sample_date())
        self.view.Fit()

    def _get_system_version(self):
        return ", ".join(platform.uname())

    def _get_python_version(self):
        return python_version.replace("\n", "")

    def _get_wxpython_version(self):
        return wx.version()

    def _create_locale_sample_date(self):
        sample = create_locale_sample_date()
        sample = sample.replace("3", "y")
        sample = sample.replace("2", "d")
        sample = sample.replace("1", "m")
        return sample

    def _get_locale_setting(self):
        return " ".join(locale.getlocale(locale.LC_TIME))
