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


from mock import Mock

from timelinelib.canvas.data.db import MemoryDB
from timelinelib.time.gregoriantime import GregorianTimeType
from timelinelib.time.numtime import NumTimeType
from timelinelib.wxgui.dialogs.eraseditor.controller import ErasEditorDialogController
from timelinelib.wxgui.dialogs.eraseditor.view import ErasEditorDialog
from timelinelib.test.cases.unit import UnitTestCase
from timelinelib.test.utils import a_gregorian_era_with
from timelinelib.canvas.data.era import Era


class describe_eras_editor_dialog(UnitTestCase):

    def test_it_can_be_created(self):
        self.show_dialog(ErasEditorDialog, None, self.db, None)

    def test_construction(self):
        self.assertEquals(2, len(self.controller.eras))
        self.assertEquals(self.view, self.controller.view)

    def test_listbox_is_populated_at_construction(self):
        self.view.SetEras.assert_called_with(self.db.get_all_eras())

    def test_delete_removes_era(self):
        era = self.db.get_all_eras()[0]
        self._simulate_delete_button_clicked_on(era)
        self.view.RemoveEra.assert_called_with(era)
        self.assertEquals(self.db.get_all_eras(), self.controller.eras)

    def test_an_era_can_be_added(self):
        count = len(self.db.get_all_eras.return_value)
        era = Mock(Era)
        self.controller._add(era)
        self.view.AppendEra.assert_called_with(era)
        self.db.save_era.assert_called_with(era)
        self.assertEqual(count + 1, len(self.db.get_all_eras.return_value))

    def test_a_date_era_can_be_created(self):
        era = self.controller._create_era()
        self.assertTrue(isinstance(era.get_time_type(), GregorianTimeType))

    def test_a_numeric_era_can_be_created(self):
        self.db.time_type = NumTimeType()
        era = self.controller._create_era()
        self.assertTrue(isinstance(era.get_time_type(), NumTimeType))

    def _simulate_delete_button_clicked_on(self, era):
        self.view.GetSelectedEra.return_value = era
        self.controller.on_remove(None)

    def setUp(self):
        eras = [a_gregorian_era_with(start="1 Jan 2010", end="1 Jan 2020", name="Haha"),
                a_gregorian_era_with(start="1 Jan 2010", end="1 Jan 2020", name="Hey Hey")]
        self.db = Mock(MemoryDB)
        self.db.get_all_eras.return_value = eras
        self.db.time_type = GregorianTimeType()
        self.view = Mock(ErasEditorDialog)
        self.controller = ErasEditorDialogController(self.view)
        self.controller.on_init(self.db, None)
