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

import wx.lib.newevent

from timelinelib.application import TimelineApplication
from timelinelib.config.dotfile import read_config
from timelinelib.config.paths import ICONS_DIR
from timelinelib.dataexport.bitmap import export_to_image
from timelinelib.dataexport.bitmap import export_to_images
from timelinelib.dataexport.timelinexml import export_db_to_timeline_xml
from timelinelib.data import TimePeriod
from timelinelib.db.exceptions import TimelineIOError
from timelinelib.db import db_open
from timelinelib.db.utils import safe_locking
from timelinelib.feedback.feature import FEATURES
from timelinelib.feedback.feature import show_feature_feedback_dialog
from timelinelib.meta.about import APPLICATION_NAME
from timelinelib.meta.about import display_about_dialog
from timelinelib.proxies.drawingarea import DrawingAreaProxy
from timelinelib.proxies.sidebar import SidebarProxy
from timelinelib.time.numtime import NumTimeType
from timelinelib.utils import ex_msg
from timelinelib.wxgui.components.hyperlinkbutton import HyperlinkButton
from timelinelib.wxgui.components.search import SearchBar
from timelinelib.wxgui.components.timeline import TimelinePanel
from timelinelib.wxgui.dialogs.categorieseditor import CategoriesEditor
from timelinelib.wxgui.dialogs.duplicateevent import open_duplicate_event_dialog_for_event
from timelinelib.wxgui.dialogs.eventeditor import open_create_event_editor
from timelinelib.wxgui.dialogs.feedback import show_feedback_dialog
from timelinelib.wxgui.dialogs.helpbrowser import HelpBrowser
from timelinelib.wxgui.dialogs.importevents import ImportDialog
from timelinelib.wxgui.dialogs.preferences import PreferencesDialog
from timelinelib.wxgui.dialogs.setcategoryeditor import SetCategoryEditorDialog
from timelinelib.wxgui.dialogs.shortcutseditor import ShortcutsEditorDialog
from timelinelib.wxgui.dialogs.textdisplay import TextDisplayDialog
from timelinelib.wxgui.dialogs.timeeditor import TimeEditorDialog
from timelinelib.wxgui.timer import TimelineTimer
from timelinelib.wxgui.utils import _ask_question
from timelinelib.wxgui.utils import display_error_message
from timelinelib.wxgui.utils import display_information_message
from timelinelib.wxgui.utils import WildcardHelper
import timelinelib.wxgui.utils as gui_utils


CatsViewChangedEvent, EVT_CATS_VIEW_CHANGED = wx.lib.newevent.NewCommandEvent()


ID_SIDEBAR = wx.NewId()
ID_LEGEND = wx.NewId()
ID_BALLOONS = wx.NewId()
ID_ZOOMIN = wx.NewId()
ID_ZOOMOUT = wx.NewId()
ID_VERT_ZOOMIN = wx.NewId()
ID_VERT_ZOOMOUT = wx.NewId()
ID_CREATE_EVENT = wx.NewId()
ID_EDIT_EVENT = wx.NewId()
ID_DUPLICATE_EVENT = wx.NewId()
ID_SET_CATEGORY_ON_SELECTED = wx.NewId()
ID_MEASURE_DISTANCE = wx.NewId()
ID_SET_CATEGORY_ON_WITHOUT = wx.NewId()
ID_EDIT_CATEGORIES = wx.NewId()
ID_SET_READONLY = wx.NewId()
ID_FIND_FIRST = wx.NewId()
ID_FIND_LAST = wx.NewId()
ID_FIT_ALL = wx.NewId()
ID_EDIT_SHORTCUTS = wx.NewId()
ID_TUTORIAL = wx.NewId()
ID_FEEDBACK = wx.NewId()
ID_CONTACT = wx.NewId()
ID_IMPORT = wx.NewId()
ID_EXPORT = wx.NewId()
ID_EXPORT_ALL = wx.NewId()
ID_EXPORT_SVG = wx.NewId()
ID_NEW_NUMERIC = wx.NewId()
ID_NEW_DIR = wx.NewId()
ID_FIND_CATEGORIES = wx.NewId()
ID_NEW = wx.ID_NEW
ID_FIND = wx.ID_FIND
ID_UNDO = wx.NewId()
ID_REDO = wx.NewId()
ID_PREFERENCES = wx.ID_PREFERENCES
ID_HELP = wx.ID_HELP
ID_ABOUT = wx.ID_ABOUT
ID_SAVEAS = wx.ID_SAVEAS
ID_EXIT = wx.ID_EXIT
ID_NAVIGATE = wx.NewId() + 100


class GuiCreator(object):

    def _create_gui(self):
        self.shortcut_items = {}
        self._create_status_bar()
        self._create_main_panel()
        self._create_main_menu_bar()
        self._bind_frame_events()

    def _create_status_bar(self):
        self.CreateStatusBar()
        self.status_bar_adapter = StatusBarAdapter(self.GetStatusBar())

    def _create_main_panel(self):
        self.main_panel = MainPanel(self, self.config, self)

    def _create_main_menu_bar(self):
        main_menu_bar = wx.MenuBar()
        self._create_file_menu(main_menu_bar)
        self._create_edit_menu(main_menu_bar)
        self._create_view_menu(main_menu_bar)
        self._create_timeline_menu(main_menu_bar)
        self._create_navigate_menu(main_menu_bar)
        self._create_help_menu(main_menu_bar)
        self._set_shortcuts()
        self.SetMenuBar(main_menu_bar)

    def _set_shortcuts(self):
        from timelinelib.config.shortcut import ShortcutController
        self.shortcut_controller = ShortcutController(self.config, self.shortcut_items)
        self.shortcut_controller.load_config_settings()
        
    def _bind_frame_events(self):
        self.Bind(wx.EVT_CLOSE, self._window_on_close)

    def _create_file_menu(self, main_menu_bar):
        file_menu = wx.Menu()
        self._create_file_new_menu(file_menu)
        self._create_file_open_menu_item(file_menu)
        self._create_file_open_recent_menu(file_menu)
        file_menu.AppendSeparator()
        self._create_file_save_as_menu(file_menu)
        file_menu.AppendSeparator()
        self._create_import_menu_item(file_menu)
        file_menu.AppendSeparator()
        self._create_file_export_to_image_menu_item(file_menu)
        self._create_file_export_to_images_menu_item(file_menu)
        self._create_file_export_to_svg_menu_item(file_menu)
        file_menu.AppendSeparator()
        self._create_file_exit_menu_item(file_menu)
        main_menu_bar.Append(file_menu, _("&File"))
        self.file_menu = file_menu

    def _create_file_new_menu(self, file_menu):
        file_new_menu = wx.Menu()
        self._create_file_new_timeline_menu_item(file_new_menu)
        self._create_file_new_numtimeline_menu_item(file_new_menu)
        self._create_file_new_dir_timeline_menu_item(file_new_menu)
        file_menu.AppendMenu(wx.ID_ANY, _("New"), file_new_menu, _("Create a new timeline"))

    def _create_file_new_timeline_menu_item(self, file_new_menu):
        accel = wx.GetStockLabel(wx.ID_NEW, wx.STOCK_WITH_ACCELERATOR|wx.STOCK_WITH_MNEMONIC)
        accel = accel.split("\t", 1)[1]
        file_new_menu.Append(
            wx.ID_NEW, _("File Timeline...") + "\t" + accel, _("File Timeline..."))
        self.shortcut_items[wx.ID_NEW] = file_new_menu.FindItemById(wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self._mnu_file_new_on_click, id=wx.ID_NEW)

    def _create_file_new_numtimeline_menu_item(self, file_new_menu):
        mnu_file_new_numeric = file_new_menu.Append(
            ID_NEW_NUMERIC, _("Numeric Timeline..."), _("Numeric Timeline..."))
        self.shortcut_items[ID_NEW_NUMERIC] = mnu_file_new_numeric
        self.Bind(wx.EVT_MENU, self._mnu_file_new_numeric_on_click, mnu_file_new_numeric)

    def _create_file_new_dir_timeline_menu_item(self, file_new_menu):
        mnu_file_new_dir = file_new_menu.Append(
            ID_NEW_DIR, _("Directory Timeline..."), _("Directory Timeline..."))
        self.shortcut_items[ID_NEW_DIR] = mnu_file_new_dir
        self.Bind(wx.EVT_MENU, self._mnu_file_new_dir_on_click, mnu_file_new_dir)

    def _create_file_open_menu_item(self, file_menu):
        file_menu.Append(
            wx.ID_OPEN, self._add_ellipses_to_menuitem(wx.ID_OPEN),
            _("Open an existing timeline"))
        self.Bind(wx.EVT_MENU, self._mnu_file_open_on_click, id=wx.ID_OPEN)

    def _create_file_open_recent_menu(self, file_menu):
        self.mnu_file_open_recent_submenu = wx.Menu()
        file_menu.AppendMenu(wx.ID_ANY, _("Open &Recent"), self.mnu_file_open_recent_submenu)
        self.update_open_recent_submenu()

    def _create_file_save_as_menu(self, file_menu):
        menu = file_menu.Append(wx.ID_SAVEAS, "", _("Save As..."))
        self.shortcut_items[wx.ID_SAVEAS] = menu
        self.Bind(wx.EVT_MENU, self.mnu_file_save_as_on_click, id=wx.ID_SAVEAS)

    def _create_import_menu_item(self, file_menu):
        mnu_file_import = file_menu.Append(
            ID_IMPORT, _("Import timeline..."), _("Import timeline..."))
        self.shortcut_items[ID_IMPORT] = mnu_file_import
        self.Bind(wx.EVT_MENU, self._mnu_file_import_on_click, mnu_file_import)
        self.menu_controller.add_menu_requiring_writable_timeline(mnu_file_import)

    def _create_file_export_to_image_menu_item(self, file_menu):
        mnu_file_export_view = file_menu.Append(
            ID_EXPORT, _("&Export Current view to Image..."), _("Export the current view to a PNG image"))
        self.shortcut_items[ID_EXPORT] = mnu_file_export_view
        self.menu_controller.add_menu_requiring_timeline(mnu_file_export_view)
        self.Bind(wx.EVT_MENU, self._mnu_file_export_view_on_click, mnu_file_export_view)

    def _create_file_export_to_images_menu_item(self, file_menu):
        mnu_file_export_all = file_menu.Append(
            ID_EXPORT_ALL, _("&Export Whole Timeline to Images..."), _("Export whole Timeline to PNG images"))
        self.shortcut_items[ID_EXPORT_ALL] = mnu_file_export_all
        self.menu_controller.add_menu_requiring_timeline(mnu_file_export_all)
        self.Bind(wx.EVT_MENU, self._mnu_file_export_all_on_click, mnu_file_export_all)

    def _create_file_export_to_svg_menu_item(self, file_menu):
        mnu_file_export_svg = file_menu.Append(
            ID_EXPORT_SVG, _("&Export to SVG..."), _("Export the current view to a SVG image"))
        self.shortcut_items[ID_EXPORT_SVG] = mnu_file_export_svg
        self.menu_controller.add_menu_requiring_timeline(mnu_file_export_svg)
        self.Bind(wx.EVT_MENU, self._mnu_file_export_svg_on_click, mnu_file_export_svg)

    def _create_file_exit_menu_item(self, file_menu):
        file_menu.Append(wx.ID_EXIT, "", _("Exit the program"))
        self.shortcut_items[wx.ID_EXIT] = file_menu.FindItemById(wx.ID_EXIT)
        self.Bind(wx.EVT_MENU, self._mnu_file_exit_on_click, id=wx.ID_EXIT)

    def _create_edit_menu(self, main_menu_bar):
        from timelinelib.wxgui.dialogs.categoryfind import CategoryFindDialog
        def create_category_find_dialog():
            return CategoryFindDialog(self, self.timeline)
        def find(evt):
            self.main_panel.show_searchbar(True)
        def find_categories(evt):
            gui_utils.show_modal(create_category_find_dialog, self.handle_db_error)
        def mouse_in_sidebar():
            if not self.config.show_sidebar:
                return False
            return SidebarProxy(self).mouse_over_sidebar()
        def preferences(evt):
            def edit_function():
                dialog = PreferencesDialog(self, self.config)
                dialog.ShowModal()
                dialog.Destroy()
            safe_locking(self, edit_function)
        def edit_shortcuts(evt):
            def edit_function():
                dialog = ShortcutsEditorDialog(self, self.shortcut_controller)
                dialog.ShowModal()
                dialog.Destroy()
            safe_locking(self, edit_function)
        cbx = False
        items = ((wx.ID_FIND, find, None, cbx),
                 (ID_FIND_CATEGORIES, find_categories, _("Find Categories..."), cbx),
                 None,
                 (wx.ID_PREFERENCES, preferences, None, cbx),
                 (ID_EDIT_SHORTCUTS, edit_shortcuts, _("Shortcuts..."), cbx))
        edit_menu = wx.Menu()
        self._create_menu_items(edit_menu, items)
        main_menu_bar.Append(edit_menu, _("&Edit"))
        self._add_edit_menu_items_to_controller(edit_menu)
        self.edit_menu = edit_menu

    def _add_edit_menu_items_to_controller(self, edit_menu):
        find_item = edit_menu.FindItemById(ID_FIND)
        find_categories_item = edit_menu.FindItemById(ID_FIND_CATEGORIES)
        self.menu_controller.add_menu_requiring_timeline(find_item)
        self.menu_controller.add_menu_requiring_timeline(find_categories_item)
                
    def _create_view_menu(self, main_menu_bar):
        def sidebar(evt):
            self.config.set_show_sidebar(evt.IsChecked())
            if evt.IsChecked():
                self.main_panel.show_sidebar()
            else:
                self.main_panel.hide_sidebar()
        def legend(evt):
            self.config.set_show_legend(evt.IsChecked())
            DrawingAreaProxy(self).show_hide_legend(evt.IsChecked())
        def balloons(evt):
            self.config.set_balloon_on_hover(evt.IsChecked())
            #self.main_panel.balloon_visibility_changed(evt.IsChecked())
            DrawingAreaProxy(self).balloon_visibility_changed(evt.IsChecked())
        def zoomin(evt):
            DrawingAreaProxy(self).zoom_in()
        def zoomout(evt):
            DrawingAreaProxy(self).zoom_out()
        def vert_zoomin(evt):
            DrawingAreaProxy(self).vert_zoom_in()
        def vert_zoomout(evt):
            DrawingAreaProxy(self).vert_zoom_out()
        cbx = True
        items = ((ID_SIDEBAR, sidebar, _("&Sidebar\tCtrl+I"), cbx),
                 (ID_LEGEND, legend, _("&Legend"), cbx),
                 None,
                 (ID_BALLOONS, balloons, _("&Balloons on hover"), cbx),
                 None,
                 (ID_ZOOMIN, zoomin, _("Zoom &In\tCtrl++"), False),
                 (ID_ZOOMOUT, zoomout, _("Zoom &Out\tCtrl+-"), False),
                 (ID_VERT_ZOOMIN, vert_zoomin, _("Vertical Zoom &In\tAlt++"), False),
                 (ID_VERT_ZOOMOUT, vert_zoomout, _("Vertical Zoom &Out\tAlt+-"), False))
        view_menu = wx.Menu()
        self._create_menu_items(view_menu, items)
        self._check_view_menu_items(view_menu)
        self._add_view_menu_items_to_controller(view_menu)
        main_menu_bar.Append(view_menu, _("&View"))
        self.view_menu = view_menu

    def _check_view_menu_items(self, view_menu):
        sidebar_item = view_menu.FindItemById(ID_SIDEBAR)
        legend_item = view_menu.FindItemById(ID_LEGEND)
        balloons_item = view_menu.FindItemById(ID_BALLOONS)
        sidebar_item.Check(self.config.get_show_sidebar())
        legend_item.Check(self.config.get_show_legend())
        balloons_item.Check(self.config.get_balloon_on_hover())

    def _add_view_menu_items_to_controller(self, view_menu):
        sidebar_item = view_menu.FindItemById(ID_SIDEBAR)
        legend_item = view_menu.FindItemById(ID_LEGEND)
        balloons_item = view_menu.FindItemById(ID_BALLOONS)
        self.menu_controller.add_menu_requiring_visible_timeline_view(sidebar_item)
        self.menu_controller.add_menu_requiring_timeline(legend_item)
        self.menu_controller.add_menu_requiring_timeline(balloons_item)

    def _create_timeline_menu(self, main_menu_bar):
        def create_event(evt):
            open_create_event_editor(self, self.config, self.timeline,
                                     self.handle_db_error)
        def edit_event(evt):
            try:
                event_id = self.main_panel.get_id_of_first_selected_event()
                event = self.timeline.find_event_with_id(event_id)
            except IndexError:
                # No event selected so do nothing!
                return
            self.main_panel.open_event_editor(event)
        def duplicate_event(evt):
            try:
                event_id = self.main_panel.get_id_of_first_selected_event()
                event = self.timeline.find_event_with_id(event_id)
            except IndexError:
                # No event selected so do nothing!
                return
            open_duplicate_event_dialog_for_event(self, self.timeline,
                                                  self.handle_db_error, event)
        def set_categoryon_selected(evt):
            def edit_function():
                    self._set_category_to_selected_events()
            safe_locking(self, edit_function)
        def measure_distance(evt):
            self._measure_distance_between_events()
        def set_category_on_without(evt):
            def edit_function():
                self._set_category()
            safe_locking(self, edit_function)
        def edit_categories(evt):
            def edit_function():
                self._edit_categories()
            safe_locking(self, edit_function)
        def set_readonly(evt):
            self.controller.set_timeline_in_readonly_mode()
        def undo(evt):
            safe_locking(self, self.timeline.undo)
            self.main_panel.redraw_timeline()          
        def redo(evt):
            safe_locking(self, self.timeline.redo)
            self.main_panel.redraw_timeline()        
        cbx = False
        items = ((ID_CREATE_EVENT, create_event, _("Create &Event..."), cbx),
                 (ID_EDIT_EVENT, edit_event, _("&Edit Selected Event..."), cbx),
                 (ID_DUPLICATE_EVENT, duplicate_event, _("&Duplicate Selected Event..."), cbx),
                 (ID_SET_CATEGORY_ON_SELECTED, set_categoryon_selected, _("Set Category on Selected Events..."), cbx),
                 None,
                 (ID_MEASURE_DISTANCE, measure_distance, _("&Measure Distance between two Events..."), cbx),
                 None,
                 (ID_SET_CATEGORY_ON_WITHOUT, set_category_on_without, _("Set Category on events &without category..."), cbx),
                 (ID_EDIT_CATEGORIES, edit_categories, _("Edit &Categories"), cbx),
                 None,
                 (ID_SET_READONLY, set_readonly, _("&Read Only"), cbx),
                 None,
                 (ID_UNDO, undo, _("&Undo\tCtrl+Z"), cbx),
                 (ID_REDO, redo, _("&Redo\tAlt+Z"), cbx))
        self.timeline_menu = wx.Menu()
        self._create_menu_items(self.timeline_menu, items)
        self._add_timeline_menu_items_to_controller(self.timeline_menu)
        main_menu_bar.Append(self.timeline_menu, _("&Timeline"))

    def _add_timeline_menu_items_to_controller(self, menu):
        self._add_to_controller_requiring_writeable_timeline(menu, ID_CREATE_EVENT)
        self._add_to_controller_requiring_writeable_timeline(menu, ID_EDIT_EVENT)
        self._add_to_controller_requiring_writeable_timeline(menu, ID_DUPLICATE_EVENT)
        self._add_to_controller_requiring_writeable_timeline(menu, ID_SET_CATEGORY_ON_SELECTED)
        self._add_to_controller_requiring_writeable_timeline(menu, ID_MEASURE_DISTANCE)
        self._add_to_controller_requiring_writeable_timeline(menu, ID_SET_CATEGORY_ON_WITHOUT)
        self._add_to_controller_requiring_writeable_timeline(menu, ID_EDIT_CATEGORIES)
        self._add_to_controller_requiring_writeable_timeline(menu, ID_SET_READONLY)

    def _add_to_controller_requiring_writeable_timeline(self, menu, item_id):
        mnu_item = menu.FindItemById(item_id)
        self.menu_controller.add_menu_requiring_writable_timeline(mnu_item)

    def _create_navigate_menu(self, main_menu_bar):
        def find_first(evt):
            event = self.timeline.get_first_event()
            if event:
                start = event.time_period.start_time
                delta = self.main_panel.get_displayed_period_delta()
                end   = start + delta
                margin_delta = self.timeline.get_time_type().margin_delta(delta)
                self._navigate_timeline(lambda tp: tp.update(start, end, -margin_delta))
        def find_last(evt):
            event = self.timeline.get_last_event()
            if event:
                end = event.time_period.end_time
                delta = self.main_panel.get_displayed_period_delta()
                start = end - delta
                margin_delta = self.timeline.get_time_type().margin_delta(delta)
                self._navigate_timeline(lambda tp: tp.update(start, end, end_delta=margin_delta))
        def fit_all(evt):
            self._fit_all_events()

        cbx = False
        items = ((ID_FIND_FIRST, find_first, _("Find &First Event"), cbx),
                 (ID_FIND_LAST, find_last, _("Find &Last Event"), cbx),
                 (ID_FIT_ALL, fit_all, _("Fit &All Events"), cbx))
        navigate_menu = wx.Menu()
        self._navigation_menu_items = []
        self._navigation_functions_by_menu_item_id = {}
        self.update_navigation_menu_items()
        navigate_menu.AppendSeparator()
        self._create_menu_items(navigate_menu, items)
        self._add_navigate_menu_items_to_controller(navigate_menu)
        main_menu_bar.Append(navigate_menu, _("&Navigate"))
        self.navigate_menu = navigate_menu

    def _add_navigate_menu_items_to_controller(self, menu):
        self._add_to_controller_requiring_timeline(menu, ID_FIND_FIRST)
        self._add_to_controller_requiring_timeline(menu, ID_FIND_LAST)
        self._add_to_controller_requiring_timeline(menu, ID_FIT_ALL)

    def _add_to_controller_requiring_timeline(self, menu, item_id):
        mnu_item = menu.FindItemById(item_id)
        self.menu_controller.add_menu_requiring_timeline(mnu_item)

    def _create_help_menu(self, main_menu_bar):
        def contents(e):
            self.help_browser.show_page("contents")
        def tutorial(e):
            self.controller.open_timeline(":tutorial:")
        def feedback(e):
            show_feedback_dialog(
                parent=None,
                info="",
                subject=_("Feedback"),
                body="")
        def features(e):
            info = self.feedback_featues[e.Id]
            show_feature_feedback_dialog( "x", info, "y")
        def contact(e):
            self.help_browser.show_page("contact")
        def about(e):
            display_about_dialog()
        cbx = False
        items = [(wx.ID_HELP, contents, _("&Contents\tF1"), cbx),
                 None,
                 (ID_TUTORIAL, tutorial, _("Getting started &tutorial"), cbx),
                 None,
                 (ID_FEEDBACK, feedback, _("Give &Feedback..."), cbx),
                 (ID_CONTACT, contact, _("Co&ntact"), cbx),
                 None,
                 (wx.ID_ABOUT, about, None, cbx)]
        help_menu = wx.Menu()
        self._create_menu_items(help_menu, items)
        self._create_menu_features_feedback(help_menu)
        main_menu_bar.Append(help_menu, _("&Help"))
        self.help_menu = help_menu

    def _create_menu_features_feedback(self, help_menu):
        def features(e):
            feature_name = self.feedback_featues[e.Id]
            show_feature_feedback_dialog(feature_name)
        self.feedback_featues = {}
        if len(FEATURES) > 0:
            menu = wx.Menu()
            for item in FEATURES.keys():
                mi = menu.Append(wx.ID_ANY, "%s..." % item)
                self.feedback_featues[mi.GetId()] = item
                self.Bind(wx.EVT_MENU, features, mi)
        help_menu.InsertMenu(5, wx.ID_ANY, "&Give Feedback on Features", menu)

    def display_timeline_context_menu(self):
        try:
            menu = self.context_menu
        except:
            self.context_menu = self._create_timeline_context_menu()
            menu = self.context_menu
        self.PopupMenu(menu)

    def _create_timeline_context_menu(self):
            menu = wx.Menu()
            menu_bar = self.file_menu.GetMenuBar()
            menu.AppendMenu(wx.ID_ANY, menu_bar.GetMenuLabel(0), self.file_menu)
            menu.AppendMenu(wx.ID_ANY, menu_bar.GetMenuLabel(1), self.edit_menu)
            menu.AppendMenu(wx.ID_ANY, menu_bar.GetMenuLabel(2), self.view_menu)
            menu.AppendMenu(wx.ID_ANY, menu_bar.GetMenuLabel(3), self.timeline_menu)
            menu.AppendMenu(wx.ID_ANY, menu_bar.GetMenuLabel(4), self.navigate_menu) 
            menu.AppendMenu(wx.ID_ANY, menu_bar.GetMenuLabel(5), self.help_menu)
            return menu 
        
    def _create_menu_items(self, menu, items):
        menu_items = []
        for item in items:
            if item is not None:
                menu_item = self._create_menu_item(menu, item)
                menu_items.append(menu_item)
            else:
                menu.AppendSeparator()
        return menu_items

    def _create_menu_item(self, menu, item_spec):
        item_id, handler, label, checkbox = item_spec
        if label is not None:
            if checkbox:
                item = menu.Append(item_id, label, kind=wx.ITEM_CHECK)
            else:
                if label is not None:
                    item = menu.Append(item_id, label)
                else:
                    item = menu.Append(item_id)
        else:
            item = menu.Append(item_id)
        self.shortcut_items[item_id] = menu.FindItemById(item_id)
        self.Bind(wx.EVT_MENU, handler, item)
        return item

    def _mnu_file_new_on_click(self, event):
        self._create_new_timeline()

    def _mnu_file_new_numeric_on_click(self, event):
        self._create_new_numeric_timeline()

    def _mnu_file_new_dir_on_click(self, event):
        self._create_new_dir_timeline()

    def _mnu_file_open_on_click(self, event):
        self._open_existing_timeline()

    def mnu_file_save_as_on_click(self, event):
        if self.timeline is not None:
            self._save_as()

    def _mnu_file_import_on_click(self, menu):
        def open_import_dialog():
            dialog = ImportDialog(self.timeline, self)
            dialog.ShowModal()
            dialog.Destroy()
        safe_locking(self, open_import_dialog)

    def _mnu_file_export_view_on_click(self, evt):
        export_to_image(self)

    def _mnu_file_export_all_on_click(self, evt):
        export_to_images(self)

    def _mnu_file_export_svg_on_click(self, evt):
        self._export_to_svg_image()

    def _mnu_file_exit_on_click(self, evt):
        self.Close()

    def _add_ellipses_to_menuitem(self, id):
        plain = wx.GetStockLabel(id,
                wx.STOCK_WITH_ACCELERATOR|wx.STOCK_WITH_MNEMONIC)
        # format of plain 'xxx[\tyyy]', example '&New\tCtrl+N'
        tab_index = plain.find("\t")
        if tab_index != -1:
            return plain[:tab_index] + "..." + plain[tab_index:]
        return plain + "..."


class MainFrameApiUsedByController(object):

    def open_timeline(self, input_file):
        self.controller.open_timeline(input_file)

    def set_timeline_readonly(self):
        self._set_readonly_text_in_status_bar()
        self.enable_disable_menus()

    def handle_db_error(self, error):
        display_error_message(ex_msg(error), self)
        self._switch_to_error_view(error)

    def update_open_recent_submenu(self):
        self._clear_recent_menu_items()
        self._create_recent_menu_items()

    def display_timeline(self, timeline):
        self.timeline = timeline
        self.menu_controller.on_timeline_change(timeline)
        self.main_panel.display_timeline(timeline)
        self._set_title()
        self._set_readonly_text_in_status_bar()

    def update_navigation_menu_items(self):
        self._clear_navigation_menu_items()
        if self.timeline:
            self._create_navigation_menu_items()
            self.shortcut_controller.add_navigation_functions()

    # Also used by TinmelineView
    def enable_disable_menus(self):
        self.menu_controller.enable_disable_menus(self.main_panel.timeline_panel_visible())
        self._enable_disable_one_selected_event_menus()
        self._enable_disable_measure_distance_between_two_events_menu()
        self._enable_disable_searchbar()
        self._enable_disable_undo()

    def _set_title(self):
        if self.timeline == None:
            self.SetTitle(APPLICATION_NAME)
        else:
            self.SetTitle("%s (%s) - %s" % (
                os.path.basename(self.timeline.path),
                os.path.dirname(os.path.abspath(self.timeline.path)),
                APPLICATION_NAME))

    def _set_readonly_text_in_status_bar(self):
        if self.controller.timeline_is_readonly():
            text = _("read-only")
        else:
            text = ""
        self.status_bar_adapter.set_read_only_text(text)

    def _clear_navigation_menu_items(self):
        while self._navigation_menu_items:
            self.navigate_menu.RemoveItem(self._navigation_menu_items.pop())
        self._navigation_functions_by_menu_item_id.clear()

    def _create_navigation_menu_items(self):
        item_data = self.timeline.get_time_type().get_navigation_functions()
        pos = 0
        id_offset = self.get_navigation_id_offset()
        for (itemstr, fn) in item_data:
            if itemstr == "SEP":
                item = self.navigate_menu.InsertSeparator(pos)
            else:
                wxid = ID_NAVIGATE + id_offset
                item = self.navigate_menu.Insert(pos, wxid, itemstr)
                self._navigation_functions_by_menu_item_id[item.GetId()] = fn
                self.Bind(wx.EVT_MENU, self._navigation_menu_item_on_click, item)
                self.shortcut_items[wxid] = item
                id_offset += 1
            self._navigation_menu_items.append(item)
            pos += 1

    def get_navigation_id_offset(self):
        id_offset = 0
        if self.timeline.get_time_type().get_name() == "numtime":
            id_offset = 100
        return id_offset
    
    def _navigation_menu_item_on_click(self, evt):
        fn = self._navigation_functions_by_menu_item_id[evt.GetId()]
        time_period = self.main_panel.get_time_period()
        fn(self, time_period, self._navigate_timeline)

    def _clear_recent_menu_items(self):
        for item in self.mnu_file_open_recent_submenu.GetMenuItems():
            self.mnu_file_open_recent_submenu.DeleteItem(item)

    def _create_recent_menu_items(self):
        self.open_recent_map = {}
        for path in self.config.get_recently_opened():
            self._map_path_to_recent_menu_item(path)

    def _map_path_to_recent_menu_item(self, path):
        name = "%s (%s)" % (
            os.path.basename(path),
            os.path.dirname(os.path.abspath(path)))
        item = self.mnu_file_open_recent_submenu.Append(wx.ID_ANY, name)
        self.open_recent_map[item.GetId()] = path
        self.Bind(wx.EVT_MENU, self._mnu_file_open_recent_item_on_click, item)

    def _mnu_file_open_recent_item_on_click(self, event):
        path = self.open_recent_map[event.GetId()]
        self.controller.open_timeline_if_exists(path)

    def _enable_disable_one_selected_event_menus(self):
        nbr_of_selected_events = self.main_panel.get_nbr_of_selected_events()
        one_event_selected = nbr_of_selected_events == 1
        some_event_selected = nbr_of_selected_events > 0
        mnu_edit_event = self. timeline_menu.FindItemById(ID_EDIT_EVENT)
        mnu_duplicate_event = self. timeline_menu.FindItemById(ID_DUPLICATE_EVENT)
        mnu_set_category = self. timeline_menu.FindItemById(ID_SET_CATEGORY_ON_SELECTED)
        mnu_edit_event.Enable(one_event_selected)
        mnu_duplicate_event.Enable(one_event_selected)
        mnu_set_category.Enable(some_event_selected)
        #self.mnu_timeline_edit_event.Enable(one_event_selected)
        #self.mnu_timeline_duplicate_event.Enable(one_event_selected)
        #self.mnu_timeline_set_event_category.Enable(some_event_selected)

    def _enable_disable_measure_distance_between_two_events_menu(self):
        two_events_selected = self.main_panel.get_nbr_of_selected_events() == 2
        mnu_measure_distance = self.timeline_menu.FindItemById(ID_MEASURE_DISTANCE)
        mnu_measure_distance.Enable(two_events_selected)
        #self.mnu_timeline_measure_distance_between_events.Enable(two_events_selected)

    def _enable_disable_searchbar(self):
        if self.timeline == None:
            self.main_panel.show_searchbar(False)

    def _enable_disable_undo(self):
        mnu_undo = self.timeline_menu.FindItemById(ID_UNDO)
        mnu_redo = self.timeline_menu.FindItemById(ID_REDO)
        if self.timeline is not None:
            mnu_undo.Enable(self.timeline.undo_enabled())
            mnu_redo.Enable(self.timeline.redo_enabled())
        else:
            mnu_undo.Enable(False)
            mnu_redo.Enable(False)
        

class MainFrame(wx.Frame, GuiCreator, MainFrameApiUsedByController):

    def __init__(self, application_arguments):
        self.config = read_config(application_arguments.get_config_file_path())

        wx.Frame.__init__(self, None, size=self.config.get_window_size(),
                          pos=self.config.get_window_pos(),
                          style=wx.DEFAULT_FRAME_STYLE, name="main_frame")

        self.Bind(EVT_CATS_VIEW_CHANGED, self._on_cats_view_changed)
        # To enable translations of wx stock items.
        self.locale = wx.Locale(wx.LANGUAGE_DEFAULT)
        self.help_browser = HelpBrowser(self)
        self.controller = TimelineApplication(self, db_open, self.config)
        self.menu_controller = MenuController()
        self._set_initial_values_to_member_variables()
        self._create_print_data()
        self._create_gui()
        self.Maximize(self.config.get_window_maximized())
        self.SetTitle(APPLICATION_NAME)
        self.SetIcons(self._load_icon_bundle())
        self.main_panel.show_welcome_panel()
        self.enable_disable_menus()
        self.controller.on_started(application_arguments)
        self._create_and_start_timer()

    # API:s used by time types
    def week_starts_on_monday(self):
        return self.controller.week_starts_on_monday()

    def display_time_editor_dialog(self, time_type, initial_time,
                                   handle_new_time_fn, title):
        dialog = TimeEditorDialog(self, self.config, time_type, initial_time, title)
        dialog.ShowModal() 
        result = dialog.GetReturnCode()
        dialog.Destroy()
        if result == wx.ID_OK:
            handle_new_time_fn(dialog.time)

    # Concurrent editing
    def ok_to_edit(self):
        return self.controller.ok_to_edit()

    def edit_ends(self):
        self.controller.edit_ends()

    def _on_cats_view_changed(self, evt):
        self.main_panel.get_view_properties().change_view_cats_individually(evt.GetClientData())

    # Creation process methods
    def _set_initial_values_to_member_variables(self):
        self.timeline = None
        self.timeline_wildcard_helper = WildcardHelper(
            _("Timeline files"), ["timeline", "ics"])
        self.images_svg_wildcard_helper = WildcardHelper(
            _("SVG files"), ["svg"])

    def _create_print_data(self):
        self.printData = wx.PrintData()
        self.printData.SetPaperId(wx.PAPER_A4)
        self.printData.SetPrintMode(wx.PRINT_MODE_PRINTER)
        self.printData.SetOrientation(wx.LANDSCAPE)

    def _create_and_start_timer(self):
        self.alert_dialog_open = False
        self.timer = TimelineTimer(self)
        self.timer.register(self._timer_tick)
        self.timer.start(10000)

    def _timer_tick(self, evt):
        self._handle_event_alerts()

    def _load_icon_bundle(self):
        bundle = wx.IconBundle()
        for size in ["16", "32", "48"]:
            iconpath = os.path.join(ICONS_DIR, "%s.png" % size)
            icon = wx.IconFromBitmap(wx.BitmapFromImage(wx.Image(iconpath)))
            bundle.AddIcon(icon)
        return bundle

    # File Menu action handlers
    def _create_new_timeline(self):
        path = self._get_file_path()
        if path is not None:
            self.controller.open_timeline(path)

    def _create_new_numeric_timeline(self):
        path = self._get_file_path()
        if path is not None:
            timetype = NumTimeType()
            self.controller.open_timeline(path, timetype)

    def _get_file_path(self):
        path = None
        wildcard = self.timeline_wildcard_helper.wildcard_string()
        dialog = wx.FileDialog(self, message=_("Create Timeline"),
                               wildcard=wildcard, style=wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            path = self.timeline_wildcard_helper.get_path(dialog)
            if os.path.exists(path):
                msg_first_part = _("The specified timeline already exists.")
                msg_second_part = _("Opening timeline instead of creating new.")
                wx.MessageBox("%s\n\n%s" % (msg_first_part, msg_second_part),
                              _("Information"),
                              wx.OK|wx.ICON_INFORMATION, self)
        dialog.Destroy()
        return path

    def _create_new_dir_timeline(self):
        dialog = wx.DirDialog(self, message=_("Create Timeline"))
        if dialog.ShowModal() == wx.ID_OK:
            self.controller.open_timeline(dialog.GetPath())
        dialog.Destroy()

    def _open_existing_timeline(self):
        dir = ""
        if self.timeline is not None:
            dir = os.path.dirname(self.timeline.path)
        wildcard = self.timeline_wildcard_helper.wildcard_string()
        dialog = wx.FileDialog(self, message=_("Open Timeline"),
                               defaultDir=dir,
                               wildcard=wildcard, style=wx.FD_OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            self.controller.open_timeline(dialog.GetPath())
        dialog.Destroy()

    def _save_as(self):
        new_timeline_path = self._get_new_timeline_path_from_user()
        self._save_timeline_to_new_path(new_timeline_path)

    def _get_new_timeline_path_from_user(self):
        defaultDir = os.path.dirname(self.timeline.path)
        wildcard_helper = WildcardHelper(_("Timeline files"), ["timeline"])
        wildcard = wildcard_helper.wildcard_string()
        style = wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT
        message = _("Save Timeline As")
        dialog = wx.FileDialog(self, message=message, defaultDir=defaultDir,
                               wildcard=wildcard, style=style)
        if dialog.ShowModal() == wx.ID_OK:
            new_timeline_path = wildcard_helper.get_path(dialog)
        else:
            new_timeline_path = None
        dialog.Destroy()
        return new_timeline_path

    def _save_timeline_to_new_path(self, new_timeline_path):
        if new_timeline_path is not None:
            assert new_timeline_path.endswith(".timeline")
            export_db_to_timeline_xml(self.timeline, new_timeline_path)
            self.controller.open_timeline(new_timeline_path)

    def _export_to_svg_image(self):
        if not self._has_pysvg_module():
            display_error_message(_("Could not find pysvg Python package. It is needed to export to SVG. See the Timeline website or the doc/installing.rst file for instructions how to install it."), self)
            return
        wildcard = self.images_svg_wildcard_helper.wildcard_string()
        dialog = wx.FileDialog(self, message=_("Export to SVG"),
                               wildcard=wildcard, style=wx.FD_SAVE)
        if dialog.ShowModal() == wx.ID_OK:
            path = self.images_svg_wildcard_helper.get_path(dialog)
            overwrite_question = _("File '%s' exists. Overwrite?") % path
            if (not os.path.exists(path) or
                _ask_question(overwrite_question, self) == wx.YES):
                self.main_panel.svgexport(path)
        dialog.Destroy()

    def _has_pysvg_module(self):
        try:
            import pysvg
            return True
        except ImportError:
            return False

    def _window_on_close(self, event):
        self.save_current_timeline_data()
        self._save_application_config()
        self.Destroy()

    def _save_application_config(self):
        self.config.set_window_size(self.GetSize())
        self.config.set_window_pos(self.GetPosition())
        self.config.set_window_maximized(self.IsMaximized())
        self.config.set_sidebar_width(self.main_panel.get_sidebar_width())
        try:
            self.config.write()
        except IOError, ex:
            friendly = _("Unable to write configuration file.")
            msg = "%s\n\n%s" % (friendly, ex_msg(ex))
            display_error_message(msg, self)

    def save_current_timeline_data(self):
        if self.timeline:
            try:
                self.main_panel.save_view_properties(self.timeline)
            except TimelineIOError, e:
                self.handle_db_error(e)

    # Timeline Menu action handlers
    def _measure_distance_between_events(self):
        event1, event2 = self._get_selected_events()
        distance = self.controller.calc_events_distance(event1, event2)
        self._display_distance(distance)

    def _get_selected_events(self):
        event_id_1, event_id_2 = self.main_panel.get_ids_of_two_first_selected_events()
        event1 = self.timeline.find_event_with_id(event_id_1)
        event2 = self.timeline.find_event_with_id(event_id_2)
        return event1, event2

    def _display_distance(self, distance):
        caption = _("Distance between selected events")
        distance_text = self.timeline.get_time_type().format_delta(distance)
        if distance_text == "0":
            distance_text = _("Events are overlapping or distance is 0")
        display_information_message(caption, distance_text)

    def _set_category(self):
        def create_set_category_editor():
            return SetCategoryEditorDialog(self, self.timeline)
        gui_utils.show_modal(create_set_category_editor, self.handle_db_error)
        self.main_panel.redraw_timeline()

    def _set_category_to_selected_events(self):
        selected_event_ids = self.main_panel.get_selected_event_ids()
        def create_set_category_editor():
            return SetCategoryEditorDialog(self, self.timeline, selected_event_ids)
        gui_utils.show_modal(create_set_category_editor, self.handle_db_error)
        self.main_panel.redraw_timeline()

    def _edit_categories(self):
        def create_categories_editor():
            return CategoriesEditor(self, self.timeline)
        gui_utils.show_modal(create_categories_editor, self.handle_db_error)

    # Navigate Menu action handlers
    def _navigate_timeline(self, navigation_fn):
        return self.main_panel.navigate_timeline(navigation_fn)

    def _fit_all_events(self):
        all_period = self._period_for_all_visible_events()
        if all_period == None:
            return
        if all_period.is_period():
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
                return TimePeriod(time_type, start, end).zoom(-1)
            else:
                return None
        except ValueError, ex:
            display_error_message(ex.message)
        return None

    def _all_visible_events(self):
        all_events = self.timeline.get_all_events()
        return self.main_panel.get_visible_events(all_events)

    def _first_time(self, events):
        start_time = lambda event: event.time_period.start_time
        return start_time(min(events, key=start_time))

    def _last_time(self, events):
        end_time = lambda event: event.time_period.end_time
        return end_time(max(events, key=end_time))

    def get_export_periods(self):
        events = self._all_visible_events()
        first_time = self._first_time(events)
        last_time = self._last_time(events)
        return self.main_panel.get_export_periods(first_time, last_time)

    # Error handling
    def _switch_to_error_view(self, error):
        self.controller.set_no_timeline()
        self.main_panel.error_panel.populate(error)
        self.main_panel.show_error_panel()
        self.enable_disable_menus()

    # Timer event handlers
    def _handle_event_alerts(self):
        if self.timeline is None:
            return
        if self.alert_dialog_open:
            return
        self._display_events_alerts()
        self.alert_dialog_open = False

    def _display_events_alerts(self):
        self.alert_dialog_open = True
        all_events = self.timeline.get_all_events()
        AlertController().display_events_alerts(all_events, self.timeline.get_time_type())


class AlertController(object):

    def display_events_alerts(self, all_events, time_type):
        self.time_type = time_type
        for event in all_events:
            alert = event.get_data("alert")
            if alert is not None:
                if self._time_has_expired(alert[0]):
                    self._display_and_delete_event_alert(event, alert)

    def _display_and_delete_event_alert(self, event, alert):
        self._display_alert_dialog(alert, event)
        event.set_data("alert", None)

    def _alert_time_as_text(self, alert):
        return "%s" % alert[0]

    def _time_has_expired(self, time):
        return time <= self.time_type.now()

    def _display_alert_dialog(self, alert, event):
        text = self._format_alert_text(alert, event)
        dialog = TextDisplayDialog("Alert", text)
        dialog.SetWindowStyleFlag(dialog.GetWindowStyleFlag() | wx.STAY_ON_TOP)
        wx.Bell()
        dialog.ShowModal()
        dialog.Destroy()

    def _format_alert_text(self, alert, event):
        text1 = "Trigger time: %s\n\n" % alert[0]
        text2 = "Event: %s\n\n" % event.get_label()
        text = "%s%s%s" % (text1, text2, alert[1])
        return text


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
      * The timeline panel (show_timeline_panel)
      * The error panel (show_error_panel)

    Also displays the search bar.
    """

    def __init__(self, parent, config, main_frame):
        wx.Panel.__init__(self, parent)
        self.config = config
        self.main_frame = main_frame
        self._create_gui()
        # Install variables for backwards compatibility
        self.category_tree = self.timeline_panel.sidebar.category_tree
        self.show_sidebar = self.timeline_panel.show_sidebar
        self.hide_sidebar = self.timeline_panel.hide_sidebar
        self.get_sidebar_width = self.timeline_panel.get_sidebar_width

    def get_export_periods(self, first_time, last_time):
        periods = []
        current_period = None
        if self.main_frame.timeline:
            time_type = self.main_frame.timeline.get_time_type()
            current_period = self.get_view_properties().displayed_period
            period_delta = current_period.end_time - current_period.start_time
            periods.append(current_period)
            start_time = current_period.start_time
            period = current_period
            while first_time < start_time:
                start_time = period.start_time - period_delta
                end_time = period.start_time
                period = TimePeriod(time_type, start_time, end_time)
                periods.insert(0, period)
            end_time = current_period.end_time
            period = current_period
            while last_time > end_time:
                start_time = period.end_time
                end_time = period.end_time + period_delta
                period = TimePeriod(time_type, start_time, end_time)
                periods.append(period)
        return periods, current_period

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
            self.searchbar.set_focus()
        self.GetSizer().Layout()

    def get_current_image(self):
        return self.timeline_panel.get_current_image()

    def _remove_timeline_and_show_welcome_panel(self):
        self.category_tree.set_no_timeline_view()
        self.set_searchbar_timeline_canvas(None)
        self.set_timeline(None)
        self.show_welcome_panel()

    def display_timeline(self, timeline):
        if timeline == None:
            # Do we ever end up here with the welcome panel displayed?
            self._remove_timeline_and_show_welcome_panel()
        else:
            self._show_new_timeline(timeline)

    def _show_new_timeline(self, timeline):
        self.set_timeline(timeline)
        self.category_tree.set_timeline_view(
            self.get_timeline_canvas().get_timeline(),
            self.get_timeline_canvas().get_view_properties())
        self.set_searchbar_timeline_canvas(self.get_timeline_canvas())
        self.show_timeline_panel()

    def set_timeline(self, timeline):
        self.timeline_panel.set_timeline(timeline)

    def get_timeline_canvas(self):
        return self.timeline_panel.get_timeline_canvas()

    def get_scene(self):
        return self.timeline_panel.get_scene()

    def save_view_properties(self, timeline):
        timeline.save_view_properties(self.get_view_properties())

    def get_displayed_period_delta(self):
        return self.get_view_properties().displayed_period.delta()

    def get_time_period(self):
        return self.timeline_panel.get_time_period()

    def get_ids_of_two_first_selected_events(self):
        view_properties = self.get_view_properties()
        return (view_properties.selected_event_ids[0],
                view_properties.selected_event_ids[1])

    def get_selected_event_ids(self):
        return self.get_view_properties().get_selected_event_ids()

    def get_id_of_first_selected_event(self):
        return self.get_view_properties().get_selected_event_ids()[0]

    def get_nbr_of_selected_events(self):
        return len(self.get_view_properties().get_selected_event_ids())

    def open_event_editor(self, event):
        self.timeline_panel.open_event_editor(event)

    def redraw_timeline(self):
        self.timeline_panel.redraw_timeline()

    def navigate_timeline(self, navigation_fn):
        return self.timeline_panel.navigate_timeline(navigation_fn)

    def get_visible_events(self, all_events):
        view_properties = self.get_view_properties()
        visible_events = view_properties.filter_events(all_events)
        return visible_events

    def set_searchbar_timeline_canvas(self, timeline_canvas):
        self.searchbar.set_timeline_canvas(timeline_canvas)

    def svgexport(self, path):
        import timelinelib.dataexport.svg as svgexport
        svgexport.export(
                    path,
                    self.get_scene(),
                    self.get_view_properties())

    def get_view_properties(self):
        return self.timeline_panel.get_view_properties()

    def _create_gui(self):
        # Search bar
        self.searchbar = SearchBar(self)
        self.searchbar.Show(False)
        # Panels
        self.welcome_panel = WelcomePanel(self, self.main_frame)
        self.timeline_panel = TimelinePanel(
            self, self.config, self.main_frame.handle_db_error,
            self.main_frame.status_bar_adapter, self.main_frame)
        self.error_panel = ErrorPanel(self, self.main_frame)
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
        panel.activated()


class WelcomePanel(wx.Panel):

    def __init__(self, parent, main_frame):
        wx.Panel.__init__(self, parent)
        self.main_frame = main_frame
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
        self.main_frame.open_timeline(":tutorial:")

    def activated(self):
        pass


class ErrorPanel(wx.Panel):

    def __init__(self, parent, main_frame):
        wx.Panel.__init__(self, parent)
        self.main_frame = main_frame
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
        self.main_frame.help_browser.show_page("contact")

    def activated(self):
        pass


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
