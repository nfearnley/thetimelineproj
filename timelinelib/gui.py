# Copyright (C) 2009  Rickard Lindberg, Roger Lindberg
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
GUI components.

The GUI components are mainly for interacting with the user and should not
contain much logic. For example, the drawing algorithm is responsible for
drawing the timeline, but the `DrawingArea` class in this module provides the
GUI component on which it will draw.
"""


import datetime
import calendar
import logging
import os.path
from datetime import datetime as dt
from datetime import time

import wx
import wx.html
import wx.lib.colourselect as colourselect
from wx.lib.masked import TimeCtrl

from timelinelib.db import open as db_open
from timelinelib.db.interface import TimelineIOError
from timelinelib.db.interface import TimelineDB
from timelinelib.db.interface import STATE_CHANGE_ANY
from timelinelib.db.interface import STATE_CHANGE_CATEGORY
from timelinelib.db.objects import Event
from timelinelib.db.objects import Category
from timelinelib.db.objects import TimePeriod
from timelinelib.drawing import get_drawer
from timelinelib.drawing.interface import DrawingHints
from timelinelib.drawing.interface import EventRuntimeData
from timelinelib.drawing.utils import mult_timedelta
from timelinelib.guinew.utils import TxtException
from timelinelib.guinew.utils import sort_categories
from timelinelib.guinew.utils import _set_focus_and_select
from timelinelib.guinew.utils import _parse_text_from_textbox
from timelinelib.guinew.utils import _display_error_message
from timelinelib.guinew.utils import _ask_question
from timelinelib.guinew.utils import _step_function
from timelinelib.guinew.utils import _create_wildcard
from timelinelib.guinew.utils import _extend_path
import config
from about import display_about_dialog
from about import APPLICATION_NAME
from paths import ICONS_DIR
from paths import HELP_RESOURCES_DIR
import printing
import help
import help_pages


# Border, in pixels, between controls in a window (should always be used when
# border is needed)
BORDER = 5
# Used by dialogs as a return code when a TimelineIOError has been raised
ID_ERROR = wx.NewId()
# Used by Sizer and Mover classes to detect when to go into action
HIT_REGION_PX_WITH = 5

help_browser = None


class MainFrame(wx.Frame):
    """
    The main frame of the application.

    Can be resized, maximized and minimized. Contains one panel: MainPanel.

    Owns an instance of a timeline that is currently being displayed. When the
    timeline changes, this control will notify sub controls about it.
    """

    def __init__(self):
        wx.Frame.__init__(self, None, size=config.get_window_size(),
                          style=wx.DEFAULT_FRAME_STYLE)
        # To enable translations of wx stock items.
        self.locale = wx.Locale(wx.LANGUAGE_DEFAULT)
        self._set_initial_values_to_member_variables()
        self._create_gui()
        self.Maximize(config.get_window_maximized())
        self.SetTitle(APPLICATION_NAME)
        self.mnu_view_sidebar.Check(config.get_show_sidebar())
        self.mnu_view_legend.Check(config.get_show_legend())
        self.mnu_view_balloons.Check(config.get_balloon_on_hover())
        self.SetIcons(self._load_icon_bundle())
        self._init_help_system()
        self.main_panel.show_welcome_panel()
        self._enable_disable_menus()

    def open_timeline(self, input_file):
        """Read timeline info from the given input file and display it."""
        # Make sure that we have an absolute path
        input_file_abs = os.path.abspath(input_file)
        try:
            timeline = db_open(input_file_abs)
        except TimelineIOError, e:
            self.handle_timeline_error(e)
        else:
            config.append_recently_opened(input_file_abs)
            self._update_open_recent_submenu()
            self._display_timeline(timeline)

    def open_timeline_if_exists(self, path):
        if os.path.exists(path):
            self.open_timeline(path)
        else:
            _display_error_message(_("File '%s' does not exist.") % path, self)

    def create_new_event(self, start=None, end=None):
        try:
            dialog = EventEditor(self, _("Create Event"), self.timeline,
                                 start, end)
        except TimelineIOError, e:
            self.handle_timeline_error(e)
        else:
            if dialog.ShowModal() == ID_ERROR:
                self._switch_to_error_view(dialog.error)
            dialog.Destroy()

    def edit_event(self, event):
        try:
            dialog = EventEditor(self, _("Edit Event"), self.timeline,
                                 event=event)
        except TimelineIOError, e:
            self.handle_timeline_error(e)
        else:
            if dialog.ShowModal() == ID_ERROR:
                self._switch_to_error_view(dialog.error)
            dialog.Destroy()

    def edit_categories(self):
        try:
            dialog = CategoriesEditor(self, self.timeline)
        except TimelineIOError, e:
            self.handle_timeline_error(e)
        else:
            if dialog.ShowModal() == ID_ERROR:
                self._switch_to_error_view(dialog.error)
            dialog.Destroy()

    def handle_timeline_error(self, error):
        _display_error_message(error.message, self)
        self._switch_to_error_view(error)

    def _create_gui(self):
        def add_ellipses_to_menuitem(id):
            plain = wx.GetStockLabel(id,
                    wx.STOCK_WITH_ACCELERATOR|wx.STOCK_WITH_MNEMONIC)
            # format of plain 'xxx[\tyyy]', example '&New\tCtrl+N'
            tab_index = plain.find("\t")
            if tab_index != -1:
                return plain[:tab_index] + "..." + plain[tab_index:]
            return plain + "..."
        # The only content of this frame is the MainPanel
        self.main_panel = MainPanel(self)
        self.Bind(wx.EVT_CLOSE, self._window_on_close)
        # The status bar
        self.CreateStatusBar()
        # The menu
        # File menu
        self.mnu_file = wx.Menu()
        mnu_file_new = wx.Menu()
        accel = wx.GetStockLabel(wx.ID_NEW, wx.STOCK_WITH_ACCELERATOR|wx.STOCK_WITH_MNEMONIC)
        accel = accel.split("\t", 1)[1]
        self.mnu_file_new_file = mnu_file_new.Append(wx.ID_NEW, 
                                                     _("File Timeline...") + "\t" + accel, 
                                                     _("File Timeline..."))
        self.mnu_file_new_dir = mnu_file_new.Append(wx.ID_ANY, 
                                                    _("Directory Timeline..."), 
                                                    _("Directory Timeline..."))
        self.mnu_file.AppendMenu(wx.ID_ANY, _("New"), mnu_file_new,
                                 _("Create a new timeline"))
        self.mnu_file.Append(wx.ID_OPEN, add_ellipses_to_menuitem(wx.ID_OPEN),
                             _("Open an existing timeline"))
        self.mnu_file_open_recent_submenu = wx.Menu()
        self.mnu_file.AppendMenu(wx.ID_ANY, _("Open &Recent"), self.mnu_file_open_recent_submenu)
        self._update_open_recent_submenu()
        self.mnu_file.AppendSeparator()
        self.mnu_file_print_setup = self.mnu_file.Append(wx.ID_PRINT_SETUP,
                                       _("Page Set&up..."),
                                       _("Setup page for printing"))
        self.mnu_file_print_preview = self.mnu_file.Append(wx.ID_PREVIEW, "",
                                       _("Print Preview"))
        self.mnu_file_print = self.mnu_file.Append(wx.ID_PRINT,
                                       add_ellipses_to_menuitem(wx.ID_PRINT),
                                       _("Print"))
        self.mnu_file.AppendSeparator()
        self.mnu_file_export = self.mnu_file.Append(wx.ID_ANY,
                                                   _("&Export to Image..."),
                                                   _("Export the current view to a PNG image"))
        self.mnu_file.AppendSeparator()
        self.mnu_file.Append(wx.ID_EXIT, "",
                             _("Exit the program"))
        self.Bind(wx.EVT_MENU, self._mnu_file_new_on_click, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self._mnu_file_new_dir_on_click, self.mnu_file_new_dir)
        self.Bind(wx.EVT_MENU, self._mnu_file_open_on_click, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self._mnu_file_print_on_click, id=wx.ID_PRINT)
        self.Bind(wx.EVT_MENU, self._mnu_file_print_preview_on_click, id=wx.ID_PREVIEW)
        self.Bind(wx.EVT_MENU, self._mnu_file_print_setup_on_click, id=wx.ID_PRINT_SETUP)
        self.Bind(wx.EVT_MENU, self._mnu_file_export_on_click,
                  self.mnu_file_export)
        self.Bind(wx.EVT_MENU, self._mnu_file_exit_on_click, id=wx.ID_EXIT)
        # Edit menu
        self.mnu_edit = wx.Menu()
        mnu_edit_preferences = self.mnu_edit.Append(wx.ID_PREFERENCES)
        self.Bind(wx.EVT_MENU, self._mnu_edit_preferences_on_click,
                  mnu_edit_preferences)
        # Timeline menu
        self.mnu_timeline = wx.Menu()
        self.mnu_timeline_create_event = self.mnu_timeline.Append(wx.ID_ANY,
                                    _("Create &Event..."),
                                    _("Create a new event"))
        self.mnu_timeline_edit_categories = self.mnu_timeline.Append(wx.ID_ANY,
                                       _("Edit &Categories"),
                                       _("Edit categories"))
        self.Bind(wx.EVT_MENU, self._mnu_timeline_create_event_on_click,
                  self.mnu_timeline_create_event)
        self.Bind(wx.EVT_MENU, self._mnu_timeline_edit_categories_on_click,
                  self.mnu_timeline_edit_categories)
        # View menu
        self.mnu_view = wx.Menu()
        self.mnu_view_sidebar = self.mnu_view.Append(wx.ID_ANY,
                                                     _("&Sidebar\tCtrl+I"),
                                                     kind=wx.ITEM_CHECK)
        self.mnu_view_legend = self.mnu_view.Append(wx.ID_ANY,
                                                    _("&Legend"),
                                                    kind=wx.ITEM_CHECK)
        self.mnu_view.AppendSeparator()
        self.mnu_view_balloons = self.mnu_view.Append(wx.ID_ANY,
                                                    _("&Balloons on hover"),
                                                    kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self._mnu_view_sidebar_on_click,
                  self.mnu_view_sidebar)
        self.Bind(wx.EVT_MENU, self._mnu_view_legend_on_click,
                  self.mnu_view_legend)
        self.Bind(wx.EVT_MENU, self._mnu_view_balloons_on_click,
                  self.mnu_view_balloons)
        # Navigate menu
        self.mnu_navigate = wx.Menu()
        goto_today = self.mnu_navigate.Append(wx.ID_ANY, _("Go to &Today\tCtrl+H"))
        goto_date = self.mnu_navigate.Append(wx.ID_ANY, _("Go to D&ate...\tCtrl+G"))
        self.mnu_navigate.AppendSeparator()
        backward = self.mnu_navigate.Append(wx.ID_ANY, _("Backward\tPgUp"))
        forward = self.mnu_navigate.Append(wx.ID_ANY, _("Forward\tPgDn"))
        self.mnu_navigate.AppendSeparator()
        fit_year = self.mnu_navigate.Append(wx.ID_ANY, _("Fit Year"))
        fit_month = self.mnu_navigate.Append(wx.ID_ANY, _("Fit Month"))
        fit_day = self.mnu_navigate.Append(wx.ID_ANY, _("Fit Day"))
        self.mnu_navigate.AppendSeparator()
        find_first = self.mnu_navigate.Append(wx.ID_ANY, _("Find First Event"))
        find_last  = self.mnu_navigate.Append(wx.ID_ANY, _("Find Last Event"))
        self.Bind(wx.EVT_MENU, self._mnu_navigate_goto_today_on_click, goto_today)
        self.Bind(wx.EVT_MENU, self._mnu_navigate_goto_date_on_click, goto_date)
        self.Bind(wx.EVT_MENU, self._mnu_navigate_backward_on_click, backward)
        self.Bind(wx.EVT_MENU, self._mnu_navigate_forward_on_click, forward)
        self.Bind(wx.EVT_MENU, self._mnu_navigate_fit_year_on_click, fit_year)
        self.Bind(wx.EVT_MENU, self._mnu_navigate_fit_month_on_click, fit_month)
        self.Bind(wx.EVT_MENU, self._mnu_navigate_fit_day_on_click, fit_day)
        self.Bind(wx.EVT_MENU, self._mnu_navigate_find_first_on_click, find_first)
        self.Bind(wx.EVT_MENU, self._mnu_navigate_find_last_on_click, find_last)
        # Help menu
        self.mnu_help = wx.Menu()
        help_contents = self.mnu_help.Append(wx.ID_HELP, _("&Contents\tF1"))
        self.Bind(wx.EVT_MENU, self._mnu_help_contents_on_click, help_contents)
        self.mnu_help.AppendSeparator()
        help_tutorial = self.mnu_help.Append(wx.ID_ANY, _("Getting started tutorial"))
        self.Bind(wx.EVT_MENU, self._mnu_help_tutorial_on_click, help_tutorial)
        help_contact = self.mnu_help.Append(wx.ID_ANY, _("Contact"))
        self.Bind(wx.EVT_MENU, self._mnu_help_contact_on_click, help_contact)
        self.mnu_help.AppendSeparator()
        help_about = self.mnu_help.Append(wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self._mnu_help_about_on_click, help_about)
        # The menu bar
        menuBar = wx.MenuBar()
        menuBar.Append(self.mnu_file, _("&File"))
        menuBar.Append(self.mnu_edit, _("&Edit"))
        menuBar.Append(self.mnu_view, _("&View"))
        menuBar.Append(self.mnu_timeline, _("&Timeline"))
        menuBar.Append(self.mnu_navigate, _("&Navigate"))
        menuBar.Append(self.mnu_help, _("&Help"))
        self.SetMenuBar(menuBar)

    def _update_open_recent_submenu(self):
        # Clear items
        for item in self.mnu_file_open_recent_submenu.GetMenuItems():
            self.mnu_file_open_recent_submenu.DeleteItem(item)
        # Create new items and map (item id > path)
        self.open_recent_map = {}
        for path in config.get_recently_opened():
            name = "%s (%s)" % (
                os.path.basename(path),
                os.path.dirname(os.path.abspath(path)))
            item = self.mnu_file_open_recent_submenu.Append(wx.ID_ANY, name)
            self.open_recent_map[item.GetId()] = path
            self.Bind(wx.EVT_MENU, self._mnu_file_open_recent_item_on_click,
                      item)

    def _window_on_close(self, event):
        self._save_current_timeline_data()
        self._save_application_config()
        self.Destroy()

    def _mnu_file_new_on_click(self, event):
        """Event handler used when the user wants to create a new timeline."""
        self._create_new_timeline()

    def _mnu_file_new_dir_on_click(self, event):
        self._create_new_dir_timeline()

    def _mnu_file_open_on_click(self, event):
        """Event handler used when the user wants to open a new timeline."""
        self._open_existing_timeline()

    def _mnu_file_open_recent_item_on_click(self, event):
        path = self.open_recent_map[event.GetId()]
        self.open_timeline_if_exists(path)

    def _mnu_file_print_on_click(self, event):
        self.main_panel.drawing_area.print_timeline(event)

    def _mnu_file_print_preview_on_click(self, event):
        self.main_panel.drawing_area.print_preview(event)

    def _mnu_file_print_setup_on_click(self, event):
        self.main_panel.drawing_area.print_setup(event)

    def _mnu_file_export_on_click(self, evt):
        self._export_to_image()

    def _mnu_file_exit_on_click(self, evt):
        """Event handler for the Exit menu item"""
        self.Close()

    def _mnu_edit_preferences_on_click(self, evt):
        dialog = PreferencesDialog(self)
        dialog.ShowModal()
        dialog.Destroy()

    def _mnu_view_sidebar_on_click(self, evt):
        if evt.IsChecked():
            self.main_panel.show_sidebar()
        else:
            self.main_panel.hide_sidebar()

    def _mnu_view_legend_on_click(self, evt):
        self.main_panel.drawing_area.show_hide_legend(evt.IsChecked())

    def _mnu_view_balloons_on_click(self, evt):
        config.set_balloon_on_hover(evt.IsChecked())
        self.main_panel.drawing_area.balloon_visibility_changed(evt.IsChecked())

    def _mnu_timeline_create_event_on_click(self, evt):
        self.create_new_event()

    def _mnu_timeline_edit_categories_on_click(self, evt):
        self.edit_categories()

    def _mnu_navigate_goto_today_on_click(self, evt):
        self._navigate_timeline(lambda tp: tp.center(dt.now()))

    def _mnu_navigate_goto_date_on_click(self, evt):
        self._goto_date()

    def _mnu_navigate_backward_on_click(self, evt):
        self._navigate_backward()

    def _mnu_navigate_forward_on_click(self, evt):
        self._navigate_forward()

    def _mnu_navigate_fit_year_on_click(self, evt):
        self._navigate_timeline(lambda tp: tp.fit_year())

    def _mnu_navigate_fit_month_on_click(self, evt):
        self._navigate_timeline(lambda tp: tp.fit_month())

    def _mnu_navigate_fit_day_on_click(self, evt):
        self._navigate_timeline(lambda tp: tp.fit_day())

    def _mnu_navigate_find_first_on_click(self, evt):
        event = self.timeline.get_first_event()
        if event:
            start = event.time_period.start_time
            end   = (start + (self.main_panel.drawing_area.time_period.end_time -
                              self.main_panel.drawing_area.time_period.start_time)) 
            self._navigate_timeline(lambda tp: tp.update(start, end))

    def _mnu_navigate_find_last_on_click(self, evt):
        event = self.timeline.get_last_event()
        if event:
            end = event.time_period.end_time
            start = (end - (self.main_panel.drawing_area.time_period.end_time -
                              self.main_panel.drawing_area.time_period.start_time)) 
            self._navigate_timeline(lambda tp: tp.update(start, end))
    
    def _mnu_help_contents_on_click(self, e):
        help_browser.show_page("contents")

    def _mnu_help_tutorial_on_click(self, e):
        help_browser.show_page("tutorial")

    def _mnu_help_contact_on_click(self, e):
        help_browser.show_page("contact")

    def _mnu_help_about_on_click(self, e):
        display_about_dialog()

    def _init_help_system(self):
        help_system = help.HelpSystem("contents", HELP_RESOURCES_DIR + "/", "page:")
        help_pages.install(help_system)
        global help_browser
        help_browser = HelpBrowser(self, help_system)

    def _switch_to_error_view(self, error):
        self._display_timeline(None)
        self.main_panel.error_panel.populate(error)
        self.main_panel.show_error_panel()
        self._enable_disable_menus()

    def _display_timeline(self, timeline):
        self.timeline = timeline
        self.main_panel.catbox.set_timeline(self.timeline)
        self.main_panel.drawing_area.set_timeline(self.timeline)
        if timeline == None:
            self.main_panel.show_welcome_panel()
            self.SetTitle(APPLICATION_NAME)
        else:
            self.main_panel.show_timeline_panel()
            self.SetTitle("%s (%s) - %s" % (
                os.path.basename(self.timeline.path),
                os.path.dirname(os.path.abspath(self.timeline.path)),
                APPLICATION_NAME))
        self._enable_disable_menus()

    def _create_new_timeline(self):
        """
        Create a new empty timeline.

        The user is asked to enter the filename of the new timeline to be
        created.

        If the new filename entered, should already exist, the existing
        timeline is opened. The user will be informed about this situation.
        """
        dialog = wx.FileDialog(self, message=_("Create Timeline"),
                               wildcard=self.wildcard, style=wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            self._save_current_timeline_data()
            path, extension = _extend_path(dialog.GetPath(), self.extensions,
                                           self.default_extension)
            if os.path.exists(path):
                msg_first_part = _("The specified timeline already exists.")
                msg_second_part = _("Opening timeline instead of creating new.")
                wx.MessageBox("%s\n\n%s" % (msg_first_part, msg_second_part),
                              _("Information"),
                              wx.OK|wx.ICON_INFORMATION, self)
            self.open_timeline(path)
        dialog.Destroy()

    def _create_new_dir_timeline(self):
        """
        Create a new empty timeline.

        The user is asked to enter the path to a dircetory from which files are
        to be read.

        If the new path entered, should already exist, the existing
        timeline is opened. The user will be informed about this situation.
        """
        dialog = wx.DirDialog(self, message=_("Create Timeline"))
        if dialog.ShowModal() == wx.ID_OK:
            self._save_current_timeline_data()
            self.open_timeline(dialog.GetPath())
        dialog.Destroy()

    def _open_existing_timeline(self):
        """
        Open a new timeline.

        The user is asked to enter the filename of the timeline to be opened.
        """
        dir = ""
        if self.timeline is not None:
            dir = os.path.dirname(self.timeline.path)
        dialog = wx.FileDialog(self, message=_("Open Timeline"),
                               defaultDir=dir,
                               wildcard=self.wildcard, style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            self._save_current_timeline_data()
            self.open_timeline(dialog.GetPath())
        dialog.Destroy()

    def _enable_disable_menus(self):
        """
        Enable or disable menu items depending on the state of the application.
        """
        items_requiring_timeline_view = [
            self.mnu_view_sidebar,
        ]
        items_requiring_timeline = [
            self.mnu_file_print,
            self.mnu_file_print_preview,
            self.mnu_file_print_setup,
            self.mnu_file_export,
            self.mnu_view_legend,
        ]
        items_requiring_update = [
            self.mnu_timeline_create_event, 
            self.mnu_timeline_edit_categories, 
        ]
        for item in self.mnu_timeline.GetMenuItems():
            items_requiring_timeline.append(item)
        for item in self.mnu_navigate.GetMenuItems():
            items_requiring_timeline.append(item)
        have_timeline_view = self.main_panel.timeline_panel_visible()
        have_timeline = self.timeline != None
        is_read_only = have_timeline and self.timeline.is_read_only()     
        for item in items_requiring_timeline_view:
            item.Enable(have_timeline_view)
        for item in items_requiring_timeline:
            item.Enable(have_timeline)
        for item in items_requiring_update:
            item.Enable(not is_read_only)

    def _save_application_config(self):
        config.set_window_size(self.GetSize())
        config.set_window_maximized(self.IsMaximized())
        config.set_show_sidebar(self.mnu_view_sidebar.IsChecked())
        config.set_show_legend(self.mnu_view_legend.IsChecked())
        config.set_sidebar_width(self.main_panel.get_sidebar_width())
        config.write()

    def _save_current_timeline_data(self):
        """
        Saves settings for the timeline that is currently displayed to
        the timeline file. Date saved is:
            - currently displayed time period
        If there is no current timeline, nothing happens.
        This method should be called before a new timeline is opened
        or created or when the application is closed.
        """
        if self.timeline:
            try:
                self.timeline.set_preferred_period(self._get_time_period())
            except TimelineIOError, e:
                _display_error_message(e.message, self)
                # No need to switch to error view since this method is only
                # called on a timeline that is going to be closed anyway (and
                # another timeline, or one, will be displayed instead).

    def _export_to_image(self):
        extension_map = {"png": wx.BITMAP_TYPE_PNG}
        extensions = extension_map.keys()
        wildcard = _create_wildcard(_("Image files"), extensions)
        dialog = wx.FileDialog(self, message=_("Export to Image"),
                               wildcard=wildcard, style=wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            path, extension = _extend_path(dialog.GetPath(), extensions, "png")
            overwrite_question = _("File '%s' exists. Overwrite?") % path
            if (not os.path.exists(path) or
                _ask_question(overwrite_question, self) == wx.YES):
                bitmap = self.main_panel.drawing_area.bgbuf
                image = wx.ImageFromBitmap(bitmap)
                image.SaveFile(path, extension_map[extension])
        dialog.Destroy()

    def _goto_date(self):
        dialog = GotoDateDialog(self, self._get_time_period().mean_time())
        if dialog.ShowModal() == wx.ID_OK:
            self._navigate_timeline(lambda tp: tp.center(dialog.time))
        dialog.Destroy()

    def _navigate_backward(self):
        self._navigate_smart_step(-1)

    def _navigate_forward(self):
        self._navigate_smart_step(1)

    def _set_initial_values_to_member_variables(self):
        """
        Instance variables usage:

        timeline            The timeline currently handled by the application
        extensions          Valid extensions for files containing timeline info
        default_extension   The default extension used in FileDialog
        wildcard            The wildcard used in FileDialog
        """
        self.timeline = None
        self.extensions = ["timeline", "ics"]
        self.default_extension = self.extensions[0]
        self.wildcard = _create_wildcard(_("Timeline files"), self.extensions)

    def _load_icon_bundle(self):
        bundle = wx.IconBundle()
        for size in ["16", "32", "48"]:
            iconpath = os.path.join(ICONS_DIR, "%s.png" % size)
            icon = wx.IconFromBitmap(wx.BitmapFromImage(wx.Image(iconpath)))
            bundle.AddIcon(icon)
        return bundle

    def _navigate_smart_step(self, direction):

        def months_to_year_and_month(months):
            years = int(months / 12)
            month = months - years * 12
            if month == 0:
                month = 12
                years -=1
            return years, month

        tp = self._get_time_period()
        start, end = tp.start_time, tp.end_time
        year_diff = end.year - start.year
        start_months = start.year * 12 + start.month
        end_months = end.year * 12 + end.month
        month_diff = end_months - start_months
        whole_years = start.replace(year=start.year + year_diff) == end
        whole_months = start.day == 1 and end.day == 1
        direction_backward = direction < 0
        # Whole years
        if whole_years and year_diff > 0:
            if direction_backward:
                new_start = start.replace(year=start.year-year_diff)
                new_end   = start
            else:
                new_start = end
                new_end   = end.replace(year=new_start.year+year_diff)
            self._navigate_timeline(lambda tp: tp.update(new_start, new_end))
        # Whole months
        elif whole_months and month_diff > 0:
            if direction_backward:
                new_end = start
                new_start_year, new_start_month = months_to_year_and_month(
                                                        start_months -
                                                        month_diff)
                new_start = start.replace(year=new_start_year,
                                          month=new_start_month)
            else:
                new_start = end
                new_end_year, new_end_month = months_to_year_and_month(
                                                        end_months +
                                                        month_diff)
                new_end = end.replace(year=new_end_year, month=new_end_month)
            self._navigate_timeline(lambda tp: tp.update(new_start, new_end))
        # No need for smart delta
        else:
            self._navigate_timeline(lambda tp: tp.move_delta(direction*tp.delta()))

    def _navigate_timeline(self, navigation_fn):
        """Shortcut for method in DrawingArea."""
        return self.main_panel.drawing_area.navigate_timeline(navigation_fn)

    def _get_time_period(self):
        """Shortcut for method in DrawingArea."""
        return self.main_panel.drawing_area.get_time_period()


class MainPanel(wx.Panel):
    """
    Panel that covers the whole client area of MainFrame.

    Displays one of the following panels:

      * The welcome panel (show_welcome_panel)
      * A splitter with sidebar and DrawingArea (show_timeline_panel)
      * The error panel (show_error_panel)
    """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self._create_gui()
        # Install variables for backwards compatibility
        self.catbox = self.timeline_panel.sidebar.catbox
        self.drawing_area = self.timeline_panel.drawing_area
        self.show_sidebar = self.timeline_panel.show_sidebar
        self.hide_sidebar = self.timeline_panel.hide_sidebar
        self.get_sidebar_width = self.timeline_panel.get_sidebar_width

    def timeline_panel_visible(self):
        return self.timeline_panel.IsShown()

    def show_welcome_panel(self):
        self._show_panel(self.welcome_panel)

    def show_timeline_panel(self):
        self._show_panel(self.timeline_panel)

    def show_error_panel(self):
        self._show_panel(self.error_panel)

    def _create_gui(self):
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.welcome_panel = WelcomePanel(self)
        self.sizer.Add(self.welcome_panel, flag=wx.GROW, proportion=1)
        self.timeline_panel = TimelinePanel(self)
        self.sizer.Add(self.timeline_panel, flag=wx.GROW, proportion=1)
        self.error_panel = ErrorPanel(self)
        self.sizer.Add(self.error_panel, flag=wx.GROW, proportion=1)
        self.SetSizer(self.sizer)

    def _show_panel(self, panel):
        # Hide all panels
        for panel_to_hide in [self.welcome_panel, self.timeline_panel,
                              self.error_panel]:
            panel_to_hide.Show(False)
        # Show this one
        panel.Show(True)
        self.sizer.Layout()


class WelcomePanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self._create_gui()

    def _create_gui(self):
        vsizer = wx.BoxSizer(wx.VERTICAL)
        # Text 1
        t1 = wx.StaticText(self, label=_("No timeline opened."))
        vsizer.Add(t1, flag=wx.ALIGN_CENTER_HORIZONTAL)
        # Spacer
        vsizer.AddSpacer(20)
        # Text 2
        t2 = wx.StaticText(self, label=_("First time using Timeline?"))
        vsizer.Add(t2, flag=wx.ALIGN_CENTER_HORIZONTAL)
        # Button
        btn_tutorial = HyperlinkButton(self, _("Getting started tutorial"))
        self.Bind(wx.EVT_HYPERLINK, self._btn_tutorial_on_click, btn_tutorial)
        vsizer.Add(btn_tutorial, flag=wx.ALIGN_CENTER_HORIZONTAL)
        # Sizer
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(vsizer, flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, proportion=1)
        self.SetSizer(hsizer)

    def _btn_tutorial_on_click(self, e):
        help_browser.show_page("tutorial")


class TimelinePanel(wx.Panel):
    """Showing the drawn timeline and the optional sidebar."""

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.sidebar_width = config.get_sidebar_width()
        self._create_gui()
        self.show_sidebar()
        if not config.get_show_sidebar():
            self.hide_sidebar()

    def get_sidebar_width(self):
        return self.sidebar_width

    def show_sidebar(self):
        self.splitter.SplitVertically(self.sidebar, self.drawing_area,
                                      self.sidebar_width)

    def hide_sidebar(self):
        self.splitter.Unsplit(self.sidebar)

    def _create_gui(self):
        self.splitter = wx.SplitterWindow(self, style=wx.SP_LIVE_UPDATE)
        self.splitter.SetMinimumPaneSize(50)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED,
                  self._splitter_on_splitter_sash_pos_changed, self.splitter)
        self.sidebar = Sidebar(self.splitter)
        self.divider_line_slider = wx.Slider(self, value = 50, size = (20, -1),
                                             style = wx.SL_LEFT | wx.SL_VERTICAL)
        self.drawing_area = DrawingArea(self.splitter, self.divider_line_slider)
        globalSizer = wx.BoxSizer(wx.HORIZONTAL)
        globalSizer.Add(self.splitter, 1, wx.EXPAND)
        globalSizer.Add(self.divider_line_slider, 0, wx.EXPAND)
        self.SetSizer(globalSizer)

    def _splitter_on_splitter_sash_pos_changed(self, e):
        self.sidebar_width = self.splitter.GetSashPosition()


class Sidebar(wx.Panel):
    """
    The left part in TimelinePanel.

    Currently only shows the categories with visibility check boxes.
    """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.BORDER_NONE)
        self._create_gui()

    def _create_gui(self):
        self.catbox = CategoriesVisibleCheckListBox(self)
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.catbox, flag=wx.GROW, proportion=1)
        self.SetSizer(sizer)


class CategoriesVisibleCheckListBox(wx.CheckListBox):
    # ClientData can not be used in this control
    # (see http://docs.wxwidgets.org/stable/wx_wxchecklistbox.html)
    # This workaround will not work if items are reordered

    def __init__(self, parent):
        wx.CheckListBox.__init__(self, parent)
        self.timeline = None
        self.Bind(wx.EVT_CHECKLISTBOX, self._checklistbox_on_checklistbox, self)

    def set_timeline(self, timeline):
        if self.timeline != None:
            self.timeline.unregister(self._timeline_changed)
        self.timeline = timeline
        if self.timeline:
            self.timeline.register(self._timeline_changed)
            self._update_categories()
        else:
            self.Clear()

    def _checklistbox_on_checklistbox(self, e):
        i = e.GetSelection()
        self.categories[i].visible = self.IsChecked(i)
        try:
            self.timeline.save_category(self.categories[i])
        except TimelineIOError, e:
            wx.GetTopLevelParent(self).handle_timeline_error(e)

    def _timeline_changed(self, state_change):
        if state_change == STATE_CHANGE_CATEGORY:
            self._update_categories()

    def _update_categories(self):
        try:
            self.categories = sort_categories(self.timeline.get_categories())
        except TimelineIOError, e:
            wx.GetTopLevelParent(self).handle_timeline_error(e)
        else:
            self.Clear()
            self.AppendItems([category.name for category in self.categories])
            for i in range(0, self.Count):
                if self.categories[i].visible:
                    self.Check(i)
                self.SetItemBackgroundColour(i, self.categories[i].color)

class EventSizer(object):
    """Objects of this class are used to simplify resizing of events."""

    _singletons = {}
    _initialized = False
    
    def __new__(cls, *args, **kwds):
        """Implement the Singleton pattern for this class."""
        if cls not in cls._singletons:
            cls._singletons[cls] = super(EventSizer, cls).__new__(cls)
        return cls._singletons[cls]    
    
    def __init__(self, drawing_area, m_x = 0, m_y = 0):
        if not EventSizer._initialized:
            self.direction = wx.LEFT
            self.drawing_area = drawing_area
            self.metrics = self.drawing_area.drawing_algorithm.metrics
            self.sizing = False
            self.event = None
            EventSizer._initialized = True
        self.metrics = self.drawing_area.drawing_algorithm.metrics

    def sizing_starts(self, m_x, m_y):
        """
        If it is ok to start a resize... initialize the resize and return True.
        Otherwise return False.
        """
        self.sizing = (self._hit(m_x, m_y) and 
                       self.drawing_area.event_rt_data.is_selected(self.event))
        if self.sizing:
            self.x = m_x
            self.y = m_y
        return self.sizing

    def is_sizing(self):
        """Return True if we are in a resizing state, otherwise return False."""
        return self.sizing

    def set_cursor(self, m_x, m_y):
        """
        Used in mouse-move events to set the size cursor before the left mouse
        button is pressed, to indicate that a resize is possible (if it is!).
        Return True if the size-indicator-cursor is set, otherwise return False.
        """
        hit = self._hit(m_x, m_y)
        if hit:
            is_selected = self.drawing_area.event_rt_data.is_selected(self.event)
            if not is_selected:
                return False
            self.drawing_area._set_size_cursor()
        else:
            self.drawing_area._set_default_cursor()
        return hit

    def _hit(self, m_x, m_y):
        """
        Calculate the 'hit-for-resize' coordinates and return True if
        the mouse is within this area. Otherwise return False.
        The 'hit-for-resize' area is the are at the left and right edges of the
        event rectangle with a width of HIT_REGION_PX_WITH.
        """
        event_info = self.drawing_area.drawing_algorithm.event_with_rect_at(m_x, m_y)
        if event_info == None:
            return False
        self.event, rect = event_info
        if abs(m_x - rect.X) < HIT_REGION_PX_WITH:
            self.direction = wx.LEFT
            return True
        elif abs(rect.X + rect.Width - m_x) < HIT_REGION_PX_WITH:
            self.direction = wx.RIGHT
            return True
        return False

    def resize(self, m_x, m_y):
        """
        Resize the event either on the left or the right side.
        The event edge is snapped to the grid.
        """
        time = self.metrics.get_time(m_x)
        time = self.drawing_area.drawing_algorithm.snap(time)
        resized = False
        if self.direction == wx.LEFT:
            resized = self.event.update_start(time)
        else:
            resized = self.event.update_end(time)
        if resized:
            self.drawing_area._redraw_timeline()

class EventMover(object):
    """Objects of this class are used to simplify moving of events."""

    _singletons = {}
    _initialized = False
    
    def __new__(cls, *args, **kwds):
        """Implement the Singleton pattern for this class."""
        if cls not in cls._singletons:
            cls._singletons[cls] = super(EventMover, cls).__new__(cls)
        return cls._singletons[cls]    
    
    def __init__(self, drawing_area):
        """Initialize only the first time the class constructor is called."""
        if not EventMover._initialized:
            self.drawing_area = drawing_area
            self.drawing_algorithm = self.drawing_area.drawing_algorithm
            self.moving = False
            self.event = None
            EventMover._initialized = True

    def move_starts(self, m_x, m_y):
        """
        If it is ok to start a move... initialize the move and return True.
        Otherwise return False.
        """
        self.moving = (self._hit(m_x, m_y) and 
                       self.drawing_area.event_rt_data.is_selected(self.event))
        if self.moving:
            self.x = m_x
            self.y = m_y
        return self.moving
        
    def is_moving(self):
        """Return True if we are in a moving state, otherwise return False."""
        return self.moving

    def set_cursor(self, m_x, m_y):
        """
        Used in mouse-move events to set the move cursor before the left mouse
        button is pressed, to indicate that a move is possible (if it is!).
        Return True if the move-indicator-cursor is set, otherwise return False.
        """
        hit = self._hit(m_x, m_y)
        if hit:
            is_selected = self.drawing_area.event_rt_data.is_selected(self.event) 
            if not is_selected:
                return False
            self.drawing_area._set_move_cursor()
        else:
            self.drawing_area._set_default_cursor()
        return hit

    def move(self, m_x, m_y):
        """
        Move the event the time distance, difftime, represented by the distance the
        mouse has moved since the last move (m_x - self.x).
        Events found above the center line are snapped to the grid.
        """
        difftime = self.drawing_algorithm.metrics.get_difftime(m_x, self.x)
        # Snap events found above the center line
        start = self.event.time_period.start_time + difftime
        end = self.event.time_period.end_time + difftime
        if not self.drawing_algorithm.event_is_period(self.event.time_period):
            halfperiod = (end - start) / 2
            middletime = self.drawing_algorithm.snap(start + halfperiod)
            start = middletime - halfperiod
            end = middletime + halfperiod
        else:
            width = start - end
            startSnapped = self.drawing_area.drawing_algorithm.snap(start)
            endSnapped = self.drawing_area.drawing_algorithm.snap(end)
            if startSnapped != start:
                # Prefer to snap at left edge (in case end snapped as well)
                start = startSnapped
                end = start - width
            elif endSnapped != end:
                end = endSnapped
                start = end + width
        # Update and redraw the event
        self.event.update_period(start, end)
        self.drawing_area._redraw_timeline()
        # Adjust the coordinates  to get a smooth movement of cursor and event.
        # We can't use event_with_rect_at() method to get hold of the rect since
        # events can jump over each other when moved.
        rect = self.drawing_algorithm.event_rect(self.event)
        if rect != None:
            self.x = rect.X + rect.Width / 2
        else:
            self.x = m_x
        self.y = m_y

    def _hit(self, m_x, m_y):
        """
        Calculate the 'hit-for-move' coordinates and return True if
        the mouse is within this area. Otherwise return False.
        The 'hit-for-move' area is the are at the center of an event
        with a width of 2 * HIT_REGION_PX_WITH.
        """
        event_info = self.drawing_area.drawing_algorithm.event_with_rect_at(m_x, m_y)
        if event_info == None:
            return False
        self.event, rect = event_info
        center = rect.X + rect.Width / 2
        if abs(m_x - center) <= HIT_REGION_PX_WITH:
            return True
        return False

class DrawingArea(wx.Panel):
    """
    The right part in TimelinePanel: a window on which the timeline is drawn.

    This class has information about what timeline and what part of the
    timeline to draw and makes sure that the timeline is redrawn whenever it is
    needed.

    Double buffering is used to avoid flicker while drawing. This is
    accomplished by always drawing to a background buffer: bgbuf. The paint
    method of the control thus only draws the background buffer to the screen.

    Scrolling and zooming of the timeline is implemented in this class. This is
    done whenever the mouse wheel is scrolled (_window_on_mousewheel).
    Moving also takes place when the mouse is dragged while pressing the left
    mouse key (_window_on_motion).

    Selection of a period on the timeline (period = any number of minor strips)
    is also implemented in this class. A selection is done in the following
    way: Press and hold down the Control key on the keyboard, move the mouse to
    the first minor strip to be selected and then press and hold down the left
    mouse key. Now, while moving the mouse over the timeline, the minor strips
    will be selected.

    What happens is that when the left mouse button is pressed
    (_window_on_left_down) the variable self._current_time is set to the
    time on the timeline where the mouse is. This is the anchor point for the
    selection. When the mouse is moved (_window_on_motion) and left mouse button
    is pressed and the Control key is held down the method
    self._mark_selected_minor_strips(evt.m_x) is called. This method marks all
    minor strips between the anchor point and the current point (evt.m_x).
    When the mouse button is released the selection ends.
    """

    def __init__(self, parent, divider_line_slider):
        wx.Panel.__init__(self, parent, style=wx.NO_BORDER)
        self.divider_line_slider = divider_line_slider
        self._create_gui()
        self._set_initial_values_to_member_variables()
        self._set_colors_and_styles()
        self.timeline = None
        self.printData = wx.PrintData()
        self.printData.SetPaperId(wx.PAPER_A4)
        self.printData.SetPrintMode(wx.PRINT_MODE_PRINTER)
        self.printData.SetOrientation(wx.LANDSCAPE)
        self.event_rt_data = EventRuntimeData()
        logging.debug("Init done in DrawingArea")

    def print_timeline(self, event):
        pdd = wx.PrintDialogData(self.printData)
        pdd.SetToPage(1)
        printer = wx.Printer(pdd)
        printout = printing.TimelinePrintout(self, False)
        frame = wx.GetApp().GetTopWindow()
        if not printer.Print(frame, printout, True):
            if printer.GetLastError() == wx.PRINTER_ERROR:
                wx.MessageBox(_("There was a problem printing.\nPerhaps your current printer is not set correctly?"), _("Printing"), wx.OK)
        else:
            self.printData = wx.PrintData( printer.GetPrintDialogData().GetPrintData() )
        printout.Destroy()

    def print_preview(self, event):
        data = wx.PrintDialogData(self.printData)
        printout_preview  = printing.TimelinePrintout(self, True)
        printout = printing.TimelinePrintout(self, False)
        self.preview = wx.PrintPreview(printout_preview, printout, data)
        if not self.preview.Ok():
            logging.debug("Problem with preview dialog...\n")
            return
        frame = wx.GetApp().GetTopWindow()
        pfrm = wx.PreviewFrame(self.preview, frame, _("Print preview"))
        pfrm.Initialize()
        pfrm.SetPosition(frame.GetPosition())
        pfrm.SetSize(frame.GetSize())
        pfrm.Show(True)

    def print_setup(self, event):
        psdd = wx.PageSetupDialogData(self.printData)
        psdd.CalculatePaperSizeFromId()
        dlg = wx.PageSetupDialog(self, psdd)
        dlg.ShowModal()
        # this makes a copy of the wx.PrintData instead of just saving
        # a reference to the one inside the PrintDialogData that will
        # be destroyed when the dialog is destroyed
        self.printData = wx.PrintData( dlg.GetPageSetupData().GetPrintData() )
        dlg.Destroy()

    def set_timeline(self, timeline):
        """Inform what timeline to draw."""
        if self.timeline != None:
            self.timeline.unregister(self._timeline_changed)
        self.timeline = timeline
        if self.timeline:
            self.timeline.register(self._timeline_changed)
            try:
                self.time_period = timeline.get_preferred_period()
            except TimelineIOError, e:
                wx.GetTopLevelParent(self).handle_timeline_error(e)
                return
            self._redraw_timeline()
            self.Enable()
            self.SetFocus()
        else:
            self.Disable()

    def show_hide_legend(self, show):
        self.show_legend = show
        if self.timeline:
            self._redraw_timeline()

    def get_time_period(self):
        """Return currently displayed time period."""
        if self.timeline == None:
            raise Exception(_("No timeline set"))
        return self.time_period

    def navigate_timeline(self, navigation_fn):
        """
        Perform a navigation operation followed by a redraw.

        The navigation_fn should take one argument which is the time period
        that should be manipulated in order to carry out the navigation
        operation.

        Should the navigation operation fail (max zoom level reached, etc) a
        message will be displayed in the statusbar.

        Note: The time period should never be modified directly. This method
        should always be used instead.
        """
        if self.timeline == None:
            raise Exception(_("No timeline set"))
        try:
            navigation_fn(self.time_period)
            self._redraw_timeline()
            wx.GetTopLevelParent(self).SetStatusText("")
        except (ValueError, OverflowError), e:
            wx.GetTopLevelParent(self).SetStatusText(e.message)

    def _create_gui(self):
        self.Bind(wx.EVT_SIZE, self._window_on_size)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self._window_on_erase_background)
        self.Bind(wx.EVT_PAINT, self._window_on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self._window_on_left_down)
        self.Bind(wx.EVT_RIGHT_DOWN, self._window_on_right_down)
        self.Bind(wx.EVT_LEFT_DCLICK, self._window_on_left_dclick)
        self.Bind(wx.EVT_LEFT_UP, self._window_on_left_up)
        self.Bind(wx.EVT_MOTION, self._window_on_motion)
        self.Bind(wx.EVT_MOUSEWHEEL, self._window_on_mousewheel)
        self.Bind(wx.EVT_KEY_DOWN, self._window_on_key_down)
        self.Bind(wx.EVT_KEY_UP, self._window_on_key_up)
        self.divider_line_slider.Bind(wx.EVT_SLIDER, self._slider_on_slider)
        self.divider_line_slider.Bind(wx.EVT_CONTEXT_MENU,
                                      self._slider_on_context_menu)

    def _window_on_size(self, event):
        """
        Event handler used when the window has been resized.

        Called at the application start and when the frame is resized.

        Here we create a new background buffer with the new size and draw the
        timeline onto it.
        """
        logging.debug("Resize event in DrawingArea: %s", self.GetSizeTuple())
        width, height = self.GetSizeTuple()
        self.bgbuf = wx.EmptyBitmap(width, height)
        self._redraw_timeline()

    def _window_on_erase_background(self, event):
        # For double buffering
        pass

    def _window_on_paint(self, event):
        """
        Event handler used when the window needs repainting.

        Called at the application start, after resizing, or when the window
        becomes active.

        Here we just draw the background buffer onto the screen.

        Defining a dc is crucial. Even if it is not used.
        """
        logging.debug("Paint event in DrawingArea")
        dc = wx.AutoBufferedPaintDC(self)
        dc.BeginDrawing()
        dc.DrawBitmap(self.bgbuf, 0, 0, True)
        dc.EndDrawing()

    def _window_on_left_down(self, evt):
        """
        Event handler used when the left mouse button has been pressed.

        This event establishes a new current time on the timeline.

        If the mouse hits an event that event will be selected.
        """
        try:
            logging.debug("Left mouse pressed event in DrawingArea")
            self._set_new_current_time(evt.m_x)
            # If we hit the event resize area of an event, start resizing
            if EventSizer(self).sizing_starts(evt.m_x, evt.m_y):
                return
            # If we hit the event move area of an event, start moving
            if EventMover(self).move_starts(evt.m_x, evt.m_y):
                return
            # No resizing or moving of events...
            if not self.timeline.is_read_only():
                posAtEvent = self._toggle_event_selection(evt.m_x, evt.m_y,
                                                          evt.m_controlDown)
                if not posAtEvent:
                    if evt.m_controlDown:
                        self._set_select_period_cursor()
            evt.Skip()
        except TimelineIOError, e:
            wx.GetTopLevelParent(self).handle_timeline_error(e)

    def _window_on_right_down(self, evt):
        """
        Event handler used when the right mouse button has been pressed.

        If the mouse hits an event and the timeline is not readonly, the 
        context menu for that event is displayed.
        """
        if self.timeline.is_read_only():
            return
        self.context_menu_event = self.drawing_algorithm.event_at(evt.m_x, evt.m_y)
        if self.context_menu_event == None:
            return
        menu_definitions = (
            ("Edit", self._context_menu_on_edit_event),
            ("Delete", self._context_menu_on_delete_event),
        )
        menu = wx.Menu()
        for menu_definition in menu_definitions:
            text, method = menu_definition
            menu_item = wx.MenuItem(menu, wx.NewId(), text)
            self.Bind(wx.EVT_MENU, method, id=menu_item.GetId())
            menu.AppendItem(menu_item)
        self.PopupMenu(menu)
        menu.Destroy()
        
    def _context_menu_on_edit_event(self, evt):
        frame = wx.GetTopLevelParent(self)
        frame.edit_event(self.context_menu_event)
        
    def _context_menu_on_delete_event(self, evt):
        self.context_menu_event.selected = True
        self._delete_selected_events()
    
    def _window_on_left_dclick(self, evt):
        """
        Event handler used when the left mouse button has been double clicked.

        If the timeline is readonly, no action is taken.
        If the mouse hits an event, a dialog opens for editing this event. 
        Otherwise a dialog for creating a new event is opened.
        """
        logging.debug("Left Mouse doubleclicked event in DrawingArea")
        if self.timeline.is_read_only():
            return
        # Since the event sequence is, 1. EVT_LEFT_DOWN  2. EVT_LEFT_UP
        # 3. EVT_LEFT_DCLICK we must compensate for the toggle_event_selection
        # that occurs in the handling of EVT_LEFT_DOWN, since we still want
        # the event(s) selected or deselected after a left doubleclick
        # It doesn't look too god but I havent found any other way to do it.
        self._toggle_event_selection(evt.m_x, evt.m_y, evt.m_controlDown)
        event = self.drawing_algorithm.event_at(evt.m_x, evt.m_y)
        if event:
            wx.GetTopLevelParent(self).edit_event(event)
        else:
            wx.GetTopLevelParent(self).create_new_event(self._current_time,
                                                        self._current_time)

    def _window_on_left_up(self, evt):
        """
        Event handler used when the left mouse button has been released.

        If there is an ongoing selection-marking, the dialog for creating an
        event will be opened, and the selection-marking will be ended.
        """
        logging.debug("Left mouse released event in DrawingArea")
        if self.is_selecting:
            self._end_selection_and_create_event(evt.m_x)
        self.is_selecting = False
        self.is_scrolling = False
        self._set_default_cursor()

    def _window_on_motion(self, evt):
        """
        Event handler used when the mouse has been moved.

        If the mouse is over an event, the name of that event will be printed
        in the status bar.

        If the left mouse key is down one of two things happens depending on if
        the Control key is down or not. If it is down a selection-marking takes
        place and the minor strips passed by the mouse will be selected.  If
        the Control key is up the timeline will scroll.
        """
        logging.debug("Mouse move event in DrawingArea")
        if evt.m_leftDown:
            self._mouse_drag(evt.m_x, evt.m_y, evt.m_controlDown)
        else:
            if not evt.m_controlDown:
                self._mouse_move(evt.m_x, evt.m_y)                
                
    def _mouse_drag(self, x, y, ctrl=False):
        """
        The mouse has been moved.
        The left mouse button is depressed
        ctrl indicates if the Ctrl-key is depressed or not
        """
        if self.is_scrolling:
            self._scroll(x)
        elif self.is_selecting:
            self._mark_selected_minor_strips(x)
        # Resizing is only allowed if timeline is not readonly    
        elif EventSizer(self).is_sizing() and not self.timeline.is_read_only():
            EventSizer(self).resize(x, y)
        # Moving is only allowed if timeline is not readonly    
        elif EventMover(self).is_moving() and not self.timeline.is_read_only():
            EventMover(self).move(x, y)
        else:
            # Marking strips is only allowed if timeline is not readonly    
            if ctrl and not self.timeline.is_read_only():
                self._mark_selected_minor_strips(x)
                self.is_selecting = True
            else:
                self._scroll(x)
                self.is_scrolling = True
    
    def _mouse_move(self, x, y):
        """
        The mouse has been moved.
        The left mouse button is not depressed
        The Ctrl-key is not depressed
        """
        self._display_balloon_on_hoover(x, y)
        self._display_eventinfo_in_statusbar(x, y)
        cursor_set = EventSizer(self).set_cursor(x, y)
        if not cursor_set:
            EventMover(self).set_cursor(x, y)
                
    def _window_on_mousewheel(self, evt):
        """
        Event handler used when the mouse wheel is rotated.

        If the Control key is pressed at the same time as the mouse wheel is
        scrolled the timeline will be zoomed, otherwise it will be scrolled.
        """
        logging.debug("Mouse wheel event in DrawingArea")
        direction = _step_function(evt.m_wheelRotation)
        if evt.ControlDown():
            self._zoom_timeline(direction)
        else:
            delta = mult_timedelta(self.time_period.delta(), direction / 10.0)
            self._scroll_timeline(delta)

    def _window_on_key_down(self, evt):
        """
        Event handler used when a keyboard key has been pressed.

        The following keys are handled:
        Key         Action
        --------    ------------------------------------
        Delete      Delete any selected event(s)
        Control     Change cursor
        """
        logging.debug("Key down event in DrawingArea")
        keycode = evt.GetKeyCode()
        if keycode == wx.WXK_DELETE:
            self._delete_selected_events()
        evt.Skip()

    def _window_on_key_up(self, evt):
        keycode = evt.GetKeyCode()
        if keycode == wx.WXK_CONTROL:
            self._set_default_cursor()

    def _slider_on_slider(self, evt):
        """The divider-line slider has been moved."""
        self._redraw_timeline()

    def _slider_on_context_menu(self, evt):
        """A right click has occured in the divider-line slider."""
        menu = wx.Menu()
        menu_item = wx.MenuItem(menu, wx.NewId(), _("Center"))
        self.Bind(wx.EVT_MENU, self._context_menu_on_menu_center,
                  id=menu_item.GetId())
        menu.AppendItem(menu_item)
        self.PopupMenu(menu)
        menu.Destroy()

    def _context_menu_on_menu_center(self, evt):
        """The 'Center' context menu has been selected."""
        self.divider_line_slider.SetValue(50)
        self._redraw_timeline()

    def _timeline_changed(self, state_change):
        if state_change == STATE_CHANGE_ANY:
            self._redraw_timeline()

    def _set_initial_values_to_member_variables(self):
        """
        Instance variables usage:

        _current_time       This variable is set to the time on the timeline
                            where the mouse button is clicked when the left
                            mouse button is used
        _mark_selection     Processing flag indicating ongoing selection of a
                            time period
        timeline            The timeline currently handled by the application
        time_period         The part of the timeline currently displayed in the
                            drawing area
        drawing_algorithm   The algorithm used to draw the timeline
        bgbuf               The bitmap to which the drawing methods draw the
                            timeline. When the EVT_PAINT occurs this bitmap
                            is painted on the screen. This is a buffer drawing
                            approach for avoiding screen flicker.
        is_scrolling        True when scrolling with the mouse takes place.
                            It is set True in mouse_has_moved and set False
                            in left_mouse_button_released.
        is_selecting        True when selecting with the mouse takes place
                            It is set True in mouse_has_moved and set False
                            in left_mouse_button_released.
        show_balloons_on_hover Show ballons on mouse hoover without clicking
        """
        self._current_time = None
        self._mark_selection = False
        self.bgbuf = None
        self.timeline = None
        self.time_period = None
        self.drawing_algorithm = get_drawer()
        self.is_scrolling = False
        self.is_selecting = False
        self.show_legend = config.get_show_legend()
        self.show_balloons_on_hover = config.get_balloon_on_hover()

    def _set_colors_and_styles(self):
        """Define the look and feel of the drawing area."""
        self.SetBackgroundColour(wx.WHITE)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self._set_default_cursor()
        self.Disable()

    def _redraw_timeline(self, period_selection=None):
        """Draw the timeline onto the background buffer."""
        logging.debug("Draw timeline to bgbuf")
        memdc = wx.MemoryDC()
        memdc.SelectObject(self.bgbuf)
        try:
            memdc.BeginDrawing()
            memdc.SetBackground(wx.Brush(wx.WHITE, wx.SOLID))
            memdc.Clear()
            if self.timeline:
                try:
                    settings = DrawingHints()
                    settings.period_selection = period_selection
                    settings.draw_legend = self.show_legend
                    settings.divider_position = (
                        self.divider_line_slider.GetValue())
                    settings.divider_position = (
                        float(self.divider_line_slider.GetValue()) / 100.0)
                    self.drawing_algorithm.draw(memdc, self.time_period,
                                                self.timeline,
                                                settings,
                                                self.event_rt_data)
                except TimelineIOError, e:
                    wx.GetTopLevelParent(self).handle_timeline_error(e)
            memdc.EndDrawing()
            del memdc
            self.Refresh()
            self.Update()
        except Exception, ex:
            self.bgbuf = None
            logging.fatal("Error in drawing", exc_info=ex)

    def _scroll(self, xpixelpos):
        if self._current_time:
            delta = (self.drawing_algorithm.metrics.get_time(xpixelpos) -
                        self._current_time)
            self._scroll_timeline(delta)

    def _set_new_current_time(self, current_x):
        self._current_time = self.drawing_algorithm.metrics.get_time(current_x)
        logging.debug("Marked time " + self._current_time.isoformat("-"))

    def _toggle_event_selection(self, xpixelpos, ypixelpos, control_down):
        """
        If the given position is within the boundaries of an event that event
        will be selected or unselected depending on the current selection
        state of the event. If the Control key is down all other events
        selection state are preserved. This means that previously selected
        events will stay selected. If the Control key is not down all other
        events will be unselected.

        If the given position isn't within an event all selected events will
        be unselected.

        Return True if the given position was within an event, otherwise
        return False.
        """
        event = self.drawing_algorithm.event_at(xpixelpos, ypixelpos)
        if event:
            selected = not self.event_rt_data.is_selected(event)
            if not control_down:
                self.event_rt_data.clear_selected()
            self.event_rt_data.set_selected(event, selected)
        else:
            self.event_rt_data.clear_selected()
        self._redraw_timeline()
        return event != None

    def _end_selection_and_create_event(self, current_x):
        self._mark_selection = False
        period_selection = self._get_period_selection(current_x)
        start, end = period_selection
        wx.GetTopLevelParent(self).create_new_event(start, end)
        self._redraw_timeline()

    def _display_eventinfo_in_statusbar(self, xpixelpos, ypixelpos):
        """
        If the given position is within the boundaries of an event, the name of
        that event will be displayed in the status bar, otherwise the status
        bar text will be removed.
        """
        event = self.drawing_algorithm.event_at(xpixelpos, ypixelpos)
        if event != None:
            self._display_text_in_statusbar(event.get_label())
        else:
            self._reset_text_in_statusbar()
            
    def _display_balloon_on_hoover(self, xpixelpos, ypixelpos):
        event = self.drawing_algorithm.event_at(xpixelpos, ypixelpos)
        if self.show_balloons_on_hover:
            if event and not self.event_rt_data.is_selected(event):
                self.event_just_hoverd = event    
                self.timer = wx.Timer(self, -1)
                self.Bind(wx.EVT_TIMER, self.on_balloon_timer, self.timer)
                self.timer.Start(milliseconds=500, oneShot=True)
            else:
                self.event_just_hoverd = None
                self.redraw_balloons(None)
                
    def on_balloon_timer(self, event):
        self.redraw_balloons(self.event_just_hoverd)
   
    def redraw_balloons(self, event):
        if event:
            self.event_rt_data.set_balloon(event)
        else:    
            self.event_rt_data.clear_balloons()
        self._redraw_timeline()
        
    def _mark_selected_minor_strips(self, current_x):
        """Selection-marking starts or continues."""
        self._mark_selection = True
        period_selection = self._get_period_selection(current_x)
        self._redraw_timeline(period_selection)

    def _scroll_timeline(self, delta):
        self.navigate_timeline(lambda tp: tp.move_delta(-delta))

    def _zoom_timeline(self, direction=0):
        self.navigate_timeline(lambda tp: tp.zoom(direction))

    def _delete_selected_events(self):
        """After acknowledge from the user, delete all selected events."""
        selected_event_ids = self.event_rt_data.get_selected_event_ids()
        nbr_of_selected_event_ids = len(selected_event_ids)
        if nbr_of_selected_event_ids > 1:
            text = _("Are you sure to delete %d events?" % 
                     nbr_of_selected_event_ids)
        else:
            text = _("Are you sure to delete?")
        if _ask_question(text, self) == wx.YES:
            try:
                for event_id in selected_event_ids:
                    self.timeline.delete_event(event_id)
            except TimelineIOError, e:
                wx.GetTopLevelParent(self).handle_timeline_error(e)

    def _get_period_selection(self, current_x):
        """Return a tuple containing the start and end time of a selection."""
        start = self._current_time
        end   = self.drawing_algorithm.metrics.get_time(current_x)
        if start > end:
            start, end = end, start
        period_selection = self.drawing_algorithm.snap_selection((start,end))
        return period_selection

    def _display_text_in_statusbar(self, text):
        wx.GetTopLevelParent(self).SetStatusText(text)

    def _reset_text_in_statusbar(self):
        wx.GetTopLevelParent(self).SetStatusText("")

    def _set_select_period_cursor(self):
        self.SetCursor(wx.StockCursor(wx.CURSOR_IBEAM))

    def _set_drag_cursor(self):
        self.SetCursor(wx.StockCursor(wx.CURSOR_HAND))

    def _set_size_cursor(self):
        self.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))

    def _set_move_cursor(self):
        self.SetCursor(wx.StockCursor(wx.CURSOR_SIZING))

    def _set_default_cursor(self):
        """
        Set the cursor to it's default shape when it is in the timeline
        drawing area.
        """
        self.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

    def balloon_visibility_changed(self, visible):
        self.show_balloons_on_hover = visible
        # When display on hovering is disabled we have to make sure 
        # that any visible balloon is removed.
        if not visible:
            self.drawing_algorithm.notify_events(
                            1, None)
            self._redraw_timeline()

class ErrorPanel(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self._create_gui()

    def populate(self, error):
        self.txt_error.SetLabel(error.message)

    def _create_gui(self):
        vsizer = wx.BoxSizer(wx.VERTICAL)
        # Error text
        self.txt_error = wx.StaticText(self, label="")
        vsizer.Add(self.txt_error, flag=wx.ALIGN_CENTER_HORIZONTAL)
        # Spacer
        vsizer.AddSpacer(20)
        # Help text
        txt_help = wx.StaticText(self, label=_("Relevant help topics:"))
        vsizer.Add(txt_help, flag=wx.ALIGN_CENTER_HORIZONTAL)
        # Button
        btn_contact = HyperlinkButton(self, _("Contact"))
        self.Bind(wx.EVT_HYPERLINK, self._btn_contact_on_click, btn_contact)
        vsizer.Add(btn_contact, flag=wx.ALIGN_CENTER_HORIZONTAL)
        # Sizer
        hsizer = wx.BoxSizer(wx.HORIZONTAL)
        hsizer.Add(vsizer, flag=wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, proportion=1)
        self.SetSizer(hsizer)

    def _btn_contact_on_click(self, e):
        help_browser.show_page("contact")


class EventEditor(wx.Dialog):
    """Dialog used for creating and editing events."""

    def __init__(self, parent, title, timeline,
                 start=None, end=None, event=None):
        """
        Create a event editor dialog.

        The 'event' argument is optional. If it is given the dialog is used
        to edit this event and the controls are filled with data from
        the event and the arguments 'start' and 'end' are ignored.

        If the 'event' argument isn't given the dialog is used to create a
        new event, and the controls for start and end time are initially
        filled with data from the arguments 'start' and 'end' if they are
        given. Otherwise they will default to today.
        """
        wx.Dialog.__init__(self, parent, title=title,
                           style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER)
        self.timeline = timeline
        self.event = event
        self._create_gui()
        self._fill_controls_with_data(start, end)
        self._set_initial_focus()

    def _create_gui(self):
        """Create the controls of the dialog."""
        # Groupbox
        groupbox = wx.StaticBox(self, wx.ID_ANY, _("Event Properties"))
        groupbox_sizer = wx.StaticBoxSizer(groupbox, wx.VERTICAL)
        # Grid
        grid = wx.FlexGridSizer(4, 2, BORDER, BORDER)
        grid.AddGrowableCol(1)
        # Grid: When: Label + DateTimePickers
        grid.Add(wx.StaticText(self, label=_("When:")),
                 flag=wx.ALIGN_CENTER_VERTICAL)
        self.dtp_start = DateTimePicker(self)
        self.lbl_to = wx.StaticText(self, label=_("to"))
        self.dtp_end = DateTimePicker(self)
        when_box = wx.BoxSizer(wx.HORIZONTAL)
        when_box.Add(self.dtp_start, proportion=1)
        when_box.AddSpacer(BORDER)
        when_box.Add(self.lbl_to, flag=wx.ALIGN_CENTER_VERTICAL|wx.RESERVE_SPACE_EVEN_IF_HIDDEN)
        when_box.AddSpacer(BORDER)
        when_box.Add(self.dtp_end, proportion=1,
                     flag=wx.RESERVE_SPACE_EVEN_IF_HIDDEN)
        grid.Add(when_box)
        # Grid: When: Checkboxes
        grid.AddStretchSpacer()
        when_box_props = wx.BoxSizer(wx.HORIZONTAL)
        self.chb_period = wx.CheckBox(self, label=_("Period"))
        self.Bind(wx.EVT_CHECKBOX, self._chb_period_on_checkbox,
                  self.chb_period)
        when_box_props.Add(self.chb_period)
        self.chb_show_time = wx.CheckBox(self, label=_("Show time"))
        self.Bind(wx.EVT_CHECKBOX, self._chb_show_time_on_checkbox,
                  self.chb_show_time)
        when_box_props.Add(self.chb_show_time)
        grid.Add(when_box_props)
        # Grid: Text
        self.txt_text = wx.TextCtrl(self, wx.ID_ANY)
        grid.Add(wx.StaticText(self, label=_("Text:")),
                 flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.txt_text, flag=wx.EXPAND)
        # Grid: Category
        self.lst_category = wx.Choice(self, wx.ID_ANY)
        grid.Add(wx.StaticText(self, label=_("Category:")),
                 flag=wx.ALIGN_CENTER_VERTICAL)
        grid.Add(self.lst_category)
        groupbox_sizer.Add(grid, flag=wx.ALL|wx.EXPAND, border=BORDER)
        self.Bind(wx.EVT_CHOICE, self._lst_category_on_choice,
                  self.lst_category)
        # Event data
        self.event_data = []
        notebook = wx.Notebook(self, style=wx.BK_DEFAULT)
        for data_id in self.timeline.supported_event_data():
            if data_id == "description":
                name = _("Description")
                editor_class = DescriptionEditor
            elif data_id == "icon":
                name = _("Icon")
                editor_class = IconEditor
            else:
                continue
            panel = wx.Panel(notebook)
            editor = editor_class(panel)
            notebook.AddPage(panel, name)
            sizer = wx.BoxSizer(wx.VERTICAL)
            sizer.Add(editor, flag=wx.EXPAND, proportion=1)
            panel.SetSizer(sizer)
            self.event_data.append((data_id, editor))
        groupbox_sizer.Add(notebook, border=BORDER, flag=wx.ALL|wx.EXPAND,
                           proportion=1)
        # Main (vertical layout)
        main_box = wx.BoxSizer(wx.VERTICAL)
        # Main: Groupbox
        main_box.Add(groupbox_sizer, flag=wx.EXPAND|wx.ALL, border=BORDER,
                     proportion=1)
        # Main: Checkbox
        self.chb_add_more = wx.CheckBox(self, label=_("Add more events after this one"))
        main_box.Add(self.chb_add_more, flag=wx.ALL, border=BORDER)
        # Main: Buttons
        button_box = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)
        self.Bind(wx.EVT_BUTTON, self._btn_ok_on_click, id=wx.ID_OK)
        main_box.Add(button_box, flag=wx.EXPAND|wx.ALL, border=BORDER)
        # Hide if not creating new
        if self.event != None:
            self.chb_add_more.Show(False)
        # Realize
        self.SetSizerAndFit(main_box)

    def _btn_ok_on_click(self, evt):
        """
        Add new or update existing event.

        If the Close-on-ok checkbox is checked the dialog is also closed.
        """
        try:
            logging.debug("_btn_ok_on_click")
            try:
                # Input value retrieval and validation
                start_time = self.dtp_start.get_value()
                end_time = start_time
                if self.chb_period.IsChecked():
                    end_time = self.dtp_end.get_value()
                selection = self.lst_category.GetSelection()
                category = self.lst_category.GetClientData(selection)
                if start_time > end_time:
                    raise TxtException(_("End must be > Start"), self.dtp_start)
                name = _parse_text_from_textbox(self.txt_text, _("Text"))
                # Update existing event
                if self.updatemode:
                    self.event.update(start_time, end_time, name, category)
                    for data_id, editor in self.event_data:
                        self.event.set_data(data_id,
                                            editor.get_data())
                    self.timeline.save_event(self.event)
                # Create new event
                else:
                    self.event = Event(start_time, end_time, name, category)
                    for data_id, editor in self.event_data:
                        self.event.set_data(data_id,
                                            editor.get_data())
                    self.timeline.save_event(self.event)
                # Close the dialog ?
                if self.chb_add_more.GetValue():
                    self.txt_text.SetValue("")
                    for data_id, editor in self.event_data:
                        editor.clear_data(editor)
                else:
                    self._close()
            except TxtException, ex:
                _display_error_message("%s" % ex.error_message)
                _set_focus_and_select(ex.control)
        except TimelineIOError, e:
            _display_error_message(e.message, self)
            self.error = e
            self.EndModal(ID_ERROR)

    def _chb_period_on_checkbox(self, e):
        self._show_to_time(e.IsChecked())

    def _chb_show_time_on_checkbox(self, e):
        self.dtp_start.show_time(e.IsChecked())
        self.dtp_end.show_time(e.IsChecked())

    def _lst_category_on_choice(self, e):
        new_selection_index = e.GetSelection()
        if new_selection_index > self.last_real_category_index:
            self.lst_category.SetSelection(self.current_category_selection)
            if new_selection_index == self.add_category_item_index:
                self._add_category()
            elif new_selection_index == self.edit_categoris_item_index:
                self._edit_categories()
        else:
            self.current_category_selection = new_selection_index

    def _add_category(self):
        try:
            dialog = CategoryEditor(self, _("Add Category"),
                                    self.timeline, None)
        except TimelineIOError, e:
            _display_error_message(e.message, self)
            self.error = e
            self.EndModal(ID_ERROR)
        else:
            dialog_result = dialog.ShowModal()
            if dialog_result == ID_ERROR:
                self.error = dialog.error
                self.EndModal(ID_ERROR)
            elif dialog_result == wx.ID_OK:
                try:
                    self._update_categories(dialog.get_edited_category())
                except TimelineIOError, e:
                    _display_error_message(e.message, self)
                    self.error = e
                    self.EndModal(ID_ERROR)
            dialog.Destroy()

    def _edit_categories(self):
        try:
            dialog = CategoriesEditor(self, self.timeline)
        except TimelineIOError, e:
            _display_error_message(e.message, self)
            self.error = e
            self.EndModal(ID_ERROR)
        else:
            if dialog.ShowModal() == ID_ERROR:
                self.error = dialog.error
                self.EndModal(ID_ERROR)
            else:
                try:
                    prev_index = self.lst_category.GetSelection()
                    prev_category = self.lst_category.GetClientData(prev_index)
                    self._update_categories(prev_category)
                except TimelineIOError, e:
                    _display_error_message(e.message, self)
                    self.error = e
                    self.EndModal(ID_ERROR)
            dialog.Destroy()

    def _show_to_time(self, show=True):
        self.lbl_to.Show(show)
        self.dtp_end.Show(show)

    def _fill_controls_with_data(self, start=None, end=None):
        """Initially fill the controls in the dialog with data."""
        if self.event == None:
            self.chb_period.SetValue(False)
            self.chb_show_time.SetValue(False)
            text = ""
            category = None
            self.updatemode = False
        else:
            start = self.event.time_period.start_time
            end = self.event.time_period.end_time
            text = self.event.text
            category = self.event.category
            for data_id, editor in self.event_data:
                data = self.event.get_data(data_id)
                if data != None:
                    editor.set_data(data)
            self.updatemode = True
        if start != None and end != None:
            self.chb_show_time.SetValue(TimePeriod(start, end).has_nonzero_time())
            self.chb_period.SetValue(start != end)
        self.dtp_start.set_value(start)
        self.dtp_end.set_value(end)
        self.txt_text.SetValue(text)
        self._update_categories(category)
        self.chb_add_more.SetValue(False)
        self._show_to_time(self.chb_period.IsChecked())
        self.dtp_start.show_time(self.chb_show_time.IsChecked())
        self.dtp_end.show_time(self.chb_show_time.IsChecked())

    def _update_categories(self, select_category):
        # We can not do error handling here since this method is also called
        # from the constructor (and then error handling is done by the code
        # calling the constructor).
        self.lst_category.Clear()
        self.lst_category.Append("", None) # The None-category
        selection_set = False
        current_item_index = 1
        for cat in sort_categories(self.timeline.get_categories()):
            self.lst_category.Append(cat.name, cat)
            if cat == select_category:
                self.lst_category.SetSelection(current_item_index)
                selection_set = True
            current_item_index += 1
        self.last_real_category_index = current_item_index - 1
        self.add_category_item_index = self.last_real_category_index + 2
        self.edit_categoris_item_index = self.last_real_category_index + 3
        self.lst_category.Append("", None)
        self.lst_category.Append(_("Add new"), None)
        self.lst_category.Append(_("Edit categories"), None)
        if not selection_set:
            self.lst_category.SetSelection(0)
        self.current_category_selection = self.lst_category.GetSelection()

    def _set_initial_focus(self):
        self.dtp_start.SetFocus()

    def _close(self):
        """
        Close the dialog.

        Make sure that no events are selected after the dialog is closed.
        """
        # TODO: Replace with EventRuntimeData
        #self.timeline.reset_selected_events()
        self.EndModal(wx.ID_OK)


class CategoriesEditor(wx.Dialog):
    """
    Dialog used to edit categories of a timeline.

    The edits happen immediately. In other words: when the dialog is closing
    all edits have been applied already.
    """

    def __init__(self, parent, timeline):
        wx.Dialog.__init__(self, parent, title=_("Edit Categories"))
        self._create_gui()
        self.timeline = timeline
        # Note: We must unregister before we close this dialog. When we close
        # this dialog it will be disposed and self._timeline_changed will no
        # longer exist. The next time the timeline gets updated it will try to
        # call a method that does not exist.
        self.timeline.register(self._timeline_changed)
        self._update_categories()

    def _create_gui(self):
        self.Bind(wx.EVT_CLOSE, self._window_on_close)
        # The list box
        self.lst_categories = wx.ListBox(self, size=(200, 180),
                                         style=wx.LB_SINGLE)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self._lst_categories_on_dclick,
                  self.lst_categories)
        # The Add button
        btn_add = wx.Button(self, wx.ID_ADD)
        self.Bind(wx.EVT_BUTTON, self._btn_add_on_click, btn_add)
        # The Delete button
        btn_del = wx.Button(self, wx.ID_DELETE)
        self.Bind(wx.EVT_BUTTON, self._btn_del_on_click, btn_del)
        # The close button
        btn_close = wx.Button(self, wx.ID_CLOSE)
        btn_close.SetDefault()
        btn_close.SetFocus()
        self.SetAffirmativeId(wx.ID_CLOSE)
        self.Bind(wx.EVT_BUTTON, self._btn_close_on_click, btn_close)
        self.lst_categories.Bind(wx.EVT_KEY_DOWN, self._lst_categories_on_key_down)
        # Setup layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.lst_categories, flag=wx.ALL|wx.EXPAND, border=BORDER)
        button_box = wx.BoxSizer(wx.HORIZONTAL)
        button_box.Add(btn_add, flag=wx.RIGHT, border=BORDER)
        button_box.Add(btn_del, flag=wx.RIGHT, border=BORDER)
        button_box.AddStretchSpacer()
        button_box.Add(btn_close, flag=wx.LEFT, border=BORDER)
        vbox.Add(button_box, flag=wx.ALL|wx.EXPAND, border=BORDER)
        self.SetSizerAndFit(vbox)
        self.lst_categories.SetFocus()

    def _window_on_close(self, e):
        # This will always be called before the dialog closes so we can do the
        # unregister here.
        self.timeline.unregister(self._timeline_changed)
        self.EndModal(wx.ID_CLOSE)

    def _lst_categories_on_dclick(self, e):
        try:
            selection = e.GetSelection()
            dialog = CategoryEditor(self, _("Edit Category"), self.timeline,
                                    e.GetClientData())
        except TimelineIOError, e:
            _display_error_message(e.message, self)
            self.error = e
            self.EndModal(ID_ERROR)
        else:
            if dialog.ShowModal() == ID_ERROR:
                self.error = dialog.error
                self.EndModal(ID_ERROR)
            dialog.Destroy()

    def _btn_add_on_click(self, e):
        try:
            dialog = CategoryEditor(self, _("Add Category"), self.timeline,
                                    None)
        except TimelineIOError, e:
            _display_error_message(e.message, self)
            self.error = e
            self.EndModal(ID_ERROR)
        else:
            if dialog.ShowModal() == ID_ERROR:
                self.error = dialog.error
                self.EndModal(ID_ERROR)
            dialog.Destroy()

    def _btn_del_on_click(self, e):
        try:
            self._delete_selected_category()
        except TimelineIOError, e:
            _display_error_message(e.message, self)
            self.error = e
            self.EndModal(ID_ERROR)

    def _btn_close_on_click(self, e):
        self.Close()

    def _lst_categories_on_key_down(self, e):
        try:
            logging.debug("Key down event in CategoriesEditor")
            keycode = e.GetKeyCode()
            if keycode == wx.WXK_DELETE:
                self._delete_selected_category()
            e.Skip()
        except TimelineIOError, e:
            _display_error_message(e.message, self)
            self.error = e
            self.EndModal(ID_ERROR)

    def _timeline_changed(self, state_change):
        try:
            if state_change == STATE_CHANGE_CATEGORY:
                self._update_categories()
        except TimelineIOError, e:
            _display_error_message(e.message, self)
            self.error = e
            self.EndModal(ID_ERROR)

    def _delete_selected_category(self):
        selection = self.lst_categories.GetSelection()
        if selection != wx.NOT_FOUND:
            if _ask_question(_("Are you sure to delete?"), self) == wx.YES:
                cat = self.lst_categories.GetClientData(selection)
                self.timeline.delete_category(cat)

    def _update_categories(self):
        self.lst_categories.Clear()
        for category in sort_categories(self.timeline.get_categories()):
            self.lst_categories.Append(category.name, category)


class CategoryEditor(wx.Dialog):
    """
    Dialog used to edit a category.

    The edited category can be fetched with get_edited_category.
    """

    def __init__(self, parent, title, timeline, category):
        wx.Dialog.__init__(self, parent, title=title)
        self._create_gui()
        self.timeline = timeline
        self.category = category
        self.create_new = False
        if self.category == None:
            self.create_new = True
            self.category = Category("", (200, 200, 200), True)
        self.txt_name.SetValue(self.category.name)
        self.colorpicker.SetColour(self.category.color)
        self.chb_visible.SetValue(self.category.visible)

    def get_edited_category(self):
        return self.category

    def _create_gui(self):
        # The name text box
        self.txt_name = wx.TextCtrl(self, size=(150, -1))
        # The color chooser
        self.colorpicker = colourselect.ColourSelect(self)
        # The visible check box
        self.chb_visible = wx.CheckBox(self)
        # Setup layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        # Grid for controls
        field_grid = wx.FlexGridSizer(3, 2, BORDER, BORDER)
        field_grid.Add(wx.StaticText(self, label=_("Name:")),
                       flag=wx.ALIGN_CENTER_VERTICAL)
        field_grid.Add(self.txt_name)
        field_grid.Add(wx.StaticText(self, label=_("Color:")),
                       flag=wx.ALIGN_CENTER_VERTICAL)
        field_grid.Add(self.colorpicker)
        field_grid.Add(wx.StaticText(self, label=_("Visible:")),
                       flag=wx.ALIGN_CENTER_VERTICAL)
        field_grid.Add(self.chb_visible)
        vbox.Add(field_grid, flag=wx.EXPAND|wx.ALL, border=BORDER)
        # Buttons
        button_box = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)
        self.Bind(wx.EVT_BUTTON, self._btn_ok_on_click, id=wx.ID_OK)
        vbox.Add(button_box, flag=wx.ALL|wx.EXPAND, border=BORDER)
        self.SetSizerAndFit(vbox)
        _set_focus_and_select(self.txt_name)

    def _btn_ok_on_click(self, e):
        try:
            name = self.txt_name.GetValue().strip()
            if not self._name_valid(name):
                msg = _("Category name '%s' not valid. Must be non-empty.")
                _display_error_message(msg % name, self)
                return
            if self._name_in_use(name):
                msg = _("Category name '%s' already in use.")
                _display_error_message(msg % name, self)
                return
            self.category.name = name
            self.category.color = self.colorpicker.GetColour()
            self.category.visible = self.chb_visible.IsChecked()
            if self.create_new:
                self.timeline.add_category(self.category)
            else:
                self.timeline.save_category(self.category)
            self.EndModal(wx.ID_OK)
        except TimelineIOError, e:
            _display_error_message(e.message, self)
            self.error = e
            self.EndModal(ID_ERROR)

    def _name_valid(self, name):
        return len(name) > 0

    def _name_in_use(self, name):
        for cat in self.timeline.get_categories():
            if cat != self.category and cat.name == name:
                return True
        return False


class PreferencesDialog(wx.Dialog):
    """
    Dialog used to edit application preferences.

    This is essentially a GUI for parts of the preferences in the config
    module.
    """

    def __init__(self, parent):
        wx.Dialog.__init__(self, parent, title=_("Preferences"))
        self._create_gui()

    def _create_gui(self):
        notebook = wx.Notebook(self, style=wx.BK_DEFAULT)
        # General tab
        panel = wx.Panel(notebook)
        notebook.AddPage(panel, _("General"))
        sizer = wx.BoxSizer(wx.VERTICAL)
        chb_open_recent_startup = wx.CheckBox(panel, label=_("Open most recent timeline on startup"))
        chb_open_recent_startup.SetValue(config.get_open_recent_at_startup())
        self.Bind(wx.EVT_CHECKBOX, self._chb_open_recent_startup_on_checkbox,
                  chb_open_recent_startup)
        sizer.Add(chb_open_recent_startup, border=BORDER, flag=wx.ALL)
        panel.SetSizer(sizer)
        # The close button
        btn_close = wx.Button(self, wx.ID_CLOSE)
        btn_close.SetDefault()
        btn_close.SetFocus()
        self.SetAffirmativeId(wx.ID_CLOSE)
        self.Bind(wx.EVT_BUTTON, self._btn_close_on_click, btn_close)
        # Layout
        main_box = wx.BoxSizer(wx.VERTICAL)
        main_box.Add(notebook, border=BORDER, flag=wx.ALL|wx.EXPAND,
                     proportion=1)
        button_box = wx.BoxSizer(wx.HORIZONTAL)
        button_box.AddStretchSpacer()
        button_box.Add(btn_close, flag=wx.LEFT, border=BORDER)
        main_box.Add(button_box, flag=wx.ALL|wx.EXPAND, border=BORDER)
        # Realize
        self.SetSizerAndFit(main_box)

    def _chb_open_recent_startup_on_checkbox(self, evt):
        config.set_open_recent_at_startup(evt.IsChecked())

    def _btn_close_on_click(self, e):
        self.Close()


class GotoDateDialog(wx.Dialog):

    def __init__(self, parent, time):
        wx.Dialog.__init__(self, parent, title=_("Go to Date"))
        self._create_gui()
        self.dtpc.set_value(time)

    def _create_gui(self):
        self.dtpc = DateTimePicker(self)
        checkbox = wx.CheckBox(self, label=_("Show time"))
        checkbox.SetValue(False)
        self.dtpc.show_time(checkbox.IsChecked())
        self.Bind(wx.EVT_CHECKBOX, self._chb_show_time_on_checkbox, checkbox)
        # Layout
        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(checkbox, flag=wx.LEFT|wx.TOP|wx.RIGHT,
                 border=BORDER, proportion=1)
        vbox.Add(self.dtpc, flag=wx.EXPAND|wx.RIGHT|wx.BOTTOM|wx.LEFT,
                 border=BORDER, proportion=1)
        self.Bind(wx.EVT_BUTTON, self._btn_ok_on_click, id=wx.ID_OK)
        button_box = self.CreateStdDialogButtonSizer(wx.OK|wx.CANCEL)
        vbox.Add(button_box, flag=wx.ALL|wx.EXPAND, border=BORDER)
        self.SetSizerAndFit(vbox)

    def _chb_show_time_on_checkbox(self, e):
        self.dtpc.show_time(e.IsChecked())

    def _btn_ok_on_click(self, e):
        self.time = self.dtpc.get_value()
        self.EndModal(wx.ID_OK)


class DateTimePicker(wx.Panel):
    """
    Control to pick a Python datetime object.

    The time part will default to 00:00:00 if none is entered.
    """

    def __init__(self, parent, show_time=True):
        wx.Panel.__init__(self, parent)
        self._create_gui()
        self.show_time(show_time)

    def show_time(self, show=True):
        self.time_picker.Show(show)
        self.GetSizer().Layout()

    def get_value(self):
        """Return the selected date time as a Python datetime object."""
        date = self.date_picker.GetValue()
        date_time = dt(date.Year, date.Month+1, date.Day)
        if self.time_picker.IsShown():
            time = self.time_picker.GetValue(as_wxDateTime=True)
            date_time = date_time.replace(hour=time.Hour,
                                          minute=time.Minute)
        return date_time

    def set_value(self, value):
        if value == None:
            now = dt.now()
            value = dt(now.year, now.month, now.day)
        wx_date_time = self._python_date_to_wx_date(value)
        self.date_picker.SetValue(wx_date_time)
        self.time_picker.SetValue(wx_date_time)

    def _create_gui(self):
        self.date_picker = wx.GenericDatePickerCtrl(self,
                               style=wx.DP_DROPDOWN|wx.DP_SHOWCENTURY)
        self.Bind(wx.EVT_DATE_CHANGED, self._date_picker_on_date_changed,
                  self.date_picker)
        self.time_picker = TimeCtrl(self, format="24HHMM")
        # Layout
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.date_picker, proportion=1,
                  flag=wx.ALIGN_CENTER_VERTICAL)
        sizer.Add(self.time_picker, proportion=0,
                  flag=wx.ALIGN_CENTER_VERTICAL)
        self.SetSizerAndFit(sizer)

    def _date_picker_on_date_changed(self, e):
        date = self.get_value()
        if date < TimePeriod.MIN_TIME:
            self.set_value(TimePeriod.MIN_TIME)
        if date > TimePeriod.MAX_TIME:
            self.set_value(TimePeriod.MAX_TIME)

    def _python_date_to_wx_date(self, py_date):
        return wx.DateTimeFromDMY(py_date.day, py_date.month-1, py_date.year,
                                  py_date.hour, py_date.minute,
                                  py_date.second)


class HyperlinkButton(wx.HyperlinkCtrl):

    def __init__(self, parent, label, url=""):
        wx.HyperlinkCtrl.__init__(self, parent, wx.ID_ANY, label=label,
                                  url=url,
                                  style=wx.HL_ALIGN_CENTRE|wx.NO_BORDER)
        self.SetVisitedColour(self.GetNormalColour())


class HelpBrowser(wx.Frame):

    HOME_ID = 10
    BACKWARD_ID = 20
    FORWARD_ID = 30

    def __init__(self, parent, help_system):
        wx.Frame.__init__(self, parent, title=_("Help"),
                          size=(600, 550), style=wx.DEFAULT_FRAME_STYLE)
        self.help_system = help_system
        self.history = []
        self.current_pos = -1
        self._create_gui()
        self._update_buttons()

    def show_page(self, id, type="page", change_history=True):
        """
        Where which is a tuple (type, id):

          * (page, page_id)
          * (search, search_string)
        """
        if change_history:
            if self.current_pos != -1:
                current_type, current_id = self.history[self.current_pos]
                if id == current_id:
                    return
            self.history = self.history[:self.current_pos + 1]
            self.history.append((type, id))
            self.current_pos += 1
        self._update_buttons()
        if type == "page":
            self.html_window.SetPage(self._generate_page(id))
        elif type == "search":
            self.html_window.SetPage(self.help_system.get_search_results_page(id))
        self.Show()
        self.Raise()

    def _create_gui(self):
        self.Bind(wx.EVT_CLOSE, self._window_on_close)
        self.toolbar = self.CreateToolBar()
        size = (24, 24)
        home_bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_HOME, wx.ART_TOOLBAR,
                                            size)
        back_bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_BACK, wx.ART_TOOLBAR,
                                            size)
        forward_bmp = wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD,
                                               wx.ART_TOOLBAR, size)
        self.toolbar.SetToolBitmapSize(size)
        # Home
        home_str = _("Go to home page")
        self.toolbar.AddLabelTool(HelpBrowser.HOME_ID, home_str,
                                  home_bmp, shortHelp=home_str)
        self.Bind(wx.EVT_TOOL, self._toolbar_on_click, id=HelpBrowser.HOME_ID)
        # Separator
        self.toolbar.AddSeparator()
        # Backward
        backward_str = _("Go back one page")
        self.toolbar.AddLabelTool(HelpBrowser.BACKWARD_ID, backward_str,
                                  back_bmp, shortHelp=backward_str)
        self.Bind(wx.EVT_TOOL, self._toolbar_on_click,
                  id=HelpBrowser.BACKWARD_ID)
        # Forward
        forward_str = _("Go forward one page")
        self.toolbar.AddLabelTool(HelpBrowser.FORWARD_ID, forward_str,
                                  forward_bmp, shortHelp=forward_str)
        self.Bind(wx.EVT_TOOL, self._toolbar_on_click,
                  id=HelpBrowser.FORWARD_ID)
        # Separator
        self.toolbar.AddSeparator()
        # Search
        self.search = wx.SearchCtrl(self.toolbar, size=(150, -1),
                                    style=wx.TE_PROCESS_ENTER)
        self.Bind(wx.EVT_TEXT_ENTER, self._search_on_text_enter, self.search)
        self.toolbar.AddControl(self.search)
        self.toolbar.Realize()
        # Html window
        self.html_window = wx.html.HtmlWindow(self)
        self.Bind(wx.html.EVT_HTML_LINK_CLICKED,
                  self._html_window_on_link_clicked, self.html_window)
        self.html_window.Connect(wx.ID_ANY, wx.ID_ANY, wx.EVT_KEY_DOWN.typeId,
                                 self._window_on_key_down)

    def _window_on_close(self, e):
        self.Show(False)

    def _window_on_key_down(self, evt):
        """
        Event handler used when a keyboard key has been pressed.

        The following keys are handled:
        Key         Action
        --------    ------------------------------------
        Backspace   Go to previous page
        """
        logging.debug("Key down event in HelpBrowser")
        keycode = evt.GetKeyCode()
        if keycode == wx.WXK_BACK:
            self._go_back()
        evt.Skip()

    def _toolbar_on_click(self, e):
        if e.GetId() == HelpBrowser.HOME_ID:
            self._go_home()
        elif e.GetId() == HelpBrowser.BACKWARD_ID:
            self._go_back()
        elif e.GetId() == HelpBrowser.FORWARD_ID:
            self._go_forward()

    def _search_on_text_enter(self, e):
        self._search(self.search.GetValue())

    def _html_window_on_link_clicked(self, e):
        url = e.GetLinkInfo().GetHref()
        if url.startswith("page:"):
            self.show_page(url[5:])
        else:
            pass
            # open in broswer

    def _go_home(self):
        self.show_page(self.help_system.home_page)

    def _go_back(self):
        if self.current_pos > 0:
            self.current_pos -= 1
            current_type, current_id = self.history[self.current_pos]
            self.show_page(current_id, type=current_type, change_history=False)

    def _go_forward(self):
        if self.current_pos < len(self.history) - 1:
            self.current_pos += 1
            current_type, current_id = self.history[self.current_pos]
            self.show_page(current_id, type=current_type, change_history=False)

    def _search(self, string):
        self.show_page(string, type="search")

    def _update_buttons(self):
        history_len = len(self.history)
        enable_backward = history_len > 1 and self.current_pos > 0
        enable_forward = history_len > 1 and self.current_pos < history_len - 1
        self.toolbar.EnableTool(HelpBrowser.BACKWARD_ID, enable_backward)
        self.toolbar.EnableTool(HelpBrowser.FORWARD_ID, enable_forward)

    def _generate_page(self, id):
        page = self.help_system.get_page(id)
        if page == None:
            error_page_html = "<h1>%s</h1><p>%s</p>" % (
                _("Page not found"),
                _("Could not find page '%s'.") % id)
            return self._wrap_in_html(error_page_html)
        else:
            return self._wrap_in_html(page.render_to_html())

    def _wrap_in_html(self, content):
        HTML_SKELETON = """
        <html>
        <head>
        </head>
        <body>
        %s
        </body>
        </html>
        """
        return HTML_SKELETON % content


class DescriptionEditor(wx.TextCtrl):

    def __init__(self, parent):
        wx.TextCtrl.__init__(self, parent, style=wx.TE_MULTILINE)

    def get_data(self):
        description = self.GetValue()
        if description.strip() != "":
            return description
        return None

    def set_data(self, data):
        self.SetValue(data)

    def clear_data(self):
        self.SetValue("")


class IconEditor(wx.Panel):

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.MAX_SIZE = (128, 128)
        # Controls
        self.img_icon = wx.StaticBitmap(self, size=self.MAX_SIZE)
        description = wx.StaticText(self, label=_("Images will be scaled to fit inside a %ix%i box.") % self.MAX_SIZE)
        btn_select = wx.Button(self, wx.ID_OPEN)
        btn_clear = wx.Button(self, wx.ID_CLEAR)
        self.Bind(wx.EVT_BUTTON, self._btn_select_on_click, btn_select)
        self.Bind(wx.EVT_BUTTON, self._btn_clear_on_click, btn_clear)
        # Layout
        sizer = wx.GridBagSizer(5, 5)
        sizer.Add(description, wx.GBPosition(0, 0), wx.GBSpan(1, 2))
        sizer.Add(btn_select, wx.GBPosition(1, 0), wx.GBSpan(1, 1))
        sizer.Add(btn_clear, wx.GBPosition(1, 1), wx.GBSpan(1, 1))
        sizer.Add(self.img_icon, wx.GBPosition(0, 2), wx.GBSpan(2, 1))
        self.SetSizerAndFit(sizer)
        # Data
        self.bmp = None

    def get_data(self):
        return self.get_icon()

    def set_data(self, data):
        self.set_icon(data)

    def clear_data(self):
        self.set_icon(None)

    def set_icon(self, bmp):
        self.bmp = bmp
        if self.bmp == None:
            self.img_icon.SetBitmap(wx.EmptyBitmap(1, 1))
        else:
            self.img_icon.SetBitmap(bmp)
        self.GetSizer().Layout()

    def get_icon(self):
        return self.bmp

    def _btn_select_on_click(self, evt):
        dialog = wx.FileDialog(self, message=_("Select Icon"),
                               wildcard="*", style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            path = dialog.GetPath()
            if os.path.exists(path):
                image = wx.EmptyImage(0, 0)
                success = image.LoadFile(path)
                # LoadFile will show error popup if not successful
                if success:
                    # Resize image if too large
                    (w, h) = image.GetSize()
                    (W, H) = self.MAX_SIZE
                    if w > W:
                        factor = float(W) / float(w)
                        w = w * factor
                        h = h * factor
                    if h > H:
                        factor = float(H) / float(h)
                        w = w * factor
                        h = h * factor
                    image = image.Scale(w, h, wx.IMAGE_QUALITY_HIGH)
                    self.set_icon(image.ConvertToBitmap())
        dialog.Destroy()

    def _btn_clear_on_click(self, evt):
        self.set_icon(None)
