# Copyright (C) 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018  Rickard Lindberg, Roger Lindberg
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


from timelinelib.calendar.gregorian.time import GregorianTime
from timelinelib.calendar.gregorian.time import GregorianDelta

SECONDS_IN_DAY = 24 * 60 * 60

class PharaonicTime(GregorianTime):
    
    MIN_JULIAN_DAY = -47
    
    @property
    def DeltaClass(self):
        return PharaonicDelta


class PharaonicDelta(GregorianDelta):
    pass
