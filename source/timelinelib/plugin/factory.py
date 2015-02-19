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


import os
import sys
from inspect import isclass


EVENTBOX_DRAWER = "eventboxdrawer"
EXPORTER = "exporter"
VALID_SERVICES = [EVENTBOX_DRAWER, EXPORTER]


class PluginException(Exception):
    pass


class PluginFactory(object):

    def __init__(self):
        self.plugins = {}

    def load_plugins(self):
        candidates = self._get_candidate_modules()
        for candidate in candidates:
            classes = [x for x in dir(candidate) if isclass(getattr(candidate, x))]
            for cl in classes:
                self._save_class_instance_for_plugins(candidate, cl)

    def get_plugins(self, service):
        try:
            return self.plugins[service]
        except:
            pass

    def _save_class_instance_for_plugins(self, candidate, cl):
        class_ = getattr(candidate, cl)
        try:
            instance = class_()
            try:
                self._validate_plugin(instance)
                self._save_plugin(instance)
            except:
                pass
        except:
            pass

    def _import_module(self, module_name):
        __import__(module_name)
        return sys.modules[module_name]

    def _get_candidate_modules(self):
        path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "plugins")
        names = [f.split(".", 1)[0] for f in os.listdir(path) if f.endswith(".py") and not f.startswith("__")]
        return [self._import_module("timelinelib.plugin.plugins.%s" % mod) for mod in names]
        # return [importlib.import_module("timelinelib.plugin.plugins.%s" % mod, package=None) for mod in names]

    def _validate_plugin(self, instance):
        self._get_plugin_method(instance, "isplugin")
        self._get_plugin_method(instance, "service")
        self._get_plugin_method(instance, "display_name")
        if not instance.isplugin():
            print "NP"
            raise PluginException()
        if instance.service() not in VALID_SERVICES:
            print "NVS"
            raise PluginException()

    def _get_plugin_method(self, obj, method_name):
        method = getattr(obj, method_name, None)
        if not callable(method):
            raise PluginException()

    def _save_plugin(self, instance):
        if instance.service() in self.plugins.keys():
            self.plugins[instance.service()].append(instance)
        else:
            self.plugins[instance.service()] = [instance]
