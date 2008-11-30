"""
Contains algorithms for drawing a timeline.
"""

import logging
from datetime import timedelta

import wx


class DrawingAlgorithm(object):
    """Base class for timeline drawing algorithms."""

    def draw(self, dc, time_period, events):
        """
        This is the interface.

        dc - used to do the actual drawing
        time_period - what period should of the timeline should be visible
        events - events inside time_period that should be drawn

        When the dc is temporarily stored in a class variable such as self.dc,
        this class variable must be deleted before the draw method ends.
        """
        pass


class Metrics(object):
    """Helper class that can calculate coordinates."""

    def __init__(self, dc, time_period):
        self.dc = dc
        self.width, self.height = dc.GetSizeTuple()
        self.time_period = time_period

    def get_x(self, time):
        # This is really ugly, but it works relatively well. If the / operator
        # were defined for timedelta this method could be written much simpler.
        pixperiod = self.time_period.delta() / self.width
        deltatotime = time - self.time_period.start_time
        tempdelta = timedelta()
        x = 0
        if tempdelta < deltatotime:
            # positive
            while tempdelta <= deltatotime:
                x += 1
                tempdelta += pixperiod
        else:
            # negative
            while tempdelta >= deltatotime:
                x -= 1
                tempdelta -= pixperiod
        return x

    def get_width(self, time_period):
        return self.get_x(time_period.end_time) - self.get_x(time_period.start_time)

    def half_height(self):
        return self.height / 2


def setup_drawing_algorithm(drawing_algorithm):
    global _drawing_algorithm
    _drawing_algorithm = drawing_algorithm


from drawing_simple1 import SimpleDrawingAlgorithm1
from drawing_simple2 import SimpleDrawingAlgorithm2


def get_algorithm():
    """Factory method."""
    return _drawing_algorithms.get(_drawing_algorithm, SimpleDrawingAlgorithm1)()
    

_drawing_algorithm  = None
_drawing_algorithms = {'simple1': SimpleDrawingAlgorithm1,
                       'simple2': SimpleDrawingAlgorithm2}