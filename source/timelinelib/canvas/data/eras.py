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


from timelinelib.canvas.data.idnumber import get_process_unique_id
from timelinelib.canvas.data.timeperiod import TimePeriod


class InvalidOperationError(Exception):
    pass


class Eras(object):
    """
    The list of all eras defined for a timeline.

    Contains function for cloning of the whole list which is a
    necessary operation for undo/redo operations.
    """

    def __init__(self, eras=None):
        if eras is None:
            self._eras = []
        else:
            self._eras = eras

    def clone(self):
        return Eras(clone_era_list(self._eras))

    def get_all(self):
        return sorted(self._eras)

    def get_in_period(self, time_period):
        def include_era(era):
            if not era.inside_period(time_period):
                return False
            return True
        return [e for e in self._eras if include_era(e)]

    def save_era(self, era):
        self._ensure_era_exists_for_update(era)
        if era not in self._eras:
            self._eras.append(era)
            era.set_id(get_process_unique_id())

    def delete_era(self, era):
        if era not in self._eras:
            raise InvalidOperationError("era not in db.")
        self._eras.remove(era)
        era.set_id(None)

    def get_all_periods(self):

        def get_key(e):
            return e.get_time_period().start_time

        def merge_colors(c1, c2):
            return ((c1[0] + c2[0]) / 2, (c1[1] + c2[1]) / 2, (c1[2] + c2[2]) / 2)

        def create_overlapping_era(e0, e1, start, end):
            era = e1.clone()
            era.set_time_period(TimePeriod(e0.get_time_type(), start, end))
            era.set_color(merge_colors(e0.get_color(), e1.get_color()))
            era.set_name("Era Overlap")
            return era

        def get_start_and_end_times(e0, e1):
            e0start = e0.get_time_period().start_time
            e0end = e0.get_time_period().end_time
            e1start = e1.get_time_period().start_time
            e1end = e1.get_time_period().end_time
            return e0start, e0end, e1start, e1end

        def return_era_for_overlapping_type_1(e0, e1):
            e0start, e0end, e1start, e1end = get_start_and_end_times(e0, e1)
            era = create_overlapping_era(e0, e1, e1start, e0end)
            e0.set_time_period(TimePeriod(e0.get_time_type(), e0start, e1start))
            e1.set_time_period(TimePeriod(e0.get_time_type(), e0end, e1end))
            return era

        def return_era_for_overlapping_type_2(e0, e1):
            e0start, e0end, _, e1end = get_start_and_end_times(e0, e1)
            era = create_overlapping_era(e0, e1, e0start, e0end)
            self.all_eras.remove(e0)
            e1.set_time_period(TimePeriod(e0.get_time_type(), e0end, e1end))
            return era

        def return_era_for_overlapping_type_3(e0, e1):
            return return_era_for_overlapping_type_2(e1, e0)

        def return_era_for_overlapping_type_4(e0, e1):
            _, _, e1start, e1end = get_start_and_end_times(e0, e1)
            era = create_overlapping_era(e0, e1, e1start, e1end)
            self.all_eras.remove(e0)
            self.all_eras.remove(e1)
            return era

        def return_era_for_overlapping_type_5(e0, e1):
            e0start, _, e1start, e1end = get_start_and_end_times(e0, e1)
            era = create_overlapping_era(e0, e1, e1start, e1end)
            e0.set_time_period(TimePeriod(e0.get_time_type(), e0start, e1start))
            self.all_eras.remove(e1)
            return era

        def return_era_for_overlapping_type_6(e0, e1):
            e0start, e0end, e1start, e1end = get_start_and_end_times(e0, e1)
            era = create_overlapping_era(e0, e1, e1start, e1end)
            e0.set_time_period(TimePeriod(e0.get_time_type(), e0start, e1start))
            e1.set_time_period(TimePeriod(e0.get_time_type(), e1end, e0end))
            e1.set_name(e0.get_name())
            e1.set_color(e0.get_color())
            return era

        def clone_all_eras():
            return [e.clone() for e in self.get_all()]

        overlap_func = (None,
                        return_era_for_overlapping_type_1,
                        return_era_for_overlapping_type_2,
                        return_era_for_overlapping_type_3,
                        return_era_for_overlapping_type_4,
                        return_era_for_overlapping_type_5,
                        return_era_for_overlapping_type_6)

        def create_overlapping_era_and_remove_hidden_eras():
            """
            self.all_eras is always sorted by Era start time.
            This method finds the first pair of Era's that overlaps.
            If such a pair is found, a overlapping Era is created and added
            to the the self.all_eras list. If any or both of the original
            Era's are hidden by the overlapping Era, they are removed from
            the self.all_eras list.
            When one overlapping pair has been found and processed the
            function returns False, after updating the self.all_eras list
            If no overlapping pairs of Era's are found the function retuns
            True.
            """
            e0 = self.all_eras[0]
            for e1 in self.all_eras[1:]:
                strategy = e0.overlapping(e1)
                if strategy > 0:
                    self.all_eras.append(overlap_func[strategy](e0, e1))
                    self.all_eras = sorted(self.all_eras, key=get_key)
                    return False
                else:
                    e0 = e1
            return True

        self.all_eras = clone_all_eras()
        if self.all_eras == []:
            return []
        while True:
            if len(self.all_eras) > 0:
                done = create_overlapping_era_and_remove_hidden_eras()
            else:
                done = True
            if done:
                return self.all_eras

    def _ensure_era_exists_for_update(self, era):
        message = "Updating an era that does not exist."
        if era.has_id():
            if not self._does_era_exists(era):
                raise InvalidOperationError(message)

    def _does_era_exists(self, an_era):
        for stored_era in self.get_all():
            if stored_era.get_id() == an_era.get_id():
                return True
        return False


def clone_era_list(eralist):
    eras = []
    for era in eralist:
        new_era = era.clone()
        new_era.set_id(era.get_id())
        eras.append(new_era)
    return eras