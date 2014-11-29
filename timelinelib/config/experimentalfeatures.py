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


from timelinelib.config.experimentalfeaturedone import ExperimentalFeatureDone
from timelinelib.config.experimentalfeaturecontainersize import ExperimentalFeatureContainerSize


EVENT_DONE = ExperimentalFeatureDone()
EXTENDED_CONTAINER_HEIGHT = ExperimentalFeatureContainerSize()
FEATURES = (EVENT_DONE, EXTENDED_CONTAINER_HEIGHT)


class ExperimentalFeatureException(Exception):
    pass


class ExperimentalFeatures(object):
    
    def __str__(self):
        """
        Formats the configuration string for all experimental features,
        which is a semicolon separated list of feature configurations.
           features-configuration ::= (feature-configuration ';')*
           feature-configuration ::=  feature-name  '='  ('True'|'False')
        """
        collector = []
        for feature in FEATURES:
            collector.append(feature.get_config())
        return "".join(collector)
    
    def get_all_features(self):
        return FEATURES

    def set_active_state_on_all_features_from_config_string(self, cfg_string):
        for item in cfg_string.split(";"):
            if "=" in item:
                name, value = item.split("=")
                self._set_active_state_on_feature_by_name(name.strip(), value.strip() == "True")
    
    def set_active_state_on_feature_by_index(self, feature_index, value):
        FEATURES[feature_index].set_active(value)
            
    def _set_active_state_on_feature_by_name(self, name, value):
        for feature in FEATURES:
            if feature.get_display_name() == name:
                feature.set_value(value)
                return
            

def experimental_feature(feature):
    """
    Decorator used for methods, only used by an Experimental feature.
    The purpose of the decorator is to simplify removal of the feature
    code if it is decided not to implement the feature.
    Example:
       @experimental_feature(EVENT_DONE)
       def foo()
           pass
    """
    def deco(foo):
        if not feature in FEATURES:
            raise ExperimentalFeatureException("Feature '%s', not implemented" % feature.get_display_name())
        return foo
    return deco
