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


from timelinelib.dataimport.timelinexml import import_db_from_timeline_xml
from timelinetest import TmpDirTestCase


class describe_import_timeline_xml(TmpDirTestCase):

    def test_can_import_empty_file(self):
        db = self.import_file_with_content("""
        <timeline>
            <version>0.0.0</version>
            <categories />
            <events />
            <view />
        </timeline>
        """.strip())

    def import_file_with_content(self, content):
        path = self.get_tmp_path("tmp.timeline")
        with open(path, "w") as f:
            f.write(content)
        return import_db_from_timeline_xml(path)
