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
Handle application configuration.

This module is global and can be used by all modules. Before accessing
configurations, the read function should be called. To save the current
configuration back to file, call the write method.
"""


import sys
from ConfigParser import ConfigParser
from ConfigParser import DEFAULTSECT
import os.path

import wx


# Name used in ConfigParser
WINDOW_WIDTH = "window_width"
WINDOW_HEIGHT = "window_height"
WINDOW_XPOS = "window xpos"
WINDOW_YPOS = "window ypos"
WINDOW_MAXIMIZED = "window_maximized"
SHOW_SIDEBAR = "show_sidebar"
SHOW_LEGEND = "show_legend"
SIDEBAR_WIDTH = "sidebar_width"
RECENT_FILES = "recent_files"
OPEN_RECENT_AT_STARTUP = "open_recent_at_startup"
BALLOON_ON_HOVER = "balloon_on_hover"
WEEK_START = "week_start"
DEFAULTS = {
    WINDOW_WIDTH: "900",
    WINDOW_HEIGHT: "500",
    WINDOW_XPOS: "-1",
    WINDOW_YPOS: "-1",
    WINDOW_MAXIMIZED: "False",
    SHOW_SIDEBAR: "True",
    SIDEBAR_WIDTH: "200",
    SHOW_LEGEND: "True",
    OPEN_RECENT_AT_STARTUP: "True",
    RECENT_FILES: "",
    BALLOON_ON_HOVER: "True",
    WEEK_START: "monday",
}
# Some settings
MAX_NBR_OF_RECENT_FILES_SAVED = 5
ENCODING = "utf-8"


global_config = None


def init():
    # Note: wx.App object must have been created before calling this method.
    global global_config
    path = os.path.join(wx.StandardPaths.Get().GetUserConfigDir(),
                        ".thetimelineproj.cfg")
    global_config = Config(path)
    global_config.read()


# These functions are just wrappers to preserve the old interface to the config
# module. In the future they should be removed. In the future you should either
# get passed a Config object or use the global global_config.
def read(): init()
def write(): global_config.write()
def get_window_size(): return global_config.window_size
def set_window_size(size): global_config.window_size = size
def get_window_pos(): return global_config.window_pos
def set_window_pos(pos): global_config.window_pos = pos
def get_window_maximized(): return global_config.window_maximized
def set_window_maximized(maximized): global_config.window_maximized = maximized
def get_show_sidebar(): return global_config.show_sidebar
def set_show_sidebar(show): global_config.show_sidebar = show
def get_show_legend(): return global_config.show_legend
def set_show_legend(show): global_config.show_legend = show
def get_sidebar_width(): return global_config.sidebar_width
def set_sidebar_width(width): global_config.sidebar_width = width
def get_recently_opened(): return global_config.recently_opened
def append_recently_opened(path): global_config.append_recently_opened(path)
def get_open_recent_at_startup(): return global_config.open_recent_at_startup
def set_open_recent_at_startup(open): global_config.open_recent_at_startup = open
def get_balloon_on_hover(): return global_config.balloon_on_hover
def set_balloon_on_hover(balloon_on_hover): global_config.balloon_on_hover = balloon_on_hover


class Config(object):
    """
    Provide read and write access to application configuration settings.

    Built as a wrapper around ConfigParser: Properties exist to read and write
    values but ConfigParser does the actual reading and writing of the
    configuration file.
    """

    def __init__(self, path):
        self.path = path
        self.config_parser = ConfigParser(DEFAULTS)

    def read(self):
        """Read settings from file specified in constructor."""
        self.config_parser.read(self.path)

    def write(self):
        """
        Write settings to file specified in constructor and raise IOError if
        failed.
        """
        f = open(self.path, "w")
        try:
            self.config_parser.write(f)
        finally:
            f.close()

    def get_window_size(self):
        return (self.config_parser.getint(DEFAULTSECT, WINDOW_WIDTH),
                self.config_parser.getint(DEFAULTSECT, WINDOW_HEIGHT))
    def set_window_size(self, size):
        width, height = size
        self.config_parser.set(DEFAULTSECT, WINDOW_WIDTH, str(width))
        self.config_parser.set(DEFAULTSECT, WINDOW_HEIGHT, str(height))
    window_size = property(get_window_size, set_window_size)

    def get_window_pos(self):
        width, height = self.get_window_size()
        # Make sure that some area of the window is visible on the screen
        # Some part of the titlebar must be visible
        xpos = max(-width + 100,
                   self.config_parser.getint(DEFAULTSECT, WINDOW_XPOS))
        # Titlebar must not be above the upper screen border
        ypos = max(0, self.config_parser.getint(DEFAULTSECT, WINDOW_YPOS))
        return (xpos, ypos)

    def set_window_pos(self, pos):
        xpos, ypos = pos
        self.config_parser.set(DEFAULTSECT, WINDOW_XPOS, str(xpos))
        self.config_parser.set(DEFAULTSECT, WINDOW_YPOS, str(ypos))
    window_pos = property(get_window_pos, set_window_pos)

    def get_window_maximized(self):
        return self.config_parser.getboolean(DEFAULTSECT, WINDOW_MAXIMIZED)
    def set_window_maximized(self, maximized):
        self.config_parser.set(DEFAULTSECT, WINDOW_MAXIMIZED, str(maximized))
    window_maximized = property(get_window_maximized, set_window_maximized)

    def get_show_sidebar(self):
        return self.config_parser.getboolean(DEFAULTSECT, SHOW_SIDEBAR)
    def set_show_sidebar(self, show):
        self.config_parser.set(DEFAULTSECT, SHOW_SIDEBAR, str(show))
    show_sidebar = property(get_show_sidebar, set_show_sidebar)

    def get_show_legend(self):
        return self.config_parser.getboolean(DEFAULTSECT, SHOW_LEGEND)
    def set_show_legend(self, show):
        self.config_parser.set(DEFAULTSECT, SHOW_LEGEND, str(show))
    show_legend = property(get_show_legend, set_show_legend)

    def get_sidebar_width(self):
        return self.config_parser.getint(DEFAULTSECT, SIDEBAR_WIDTH)
    def set_sidebar_width(self, width):
        self.config_parser.set(DEFAULTSECT, SIDEBAR_WIDTH, str(width))
    sidebar_width = property(get_sidebar_width, set_sidebar_width)

    def get_recently_opened(self):
        ro = self.config_parser.get(DEFAULTSECT, RECENT_FILES).decode(ENCODING).split(",")
        # Filter out empty elements: "".split(",") will return [""] but we want
        # the empty list
        ro_filtered = [x for x in ro if x]
        return ro_filtered
    recently_opened = property(get_recently_opened)

    def append_recently_opened(self, path):
        if path in [":tutorial:"]:
            # Special timelines should not be saved
            return
        if isinstance(path, str):
            # This path might have come from the command line so we need to convert
            # it to unicode
            path = path.decode(sys.getfilesystemencoding())
        abs_path = os.path.abspath(path)
        current = self.recently_opened
        # Just keep one entry of the same path in the list
        if abs_path in current:
            current.remove(abs_path)
        current.insert(0, abs_path)
        self.config_parser.set(DEFAULTSECT, RECENT_FILES,
              (",".join(current[:MAX_NBR_OF_RECENT_FILES_SAVED])).encode(ENCODING))

    def get_open_recent_at_startup(self):
        return self.config_parser.getboolean(DEFAULTSECT, OPEN_RECENT_AT_STARTUP)
    def set_open_recent_at_startup(self, open):
        self.config_parser.set(DEFAULTSECT, OPEN_RECENT_AT_STARTUP, str(open))
    open_recent_at_startup = property(get_open_recent_at_startup,
                                      set_open_recent_at_startup)

    def get_balloon_on_hover(self):
        return self.config_parser.getboolean(DEFAULTSECT, BALLOON_ON_HOVER)
    def set_balloon_on_hover(self, balloon_on_hover):
        self.config_parser.set(DEFAULTSECT, BALLOON_ON_HOVER, str(balloon_on_hover))
    balloon_on_hover = property(get_balloon_on_hover, set_balloon_on_hover)

    def get_week_start(self):
        return self.config_parser.get(DEFAULTSECT, WEEK_START)
    def set_week_start(self, week_start):
        if not week_start in ["monday", "sunday"]:
            raise ValueError("Invalid week start.")
        self.config_parser.set(DEFAULTSECT, WEEK_START, week_start)
    week_start = property(get_week_start, set_week_start)
