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


import os
import subprocess

import timelinetools.packaging.archive


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))


class Repository(object):

    def __init__(self, root=REPO_ROOT):
        self.root = root

    def archive(self, revision, destination_dir, name):
        subprocess.check_call([
            "hg", "archive",
            "-r", revision,
            "-R", self.root,
            "--no-decode",
            "--exclude", "%s/.hg*" % (self.root or "."),
            os.path.join(destination_dir, name)
        ])
        revision_hash = self._get_revision_hash(revision)
        revision_date = self._get_revision_date(revision_hash)
        archive = timelinetools.packaging.archive.Archive(destination_dir, name)
        archive.change_revision(revision_hash, revision_date)
        return archive

    def _get_revision_hash(self, revision):
        return subprocess.check_output([
            "hg", "id",
            "-i",
            "-r", revision,
            "-R", self.root,
        ]).strip()

    def _get_revision_date(self, revision):
        return subprocess.check_output([
            "hg", "log",
            "-r", revision,
            "-R", self.root,
            "--template", "{date|shortdate}",
        ]).strip()
