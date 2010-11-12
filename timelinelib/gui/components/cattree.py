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


import wx
import wx.lib.agw.customtreectrl as customtreectrl

from timelinelib.utils import version_str_to_tuple
import timelinelib.gui.utils as gui_utils
from timelinelib.gui.utils import category_tree
from timelinelib.gui.utils import ID_ERROR
from timelinelib.gui.utils import _ask_question
from timelinelib.gui.dialogs.categoryeditor import CategoryEditor
from timelinelib.db.interface import TimelineIOError
from timelinelib.db.interface import STATE_CHANGE_CATEGORY


NO_CHECKBOX_TYPE = 0
CHECKBOX_TYPE = 1


class CategoriesTree(customtreectrl.CustomTreeCtrl):
    """
    Display categories in tree and provide editing functions.
    
    If this control is initialized with initialize_from_timeline_view then the
    visibility of categories can also be altered using check boxes. A context
    menu is always available that can be used to edit, add, and delete
    categories.
    """

    def __init__(self, parent, fn_handle_db_error):
        style = wx.BORDER_SUNKEN
        agwStyle = (customtreectrl.TR_HIDE_ROOT |
                    customtreectrl.TR_HAS_VARIABLE_ROW_HEIGHT |
                    customtreectrl.TR_LINES_AT_ROOT |
                    customtreectrl.TR_HAS_BUTTONS)
        if version_str_to_tuple(wx.__version__) < (2, 8, 11, 0):
            customtreectrl.CustomTreeCtrl.__init__(self, parent, style=style|agwStyle)
        else:
            customtreectrl.CustomTreeCtrl.__init__(self, parent, style=style, agwStyle=agwStyle)
        self._create_gui()
        self.controller = CategoriesTreeController(self, fn_handle_db_error)

    def initialize_from_db(self, db):
        self.controller.initialize_from_db(db)

    def initialize_from_timeline_view(self, view):
        self.controller.initialize_from_timeline_view(view)

    def set_category_tree(self, tree, view_properties):
        self.DeleteAllItems()
        self.root = self.AddRoot("") # Hidden because of TR_HIDE_ROOT
        self._update_categories_from_tree(tree, self.root, view_properties)
        self.ExpandAll()

    def get_selected_category(self):
        item = self.GetSelection()
        if item is None:
            return None
        category = self.GetPyData(item)
        return category

    def destroy(self):
        self.controller.destroy()

    def _create_gui(self):
        # Context menu
        self.mnu = wx.Menu()
        self.mnu_edit = wx.MenuItem(self.mnu, wx.ID_ANY, _("Edit..."))
        self.Bind(wx.EVT_MENU, self._mnu_edit_on_click, self.mnu_edit)
        self.mnu.AppendItem(self.mnu_edit)
        self.mnu_add = wx.MenuItem(self.mnu, wx.ID_ANY, _("Add..."))
        self.Bind(wx.EVT_MENU, self._mnu_add_on_click, self.mnu_add)
        self.mnu.AppendItem(self.mnu_add)
        self.mnu_delete = wx.MenuItem(self.mnu, wx.ID_ANY, _("Delete"))
        self.Bind(wx.EVT_MENU, self._mnu_delete_on_click, self.mnu_delete)
        self.mnu.AppendItem(self.mnu_delete)
        # Events on control
        self.Bind(customtreectrl.EVT_TREE_ITEM_CHECKED,
                  self._on_tree_item_checked, self)
        self.Bind(wx.EVT_RIGHT_DOWN, self._on_right_down)
        self.Bind(wx.EVT_KEY_DOWN, self._on_key_down)

    def _update_menu_enableness(self):
        enable_if_item = [self.mnu_edit, self.mnu_delete]
        enable = self.get_selected_category() is not None
        for menu_item in enable_if_item:
            menu_item.Enable(enable)

    def _update_categories_from_tree(self, tree, root_item, view_properties):
        for (cat, subtree) in tree:
            legend_panel = wx.Panel(self, size=(10, 10))
            legend_panel.SetBackgroundColour(cat.color)
            if view_properties:
                ct_type = CHECKBOX_TYPE
            else:
                ct_type = NO_CHECKBOX_TYPE
            item = self.AppendItem(root_item, cat.name, ct_type=ct_type,
                                   wnd=legend_panel, data=cat)
            if view_properties:
                visible = view_properties.category_visible(cat)
                self.CheckItem2(item, visible)
            self._update_categories_from_tree(subtree, item, view_properties)
        
    def _on_right_down(self, e):
        (item, flags) = self.HitTest(e.GetPosition())
        if item is not None:
            self.SelectItem(item, True)
        self._update_menu_enableness()
        self.PopupMenu(self.mnu)

    def _on_key_down(self, e):
        keycode = e.GetKeyCode()
        if keycode == wx.WXK_DELETE:
            self.controller.delete_selected_category()
        e.Skip()

    def _mnu_add_on_click(self, e):
        self.controller.add_category()

    def _mnu_edit_on_click(self, e):
        self.controller.edit_selected_category()

    def _mnu_delete_on_click(self, e):
        self.controller.delete_selected_category()

    def _on_tree_item_checked(self, e):
        tree_item = e.GetItem()
        cat = tree_item.GetData()
        tree_item_checked = tree_item.IsChecked()
        self.controller.check_category(cat, tree_item_checked)


class CategoriesTreeController(object):

    def __init__(self, view, fn_handle_db_error):
        self.view = view
        self.db = None
        self.timeline_view = None
        self.fn_handle_db_error = fn_handle_db_error

    def initialize_from_db(self, db):
        self._change_active_db(db)
        self.timeline_view = None
        self._update_category_tree()

    def initialize_from_timeline_view(self, view):
        if view is None:
            new_timeline = None
        else:
            new_timeline = view.get_timeline()
        self._change_active_db(new_timeline)
        self.timeline_view = view
        self._update_category_tree()

    def add_category(self):
        add_category(self.view, self.db, self.fn_handle_db_error)

    def edit_selected_category(self):
        cat = self.view.get_selected_category()
        if cat:
            edit_category(self.view, self.db, cat, self.fn_handle_db_error)

    def delete_selected_category(self):
        cat = self.view.get_selected_category()
        if cat:
            delete_category(self.view, self.db, cat, self.fn_handle_db_error)

    def check_category(self, cat, checked):
        if self.timeline_view is None:
            raise Exception("Checking not allowed when there is no "
                            "timeline view.")
        self.timeline_view.get_view_properties().set_category_visible(cat, checked)
        self.timeline_view.redraw_timeline()

    def destroy(self):
        if self.db:
            self.db.unregister(self._db_on_changed)

    def _change_active_db(self, new_db):
        if self.db:
            self.db.unregister(self._db_on_changed)
        self.db = new_db
        if self.db:
            self.db.register(self._db_on_changed)

    def _db_on_changed(self, state_change):
        if state_change == STATE_CHANGE_CATEGORY:
            self._update_category_tree()

    def _update_category_tree(self):
        try:
            if self.db:
                categories = self.db.get_categories()
            else:
                categories = []
        except TimelineIOError, e:
            self.fn_handle_db_error(e)
        else:
            tree = category_tree(categories)
            if self.timeline_view:
                vp = self.timeline_view.get_view_properties()
            else:
                vp = None
            self.view.set_category_tree(tree, vp)


def edit_category(parent_ctrl, db, cat, fn_handle_db_error):
    """Open category editor to edit the given category."""
    def create_category_editor():
        return CategoryEditor(parent_ctrl, _("Edit Category"), db, cat)
    gui_utils.show_modal(create_category_editor, fn_handle_db_error)


def add_category(parent_ctrl, db, fn_handle_db_error):
    """Open category editor to create a new category."""
    def create_category_editor():
        return CategoryEditor(parent_ctrl, _("Add Category"), db, None)
    gui_utils.show_modal(create_category_editor, fn_handle_db_error)


def delete_category(parent_ctrl, db, cat, fn_handle_db_error):
    """Delete the given category after given confirmation from user."""
    delete_warning = _("Are you sure you want to "
                       "delete category '%s'?") % cat.name
    if cat.parent is None:
        update_warning = _("Events belonging to '%s' will no longer "
                           "belong to a category.") % cat.name
    else:
        update_warning = _("Events belonging to '%s' will now belong "
                           "to '%s'.") % (cat.name, cat.parent.name)
    question = "%s\n\n%s" % (delete_warning, update_warning)
    if _ask_question(question, parent_ctrl) == wx.YES:
        try:
            db.delete_category(cat)
        except TimelineIOError, e:
            fn_handle_db_error(e)
