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


import platform
import gettext

from timelinelib.about import APPLICATION_NAME
from timelinelib.arguments import ApplicationArguments
from timelinelib.gui.setup import start_wx_application
from timelinelib.paths import LOCALE_DIR


def setup_gettext():
    if platform.system() == "Windows":
        # The appropriate environment variables are set on other systems
        import locale
        import os
        language, encoding = locale.getdefaultlocale()
        os.environ['LANG'] = language
    gettext.install(APPLICATION_NAME.lower(), LOCALE_DIR, unicode=True)


def main():
    setup_gettext()
    start_wx_application(ApplicationArguments())
