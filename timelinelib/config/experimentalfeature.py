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


class ExperimentalFeature(object):
    
    def __init__(self, display_name, description):
        self.display_name = display_name
        self.description = description
        self.active = False
    
    def enable(self):
        self.active = True
        
    def disable(self):
        self.active = False
    
    def set_active(self, value):
        self.active = value
        
    def set_value(self, value):
        self.active = value
        
    def enabled(self):
        return self.active
    
    def get_display_name(self):
        return self.display_name
    
    def get_description(self):
        return self.description

    def get_config(self):
        return "%s=%s;" % (self.display_name, str(self.active))
