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
Script that executes all specifications.
"""

import sys
import os.path
import unittest
import gettext
import doctest
import locale

def execute_all_specs():
    setup_paths()
    enable_gettext()
    setup_locale()
    suite = create_suite()
    all_pass = execute_suite(suite)
    return all_pass

def setup_paths():
    # So that the we can write 'import timelinelib.xxx' and 'import specs.xxx'
    root_dir = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, root_dir)

def enable_gettext():
    # So that the _ function is available
    from timelinelib.about import APPLICATION_NAME
    from timelinelib.paths import LOCALE_DIR
    gettext.install(APPLICATION_NAME.lower(), LOCALE_DIR, unicode=True)

def setup_locale():
    # Some specs depend on locale being en_us (date parsing for example)
    locale.setlocale(locale.LC_ALL, "en_US")

def add_spec_from_module(suite, module_name):
    __import__(module_name)
    module = sys.modules[module_name]
    module_suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    suite.addTest(module_suite)

def add_specs(suite):
    for file in os.listdir(os.path.join(os.path.dirname(__file__), "specs")):
        if file.endswith(".py") and file != "__init__.py":
            module_name = os.path.basename(file)[:-3]
            abs_module_name = "specs.%s" % module_name
            add_spec_from_module(suite, abs_module_name)

def add_unittests(suite):
    def add_tests_from_module(module_name):
        __import__(module_name)
        module = sys.modules[module_name]
        module_suite = unittest.defaultTestLoader.loadTestsFromModule(module)
        suite.addTest(module_suite)
    add_tests_from_module("tests.unit.db.objects")
    add_tests_from_module("tests.unit.db.backends.file")
    add_tests_from_module("tests.unit.gui.utils")
    add_tests_from_module("tests.unit.gui.dialogs.mainframe")
    add_tests_from_module("tests.unit.config")
    add_tests_from_module("tests.unit.db.backends.memory")
    add_tests_from_module("tests.integration.read_010_file")
    add_tests_from_module("tests.integration.read_090_file")
    add_tests_from_module("tests.integration.read_0100_file")
    add_tests_from_module("tests.unit.gui.dialogs.duplicateevent")
    add_tests_from_module("tests.unit.gui.components.cattree")
    add_tests_from_module("tests.unit.db.backends.xmlparser")
    add_tests_from_module("tests.integration.read_write_xml")
    add_tests_from_module("tests.integration.write_xml")

def add_doctests(suite):
    def add_tests_from_module(module_name):
        __import__(module_name)
        module = sys.modules[module_name]
        module_suite = doctest.DocTestSuite(module)
        suite.addTest(module_suite)
    add_tests_from_module("timelinelib.db.backends.xmlparser")
    add_tests_from_module("timelinelib.utils")

def create_suite():
    suite = unittest.TestSuite()
    add_specs(suite)
    add_unittests(suite)
    add_doctests(suite)
    return suite

def execute_suite(suite):
    res = unittest.TextTestRunner(verbosity=1).run(suite)
    return res.wasSuccessful()

if __name__ == '__main__':
    all_pass = execute_all_specs()
    if all_pass:
        sys.exit(0)
    else:
        sys.exit(1)
