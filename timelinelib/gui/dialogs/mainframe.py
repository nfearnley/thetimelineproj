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


import os.path

import wx

from timelinelib.about import APPLICATION_NAME
from timelinelib.about import display_about_dialog
from timelinelib.application import TimelineApplication
from timelinelib.db import db_open
from timelinelib.db.interface import TimelineIOError
from timelinelib.db.objects import TimePeriod
from timelinelib.gui.components.cattree import CategoriesTree
from timelinelib.gui.components.hyperlinkbutton import HyperlinkButton
from timelinelib.gui.components.search import SearchBar
from timelinelib.gui.components.timelineview import DrawingArea
from timelinelib.gui.dialogs.categorieseditor import CategoriesEditor
from timelinelib.gui.dialogs.duplicateevent import DuplicateEvent
from timelinelib.gui.dialogs.eventeditor import EventEditor
from timelinelib.gui.dialogs.helpbrowser import HelpBrowser
from timelinelib.gui.dialogs.preferences import PreferencesDialog
from timelinelib.gui.utils import _ask_question
from timelinelib.gui.utils import _display_error_message
from timelinelib.gui.utils import WildcardHelper
from timelinelib import config
from timelinelib.paths import ICONS_DIR
from timelinelib.utils import ex_msg
import timelinelib.gui.utils as gui_utils
import timelinelib.printing as printing


class MainFrame(wx.Frame):

    def __init__(self):
        wx.Frame.__init__(self, None, size=config.get_window_size(), 
                          pos=config.get_window_pos(),
                          style=wx.DEFAULT_FRAME_STYLE)
        # To enable translations of wx stock items.
        self.locale = wx.Locale(wx.LANGUAGE_DEFAULT)

        self.help_browser = HelpBrowser(self)
        self.controller = TimelineApplication(self, db_open, config.global_config)
        self.menu_controller = MenuController()

        self._set_initial_values_to_member_variables()
        self._create_print_data()
        self._create_gui()

        self.Maximize(config.get_window_maximized())
        self.SetTitle(APPLICATION_NAME)
        self.SetIcons(self._load_icon_bundle())

        self.main_panel.show_welcome_panel()
        self.enable_disable_menus()

    def _set_initial_values_to_member_variables(self):
        self.timeline = None
        self.timeline_wildcard_helper = WildcardHelper(
            _("Timeline files"), ["timeline", "ics"])
        self.images_wildcard_helper = WildcardHelper(
            _("Image files"), [("png", wx.BITMAP_TYPE_PNG)])
        self.images_svg_wildcard_helper = WildcardHelper(
            _("SVG files"), ["svg"])

    def _create_print_data(self):
        self.printData = wx.PrintData()
        self.printData.SetPaperId(wx.PAPER_A4)
        self.printData.SetPrintMode(wx.PRINT_MODE_PRINTER)
        self.printData.SetOrientation(wx.LANDSCAPE)

    def _create_gui(self):
        self._create_status_bar()
        self._create_main_panel()
        self._create_main_menu_bar()
        self._bind_frame_events()
        
    def _create_status_bar(self):
        self.CreateStatusBar()
        self.status_bar_adapter = StatusBarAdapter(self.GetStatusBar())
        
    def _create_main_panel(self):
        self.main_panel = MainPanel(self)
        
    def _create_main_menu_bar(self):
        main_menu_bar = wx.MenuBar()
        self._create_file_menu(main_menu_bar)
        self._create_edit_menu(main_menu_bar)
        self._create_view_menu(main_menu_bar)
        self._create_timeline_menu(main_menu_bar)
        self._create_navigate_menu(main_menu_bar)
        self._create_help_menu(main_menu_bar)
        self.SetMenuBar(main_menu_bar)
        
    def _create_file_menu(self, main_menu_bar):
        file_menu = wx.Menu()
        self._create_file_new_menu(file_menu)
        self._create_file_open_menu_item(file_menu)
        self._create_file_open_recent_menu(file_menu)
        file_menu.AppendSeparator()
        self._create_file_page_setup_menu_item(file_menu)
        self._create_file_print_preview_menu_item(file_menu)
        self._create_file_print_menu_item(file_menu)
        file_menu.AppendSeparator()
        self._create_file_export_to_image_menu_item(file_menu)
        self._create_file_export_to_svg_menu_item(file_menu)
        file_menu.AppendSeparator()
        self._create_file_exit_menu_item(file_menu)
        main_menu_bar.Append(file_menu, _("&File"))

    def _create_file_new_menu(self, file_menu):
        file_new_menu = wx.Menu()
        self._create_file_new_timeline_menu_item(file_new_menu)
        self._create_file_new_dir_timeline_menu_item(file_new_menu)
        file_menu.AppendMenu(wx.ID_ANY, _("New"), file_new_menu, _("Create a new timeline"))

    def _create_file_new_timeline_menu_item(self, file_new_menu):
        accel = wx.GetStockLabel(wx.ID_NEW, wx.STOCK_WITH_ACCELERATOR|wx.STOCK_WITH_MNEMONIC)
        accel = accel.split("\t", 1)[1]
        file_new_menu.Append(
            wx.ID_NEW, _("File Timeline...") + "\t" + accel, _("File Timeline..."))
        self.Bind(wx.EVT_MENU, self._mnu_file_new_on_click, id=wx.ID_NEW)

    def _mnu_file_new_on_click(self, event):
        self._create_new_timeline()

    def _create_new_timeline(self):
        wildcard = self.timeline_wildcard_helper.wildcard_string()
        dialog = wx.FileDialog(self, message=_("Create Timeline"),
                               wildcard=wildcard, style=wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            self._save_current_timeline_data()
            path = self.timeline_wildcard_helper.get_path(dialog)
            if os.path.exists(path):
                msg_first_part = _("The specified timeline already exists.")
                msg_second_part = _("Opening timeline instead of creating new.")
                wx.MessageBox("%s\n\n%s" % (msg_first_part, msg_second_part),
                              _("Information"),
                              wx.OK|wx.ICON_INFORMATION, self)
            self.open_timeline(path)
        dialog.Destroy()

    def _create_file_new_dir_timeline_menu_item(self, file_new_menu):
        mnu_file_new_dir = file_new_menu.Append(
            wx.ID_ANY, _("Directory Timeline..."), _("Directory Timeline..."))
        self.Bind(wx.EVT_MENU, self._mnu_file_new_dir_on_click, mnu_file_new_dir)

    def _mnu_file_new_dir_on_click(self, event):
        self._create_new_dir_timeline()

    def _create_new_dir_timeline(self):
        dialog = wx.DirDialog(self, message=_("Create Timeline"))
        if dialog.ShowModal() == wx.ID_OK:
            self._save_current_timeline_data()
            self.open_timeline(dialog.GetPath())
        dialog.Destroy()

    def _create_file_open_menu_item(self, file_menu):
        file_menu.Append(
            wx.ID_OPEN, self._add_ellipses_to_menuitem(wx.ID_OPEN),
            _("Open an existing timeline"))
        self.Bind(wx.EVT_MENU, self._mnu_file_open_on_click, id=wx.ID_OPEN)

    def _mnu_file_open_on_click(self, event):
        self._open_existing_timeline()

    def _open_existing_timeline(self):
        dir = ""
        if self.timeline is not None:
            dir = os.path.dirname(self.timeline.path)
        wildcard = self.timeline_wildcard_helper.wildcard_string()
        dialog = wx.FileDialog(self, message=_("Open Timeline"),
                               defaultDir=dir,
                               wildcard=wildcard, style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            self._save_current_timeline_data()
            self.open_timeline(dialog.GetPath())
        dialog.Destroy()

    def _create_file_open_recent_menu(self, file_menu):
        self.mnu_file_open_recent_submenu = wx.Menu()
        file_menu.AppendMenu(wx.ID_ANY, _("Open &Recent"), self.mnu_file_open_recent_submenu)
        self._update_open_recent_submenu()

    def _create_file_page_setup_menu_item(self, file_menu):
        mnu_file_print_setup = file_menu.Append(
            wx.ID_PRINT_SETUP, _("Page Set&up..."), _("Setup page for printing"))
        self.menu_controller.add_menu_requiring_timeline(mnu_file_print_setup)
        self.Bind(wx.EVT_MENU, self._mnu_file_print_setup_on_click, id=wx.ID_PRINT_SETUP)

    def _mnu_file_print_setup_on_click(self, event):
        printing.print_setup(self)

    def _create_file_print_preview_menu_item(self, file_menu):
        mnu_file_print_preview = file_menu.Append(
            wx.ID_PREVIEW, "", _("Print Preview"))
        self.menu_controller.add_menu_requiring_timeline(mnu_file_print_preview)
        self.Bind(wx.EVT_MENU, self._mnu_file_print_preview_on_click, id=wx.ID_PREVIEW)

    def _mnu_file_print_preview_on_click(self, event):
        printing.print_preview(self)

    def _create_file_print_menu_item(self, file_menu):
        mnu_file_print = file_menu.Append(
            wx.ID_PRINT, self._add_ellipses_to_menuitem(wx.ID_PRINT), _("Print"))
        self.menu_controller.add_menu_requiring_timeline(mnu_file_print)
        self.Bind(wx.EVT_MENU, self._mnu_file_print_on_click, id=wx.ID_PRINT)

    def _mnu_file_print_on_click(self, event):
        printing.print_timeline(self)

    def _create_file_export_to_image_menu_item(self, file_menu):
        mnu_file_export = file_menu.Append(
            wx.ID_ANY, _("&Export to Image..."), _("Export the current view to a PNG image"))
        self.menu_controller.add_menu_requiring_timeline(mnu_file_export)
        self.Bind(wx.EVT_MENU, self._mnu_file_export_on_click, mnu_file_export)

    def _mnu_file_export_on_click(self, evt):
        self._export_to_image()

    def _export_to_image(self):
        wildcard = self.images_wildcard_helper.wildcard_string()
        dialog = wx.FileDialog(self, message=_("Export to Image"),
                               wildcard=wildcard, style=wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            path = self.images_wildcard_helper.get_path(dialog)
            overwrite_question = _("File '%s' exists. Overwrite?") % path
            if (not os.path.exists(path) or
                _ask_question(overwrite_question, self) == wx.YES):
                bitmap = self.main_panel.drawing_area.get_current_image()
                image = wx.ImageFromBitmap(bitmap)
                type = self.images_wildcard_helper.get_extension_data(path)
                image.SaveFile(path, type)
        dialog.Destroy()
 
    def _create_file_export_to_svg_menu_item(self, file_menu):
        mnu_file_export_svg = file_menu.Append(
            wx.ID_ANY, _("&Export to SVG..."), _("Export the current view to a SVG image"))
        self.menu_controller.add_menu_requiring_timeline(mnu_file_export_svg)
        self.Bind(wx.EVT_MENU, self._mnu_file_export_svg_on_click, mnu_file_export_svg)

    def _mnu_file_export_svg_on_click(self, evt):
        self._export_to_svg_image()

    def _export_to_svg_image(self):
        if not self._has_pysvg_module():
            _display_error_message(_("Could not find pysvg Python package. It is needed to export to SVG. See the Timeline website or the INSTALL file for instructions how to install it."), self)
            return
        import timelinelib.svgexport as svgexport
        wildcard = self.images_svg_wildcard_helper.wildcard_string()
        dialog = wx.FileDialog(self, message=_("Export to SVG"),
                               wildcard=wildcard, style=wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            path = self.images_svg_wildcard_helper.get_path(dialog)
            overwrite_question = _("File '%s' exists. Overwrite?") % path
            if (not os.path.exists(path) or
                _ask_question(overwrite_question, self) == wx.YES):
                svgexport.export(
                    path,
                    self.main_panel.drawing_area.get_drawer().scene,
                    self.main_panel.drawing_area.get_view_properties())
        dialog.Destroy()

    def _has_pysvg_module(self):
        try:
            import pysvg
            return True
        except ImportError:
            return False

    def _create_file_exit_menu_item(self, file_menu):
        file_menu.Append(wx.ID_EXIT, "", _("Exit the program"))
        self.Bind(wx.EVT_MENU, self._mnu_file_exit_on_click, id=wx.ID_EXIT)

    def _mnu_file_exit_on_click(self, evt):
        self.Close()

    def _create_edit_menu(self, main_menu_bar):
        edit_menu = wx.Menu()
        self._create_edit_find_menu_item(edit_menu)
        edit_menu.AppendSeparator()
        self._create_edit_preferences_menu_item(edit_menu)
        main_menu_bar.Append(edit_menu, _("&Edit"))

    def _create_edit_find_menu_item(self, edit_menu):
        find_menu_item = edit_menu.Append(wx.ID_FIND)
        self.Bind(wx.EVT_MENU, self._mnu_edit_find_on_click, find_menu_item)
        self.menu_controller.add_menu_requiring_timeline(find_menu_item)

    def _mnu_edit_find_on_click(self, evt):
        self.main_panel.show_searchbar(True)

    def _create_edit_preferences_menu_item(self, edit_menu):
        preferences_item = edit_menu.Append(wx.ID_PREFERENCES)
        self.Bind(wx.EVT_MENU, self._mnu_edit_preferences_on_click, preferences_item)

    def _mnu_edit_preferences_on_click(self, evt):
        dialog = PreferencesDialog(self)
        dialog.ShowModal()
        dialog.Destroy()

    def _create_view_menu(self, main_menu_bar):
        view_menu = wx.Menu()
        self._create_view_sidebar_menu_item(view_menu)
        self._create_view_legend_menu_item(view_menu)
        view_menu.AppendSeparator()
        self._create_view_balloons_menu_item(view_menu)
        main_menu_bar.Append(view_menu, _("&View"))

    def _create_view_sidebar_menu_item(self, view_menu):
        view_sidebar_item = view_menu.Append(
            wx.ID_ANY, _("&Sidebar\tCtrl+I"), kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self._mnu_view_sidebar_on_click, view_sidebar_item)
        self.menu_controller.add_menu_requiring_visible_timeline_view(view_sidebar_item)
        view_sidebar_item.Check(config.get_show_sidebar())

    def _mnu_view_sidebar_on_click(self, evt):
        config.set_show_sidebar(evt.IsChecked())
        if evt.IsChecked():
            self.main_panel.show_sidebar()
        else:
            self.main_panel.hide_sidebar()

    def _create_view_legend_menu_item(self, view_menu):
        view_legend_item = view_menu.Append(
            wx.ID_ANY, _("&Legend"), kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self._mnu_view_legend_on_click, view_legend_item)
        self.menu_controller.add_menu_requiring_timeline(view_legend_item)
        view_legend_item.Check(config.get_show_legend())

    def _mnu_view_legend_on_click(self, evt):
        config.set_show_legend(evt.IsChecked())
        self.main_panel.drawing_area.show_hide_legend(evt.IsChecked())

    def _create_view_balloons_menu_item(self, view_menu):
        view_balloons_item = view_menu.Append(
            wx.ID_ANY, _("&Balloons on hover"), kind=wx.ITEM_CHECK)
        self.Bind(wx.EVT_MENU, self._mnu_view_balloons_on_click, view_balloons_item)
        view_balloons_item.Check(config.get_balloon_on_hover())

    def _mnu_view_balloons_on_click(self, evt):
        config.set_balloon_on_hover(evt.IsChecked())
        self.main_panel.drawing_area.balloon_visibility_changed(evt.IsChecked())

    def _create_timeline_menu(self, main_menu_bar):
        timeline_menu = wx.Menu()
        self._create_timeline_create_event_menu_item(timeline_menu)
        self._create_timeline_duplicate_event_menu_item(timeline_menu)
        self._create_timeline_edit_categories(timeline_menu)
        main_menu_bar.Append(timeline_menu, _("&Timeline"))

    def _create_timeline_create_event_menu_item(self, timeline_menu):
        create_event_item = timeline_menu.Append(
            wx.ID_ANY, _("Create &Event..."), _("Create a new event"))
        self.Bind(wx.EVT_MENU, self._mnu_timeline_create_event_on_click, create_event_item)
        self.menu_controller.add_menu_requiring_writable_timeline(create_event_item)

    def _mnu_timeline_create_event_on_click(self, evt):
        self.create_new_event()

    def create_new_event(self, start=None, end=None):
        def create_event_editor():
            return EventEditor(self, _("Create Event"), self.timeline,
                               start, end)
        gui_utils.show_modal(create_event_editor, self.handle_db_error)

    def _create_timeline_duplicate_event_menu_item(self, timeline_menu):
        self.mnu_timeline_duplicate_event = timeline_menu.Append(
            wx.ID_ANY, _("&Duplicate Selected Event..."), _("Duplicate the Selected Event"))
        self.Bind(wx.EVT_MENU, self._mnu_timeline_duplicate_event_on_click,
                  self.mnu_timeline_duplicate_event)
        self.menu_controller.add_menu_requiring_writable_timeline(self.mnu_timeline_duplicate_event)

    def _mnu_timeline_duplicate_event_on_click(self, evt):
        self.duplicate_event()

    def duplicate_event(self, event=None):
        def show_dialog(event):
            def create_dialog():
                return DuplicateEvent(self, self.timeline, event)
            gui_utils.show_modal(create_dialog, self.handle_db_error)
        if event is None:
            try:
                drawing_area = self.main_panel.drawing_area 
                id = drawing_area.get_view_properties().get_selected_event_ids()[0]
                event = self.timeline.find_event_with_id(id)
            except IndexError, e:
                # No event selected so do nothing!
                return
        show_dialog(event)

    def _create_timeline_edit_categories(self, timeline_menu):
        edit_categories_item = timeline_menu.Append(
            wx.ID_ANY, _("Edit &Categories"), _("Edit categories"))
        self.Bind(wx.EVT_MENU, self._mnu_timeline_edit_categories_on_click,
                  edit_categories_item)
        self.menu_controller.add_menu_requiring_writable_timeline(edit_categories_item)

    def _mnu_timeline_edit_categories_on_click(self, evt):
        self.edit_categories()

    def edit_categories(self):
        def create_categories_editor():
            return CategoriesEditor(self, self.timeline)
        gui_utils.show_modal(create_categories_editor, self.handle_db_error)

    def _create_navigate_menu(self, main_menu_bar):
        navigate_menu = wx.Menu()
        self._navigation_menu_items = []
        self._navigation_functions_by_menu_item_id = {}
        self._update_navigation_menu_items()
        navigate_menu.AppendSeparator()
        self._create_navigate_find_first_event_menu_item(navigate_menu)
        self._create_navigate_find_last_event_menu_item(navigate_menu)
        self._create_navigate_fit_all_events_menu_item(navigate_menu)
        main_menu_bar.Append(navigate_menu, _("&Navigate"))
        self.mnu_navigate = navigate_menu

    def _create_navigate_find_first_event_menu_item(self, navigate_menu):
        find_first = navigate_menu.Append(wx.ID_ANY, _("Find First Event"))
        self.Bind(wx.EVT_MENU, self._mnu_navigate_find_first_on_click, find_first)
        self.menu_controller.add_menu_requiring_timeline(find_first)

    def _mnu_navigate_find_first_on_click(self, evt):
        event = self.timeline.get_first_event()
        if event:
            start = event.time_period.start_time
            delta = self.main_panel.drawing_area.get_view_properties().displayed_period.delta()
            end   = start + delta 
            margin_delta = self.timeline.get_time_type().margin_delta(delta)
            self._navigate_timeline(lambda tp: tp.update(start, end, -margin_delta))

    def _create_navigate_find_last_event_menu_item(self, navigate_menu):
        find_last = navigate_menu.Append(wx.ID_ANY, _("Find Last Event"))
        self.Bind(wx.EVT_MENU, self._mnu_navigate_find_last_on_click, find_last)
        self.menu_controller.add_menu_requiring_timeline(find_last)

    def _mnu_navigate_find_last_on_click(self, evt):
        event = self.timeline.get_last_event()
        if event:
            end = event.time_period.end_time
            delta = self.main_panel.drawing_area.get_view_properties().displayed_period.delta()
            start = end - delta
            margin_delta = self.timeline.get_time_type().margin_delta(delta)
            self._navigate_timeline(lambda tp: tp.update(start, end, end_delta=margin_delta))

    def _create_navigate_fit_all_events_menu_item(self, navigate_menu):
        fit_all_events = navigate_menu.Append(wx.ID_ANY, _("Fit All Events"))
        self.Bind(wx.EVT_MENU, self._mnu_navigate_fit_all_events_on_click, fit_all_events)
        self.menu_controller.add_menu_requiring_timeline(fit_all_events)

    def _mnu_navigate_fit_all_events_on_click(self, evt):
        self._fit_all_events()

    def _fit_all_events(self):
        all_period = self._period_for_all_visible_events()
        if all_period == None:
            return
        if all_period.is_period():
            all_period.zoom(-1)
            self._navigate_timeline(lambda tp: tp.update(all_period.start_time, all_period.end_time))
        else:
            self._navigate_timeline(lambda tp: tp.center(all_period.mean_time()))

    def _period_for_all_visible_events(self):
        try:
            visible_events = self._all_visible_events()
            if len(visible_events) > 0:
                time_type = self.timeline.get_time_type()
                start = self._first_time(visible_events)
                end = self._last_time(visible_events)
                return TimePeriod(time_type, start, end)
            else:
                return None
        except ValueError, ex:
            _display_error_message(ex.message)
        return None

    def _all_visible_events(self):
        view_properties = self.main_panel.drawing_area.get_view_properties()
        all_events = self.timeline.get_all_events()
        visible_events = view_properties.filter_events(all_events)
        return visible_events

    def _first_time(self, events):
        start_time = lambda event: event.time_period.start_time
        return start_time(min(events, key=start_time))

    def _last_time(self, events):
        end_time = lambda event: event.time_period.end_time
        return end_time(max(events, key=end_time))
    
    def _create_help_menu(self, main_menu_bar):
        help_menu = wx.Menu()
        self._create_help_contents_menu_item(help_menu)
        help_menu.AppendSeparator()
        self._create_help_tutorial_menu_item(help_menu)
        self._create_help_contact_menu_item(help_menu)
        help_menu.AppendSeparator()
        self._create_help_about_menu_item(help_menu)
        main_menu_bar.Append(help_menu, _("&Help"))

    def _create_help_contents_menu_item(self, help_menu):
        contents_item = help_menu.Append(wx.ID_HELP, _("&Contents\tF1"))
        self.Bind(wx.EVT_MENU, self._mnu_help_contents_on_click, contents_item)

    def _mnu_help_contents_on_click(self, e):
        self.help_browser.show_page("contents")

    def _create_help_tutorial_menu_item(self, help_menu):
        tutorial_item = help_menu.Append(wx.ID_ANY, _("Getting started tutorial"))
        self.Bind(wx.EVT_MENU, self._mnu_help_tutorial_on_click, tutorial_item)

    def _mnu_help_tutorial_on_click(self, e):
        self.open_timeline(":tutorial:")

    def _create_help_contact_menu_item(self, help_menu):
        contact_item = help_menu.Append(wx.ID_ANY, _("Contact"))
        self.Bind(wx.EVT_MENU, self._mnu_help_contact_on_click, contact_item)

    def _mnu_help_contact_on_click(self, e):
        self.help_browser.show_page("contact")

    def _create_help_about_menu_item(self, help_menu):
        about_item = help_menu.Append(wx.ID_ABOUT)
        self.Bind(wx.EVT_MENU, self._mnu_help_about_on_click, about_item)

    def _mnu_help_about_on_click(self, e):
        display_about_dialog()

    def _bind_frame_events(self):
        self.Bind(wx.EVT_CLOSE, self._window_on_close)

    def _window_on_close(self, event):
        self._save_current_timeline_data()
        self._save_application_config()
        self.Destroy()

    def _save_application_config(self):
        config.set_window_size(self.GetSize())
        config.set_window_pos(self.GetPosition())
        config.set_window_maximized(self.IsMaximized())
        config.set_sidebar_width(self.main_panel.get_sidebar_width())
        try:
            config.write()
        except IOError, ex:
            friendly = _("Unable to write configuration file.")
            msg = "%s\n\n%s" % (friendly, ex_msg(ex))
            _display_error_message(msg, self)

    def open_timeline(self, input_file):
        self.controller.open_timeline(input_file)
        self._update_navigation_menu_items()

    def edit_event(self, event):
        def create_event_editor():
            return EventEditor(self, _("Edit Event"), self.timeline,
                               event=event)
        gui_utils.show_modal(create_event_editor, self.handle_db_error)

    def handle_db_error(self, error):
        _display_error_message(ex_msg(error), self)
        self._switch_to_error_view(error)

    def _switch_to_error_view(self, error):
        self._display_timeline(None)
        self.main_panel.error_panel.populate(error)
        self.main_panel.show_error_panel()
        self.enable_disable_menus()

    def _display_timeline(self, timeline):
        self.timeline = timeline
        self.menu_controller.on_timeline_change(timeline)
        if timeline == None:
            # Do this before the next line so that we still have a timeline to
            # unregister
            self.main_panel.cattree.initialize_from_timeline_view(None)
            self.main_panel.searchbar.set_view(None)
        self.main_panel.drawing_area.set_timeline(self.timeline)
        self.status_bar_adapter.set_read_only_text("")
        if timeline == None:
            self.main_panel.show_welcome_panel()
            self.SetTitle(APPLICATION_NAME)
        else:
            self.main_panel.cattree.initialize_from_timeline_view(self.main_panel.drawing_area)
            self.main_panel.searchbar.set_view(self.main_panel.drawing_area)
            self.main_panel.show_timeline_panel()
            self.SetTitle("%s (%s) - %s" % (
                os.path.basename(self.timeline.path),
                os.path.dirname(os.path.abspath(self.timeline.path)),
                APPLICATION_NAME))
            if timeline.is_read_only():
                self.status_bar_adapter.set_read_only_text(_("read-only"))

    def _add_ellipses_to_menuitem(self, id):
        plain = wx.GetStockLabel(id,
                wx.STOCK_WITH_ACCELERATOR|wx.STOCK_WITH_MNEMONIC)
        # format of plain 'xxx[\tyyy]', example '&New\tCtrl+N'
        tab_index = plain.find("\t")
        if tab_index != -1:
            return plain[:tab_index] + "..." + plain[tab_index:]
        return plain + "..."

    def _update_navigation_menu_items(self):
        self._clear_navigation_menu_items()
        if self.timeline:
            self._create_navigation_menu_items()

    def _clear_navigation_menu_items(self):
        while self._navigation_menu_items:
            self.mnu_navigate.RemoveItem(self._navigation_menu_items.pop())
        self._navigation_functions_by_menu_item_id.clear()

    def _create_navigation_menu_items(self):
        item_data = self.timeline.get_time_type().get_navigation_functions()
        pos = 0
        for (itemstr, fn) in item_data:
            if itemstr == "SEP":
                item = self.mnu_navigate.InsertSeparator(pos)
            else:
                item = self.mnu_navigate.Insert(pos, wx.ID_ANY, itemstr)
                self._navigation_functions_by_menu_item_id[item.GetId()] = fn
                self.Bind(wx.EVT_MENU, self._navigation_menu_item_on_click, item)
            self._navigation_menu_items.append(item)
            pos += 1

    def _navigation_menu_item_on_click(self, evt):
        fn = self._navigation_functions_by_menu_item_id[evt.GetId()]
        fn(self, self._get_time_period(), self._navigate_timeline)

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

    def _mnu_file_open_recent_item_on_click(self, event):
        path = self.open_recent_map[event.GetId()]
        self.open_timeline_if_exists(path)

    def open_timeline_if_exists(self, path):
        if os.path.exists(path):
            self.open_timeline(path)
        else:
            _display_error_message(_("File '%s' does not exist.") % path, self)

    def enable_disable_menus(self):
        self.menu_controller.enable_disable_menus(self.main_panel.timeline_panel_visible())                                                        
        self._enable_disable_duplicate_event_menu()
        self._enable_disable_searchbar()
  
    def _enable_disable_duplicate_event_menu(self):
        view_properties = self.main_panel.drawing_area.get_view_properties()
        one_event_selected = len(view_properties.selected_event_ids) == 1
        self.mnu_timeline_duplicate_event.Enable(one_event_selected)

    def _enable_disable_searchbar(self): 
        if self.timeline == None:
            self.main_panel.show_searchbar(False)
        
    def _save_current_timeline_data(self):
        if self.timeline:
            try:
                self.timeline.save_view_properties(self.main_panel.drawing_area.get_view_properties())
            except TimelineIOError, e:
                self.handle_db_error(e)

    def _load_icon_bundle(self):
        bundle = wx.IconBundle()
        for size in ["16", "32", "48"]:
            iconpath = os.path.join(ICONS_DIR, "%s.png" % size)
            icon = wx.IconFromBitmap(wx.BitmapFromImage(wx.Image(iconpath)))
            bundle.AddIcon(icon)
        return bundle

    def _navigate_timeline(self, navigation_fn):
        return self.main_panel.drawing_area.navigate_timeline(navigation_fn)

    def _get_time_period(self):
        return self.main_panel.drawing_area.get_time_period()


class MenuController(object):
    
    def __init__(self):
        self.current_timeline = None
        self.menus_requiring_timeline = []
        self.menus_requiring_writable_timeline = []
        self.menus_requiring_visible_timeline_view = []

    def on_timeline_change(self, timeline):
        self.current_timeline = timeline
        
    def add_menu_requiring_writable_timeline(self, menu):
        self.menus_requiring_writable_timeline.append(menu)

    def add_menu_requiring_timeline(self, menu):
        self.menus_requiring_timeline.append(menu)

    def add_menu_requiring_visible_timeline_view(self, menu):
        self.menus_requiring_visible_timeline_view.append(menu)
        
    def enable_disable_menus(self, timeline_view_visible):
        for menu in self.menus_requiring_writable_timeline:
            self._enable_disable_menu_requiring_writable_timeline(menu)
        for menu in self.menus_requiring_timeline:
            self._enable_disable_menu_requiring_timeline(menu)
        for menu in self.menus_requiring_visible_timeline_view:
            self._enable_disable_menu_requiring_visible_timeline_view(menu, timeline_view_visible)
        
    def _enable_disable_menu_requiring_writable_timeline(self, menu):
        if self.current_timeline == None:
            menu.Enable(False)
        elif self.current_timeline.is_read_only():
            menu.Enable(False)
        else:
            menu.Enable(True)

    def _enable_disable_menu_requiring_timeline(self, menu):
        menu.Enable(self.current_timeline != None)

    def _enable_disable_menu_requiring_visible_timeline_view(self, menu, timeline_view_visible):
        has_timeline = self.current_timeline != None
        menu.Enable(has_timeline and timeline_view_visible)
        

class MainPanel(wx.Panel):
    """
    Panel that covers the whole client area of MainFrame.

    Displays one of the following panels:

      * The welcome panel (show_welcome_panel)
      * A splitter with sidebar and DrawingArea (show_timeline_panel)
      * The error panel (show_error_panel)

    Also displays the search bar.
    """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self._create_gui()
        # Install variables for backwards compatibility
        self.cattree = self.timeline_panel.sidebar.cattree
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

    def show_searchbar(self, show=True):
        self.searchbar.Show(show)
        if show == True:
            self.searchbar.search.SetFocus()
        self.GetSizer().Layout()

    def _create_gui(self):
        # Search bar
        def search_close():
            self.show_searchbar(False)
        self.searchbar = SearchBar(self, search_close)
        self.searchbar.Show(False)
        # Panels
        self.welcome_panel = WelcomePanel(self)
        self.timeline_panel = TimelinePanel(self)
        self.error_panel = ErrorPanel(self)
        # Layout
        self.sizerOuter = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.sizer.Add(self.welcome_panel, flag=wx.GROW, proportion=1)
        self.sizer.Add(self.timeline_panel, flag=wx.GROW, proportion=1)
        self.sizer.Add(self.error_panel, flag=wx.GROW, proportion=1)
        self.sizerOuter.Add(self.sizer, flag=wx.GROW, proportion=1)
        self.sizerOuter.Add(self.searchbar, flag=wx.GROW, proportion=0)
        self.SetSizer(self.sizerOuter)

    def _show_panel(self, panel):
        # Hide all panels
        for panel_to_hide in [self.welcome_panel, self.timeline_panel,
                              self.error_panel]:
            panel_to_hide.Show(False)
        # Show this one
        panel.Show(True)
        self.sizerOuter.Layout()


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
        wx.GetTopLevelParent(self).open_timeline(":tutorial:")


class TimelinePanel(wx.Panel):
    """
    Showing the drawn timeline, the vertical sizer, and the optional sidebar.
    """

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
        main_frame = wx.GetTopLevelParent(self)
        self.drawing_area = DrawingArea(self.splitter,
                                        main_frame.status_bar_adapter,
                                        self.divider_line_slider,
                                        main_frame.handle_db_error)
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
        self.txt_error.SetLabel(ex_msg(error))

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
        wx.GetTopLevelParent(self).help_browser.show_page("contact")


class Sidebar(wx.Panel):
    """
    The left part in TimelinePanel.

    Currently only shows the categories with visibility check boxes.
    """

    def __init__(self, parent):
        wx.Panel.__init__(self, parent, style=wx.BORDER_NONE)
        self._create_gui()

    def _create_gui(self):
        main_frame = wx.GetTopLevelParent(self)
        self.cattree = CategoriesTree(self, main_frame.handle_db_error)
        # Layout
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.cattree, flag=wx.GROW, proportion=1)
        self.SetSizer(sizer)


class StatusBarAdapter(object):

    HIDDEN_EVENT_COUNT_COLUMN = 1
    READ_ONLY_COLUMN = 2

    def __init__(self, wx_status_bar):
        self.wx_status_bar = wx_status_bar
        self.wx_status_bar.SetFieldsCount(3)
        self.wx_status_bar.SetStatusWidths([-1, 200, 150])

    def set_text(self, text):
        self.wx_status_bar.SetStatusText(text)

    def set_hidden_event_count_text(self, text):
        self.wx_status_bar.SetStatusText(text, self.HIDDEN_EVENT_COUNT_COLUMN)

    def set_read_only_text(self, text):
        self.wx_status_bar.SetStatusText(text, self.READ_ONLY_COLUMN)
