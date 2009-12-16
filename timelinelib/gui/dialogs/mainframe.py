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
The main frame of the application.
"""


import os.path
from datetime import datetime as dt

import wx

from timelinelib.db import open as db_open
from timelinelib.db.interface import TimelineIOError
from timelinelib.gui.utils import _display_error_message
from timelinelib.gui.utils import _ask_question
from timelinelib.gui.utils import _create_wildcard
from timelinelib.gui.utils import _extend_path
from timelinelib import config
from timelinelib.about import display_about_dialog
from timelinelib.about import APPLICATION_NAME
from timelinelib.paths import ICONS_DIR
from timelinelib.paths import HELP_RESOURCES_DIR
import timelinelib.printing as printing
import timelinelib.help as help
import timelinelib.help_pages as help_pages
from timelinelib.gui.utils import BORDER
from timelinelib.gui.utils import ID_ERROR
from timelinelib.gui.dialogs.categorieseditor import CategoriesEditor
from timelinelib.gui.dialogs.eventeditor import EventEditor
from timelinelib.gui.dialogs.gotodate import GotoDateDialog
from timelinelib.gui.dialogs.helpbrowser import HelpBrowser
from timelinelib.gui.dialogs.preferences import PreferencesDialog
from timelinelib.gui.components.categorieslistbox import CategoriesVisibleCheckListBox
from timelinelib.gui.components.hyperlinkbutton import HyperlinkButton
from timelinelib.gui.components.timelineview import DrawingArea


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
        fit_century = self.mnu_navigate.Append(wx.ID_ANY, _("Fit Century"))
        fit_decade = self.mnu_navigate.Append(wx.ID_ANY, _("Fit Decade"))
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
        self.Bind(wx.EVT_MENU, self._mnu_navigate_fit_century_on_click, fit_century)
        self.Bind(wx.EVT_MENU, self._mnu_navigate_fit_decade_on_click, fit_decade)
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

    def _mnu_navigate_fit_century_on_click(self, evt):
        self._navigate_timeline(lambda tp: tp.fit_century())

    def _mnu_navigate_fit_decade_on_click(self, evt):
        self._navigate_timeline(lambda tp: tp.fit_decade())

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
        self.help_browser.show_page("contents")

    def _mnu_help_tutorial_on_click(self, e):
        self.help_browser.show_page("tutorial")

    def _mnu_help_contact_on_click(self, e):
        self.help_browser.show_page("contact")

    def _mnu_help_about_on_click(self, e):
        display_about_dialog()

    def _init_help_system(self):
        help_system = help.HelpSystem("contents", HELP_RESOURCES_DIR + "/", "page:")
        help_pages.install(help_system)
        self.help_browser = HelpBrowser(self, help_system)

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
        self.help_browser.show_page("tutorial")


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
        self.help_browser.show_page("contact")


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
