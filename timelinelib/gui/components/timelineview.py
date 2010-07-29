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


from datetime import datetime as dt
from datetime import timedelta

import wx

from timelinelib.db.interface import TimelineIOError
from timelinelib.db.interface import STATE_CHANGE_ANY
from timelinelib.db.objects import time_period_center
from timelinelib.drawing.interface import ViewProperties
from timelinelib.drawing.utils import mult_timedelta
from timelinelib.drawing import get_drawer
from timelinelib.gui.utils import sort_categories
from timelinelib.gui.utils import _ask_question
from timelinelib.gui.utils import _step_function
from timelinelib.gui.utils import _display_error_message
import timelinelib.config as config
import timelinelib.printing as printing
from timelinelib.utils import ex_msg


# Used by Sizer and Mover classes to detect when to go into action
HIT_REGION_PX_WITH = 5

# The width in pixels of the vertical scroll zones.
# When the mouse reaches the any of the two scroll zone areas, scrolling 
# of the timeline will take place if there is an ongoing selection of the 
# timeline. The scroll zone areas are found at the beginning and at the
# end of the timeline.
SCROLL_ZONE_WIDTH = 20

# dragscroll timer interval in milliseconds
DRAGSCROLL_TIMER_MSINTERVAL = 300

# Identification of the object in play when dragging
DRAG_NONE   = 0
DRAG_MOVE   = 1
DRAG_SIZE   = 2
DRAG_SELECT = 3


class EventSizer(object):
    """Objects of this class are used to simplify resizing of events."""

    _singletons = {}
    _initialized = False
    
    def __new__(cls, *args, **kwds):
        """Implement the Singleton pattern for this class."""
        if cls not in cls._singletons:
            cls._singletons[cls] = super(EventSizer, cls).__new__(cls)
        return cls._singletons[cls]    
    
    def __init__(self, drawing_area, m_x = 0, m_y = 0):
        if not EventSizer._initialized:
            self.direction = wx.LEFT
            self.drawing_area = drawing_area
            self.metrics = self.drawing_area.get_drawer().metrics
            self.sizing = False
            self.event = None
            EventSizer._initialized = True
        self.metrics = self.drawing_area.get_drawer().metrics

    def sizing_starts(self, m_x, m_y):
        """
        If it is ok to start a resize... initialize the resize and return True.
        Otherwise return False.
        """
        self.sizing = (self._hit(m_x, m_y) and 
                       self.drawing_area.get_view_properties().is_selected(self.event))
        if self.sizing:
            self.x = m_x
            self.y = m_y
        return self.sizing

    def is_sizing(self):
        """Return True if we are in a resizing state, otherwise return False."""
        return self.sizing

    def set_cursor(self, m_x, m_y):
        """
        Used in mouse-move events to set the size cursor before the left mouse
        button is pressed, to indicate that a resize is possible (if it is!).
        Return True if the size-indicator-cursor is set, otherwise return False.
        """
        hit = self._hit(m_x, m_y)
        if hit:
            is_selected = self.drawing_area.get_view_properties().is_selected(self.event)
            if not is_selected:
                return False
            self.drawing_area.set_size_cursor()
        else:
            self.drawing_area.set_default_cursor()
        return hit

    def _hit(self, m_x, m_y):
        """
        Calculate the 'hit-for-resize' coordinates and return True if
        the mouse is within this area. Otherwise return False.
        The 'hit-for-resize' area is the are at the left and right edges of the
        event rectangle with a width of HIT_REGION_PX_WITH.
        """
        event_info = self.drawing_area.get_drawer().event_with_rect_at(m_x, m_y)
        if event_info == None:
            return False
        self.event, rect = event_info
        if abs(m_x - rect.X) < HIT_REGION_PX_WITH:
            self.direction = wx.LEFT
            return True
        elif abs(rect.X + rect.Width - m_x) < HIT_REGION_PX_WITH:
            self.direction = wx.RIGHT
            return True
        return False

    def resize(self, m_x):
        """
        Resize the event either on the left or the right side.
        The event edge is snapped to the grid.
        """
        time = self.metrics.get_time(m_x)
        time = self.drawing_area.get_drawer().snap(time)
        resized = False
        if self.direction == wx.LEFT:
            resized = self.event.update_start(time)
        else:
            resized = self.event.update_end(time)
        if resized:
            self.drawing_area.redraw_timeline()


class EventMover(object):
    """Objects of this class are used to simplify moving of events."""

    _singletons = {}
    _initialized = False
    
    def __new__(cls, *args, **kwds):
        """Implement the Singleton pattern for this class."""
        if cls not in cls._singletons:
            cls._singletons[cls] = super(EventMover, cls).__new__(cls)
        return cls._singletons[cls]    
    
    def __init__(self, drawing_area):
        """Initialize only the first time the class constructor is called."""
        if not EventMover._initialized:
            self.drawing_area = drawing_area
            self.drawing_algorithm = self.drawing_area.get_drawer()
            self.moving = False
            self.event = None
            EventMover._initialized = True

    def move_starts(self, m_x, m_y):
        """
        If it is ok to start a move... initialize the move and return True.
        Otherwise return False.
        """
        self.moving = (self._hit(m_x, m_y) and 
                       self.drawing_area.get_view_properties().is_selected(self.event))
        if self.moving:
            self.x = m_x
            self.y = m_y
        return self.moving
        
    def is_moving(self):
        """Return True if we are in a moving state, otherwise return False."""
        return self.moving

    def set_cursor(self, m_x, m_y):
        """
        Used in mouse-move events to set the move cursor before the left mouse
        button is pressed, to indicate that a move is possible (if it is!).
        Return True if the move-indicator-cursor is set, otherwise return False.
        """
        hit = self._hit(m_x, m_y)
        if hit:
            is_selected = self.drawing_area.get_view_properties().is_selected(self.event) 
            if not is_selected:
                return False
            self.drawing_area.set_move_cursor()
        else:
            self.drawing_area.set_default_cursor()
        return hit

    def move(self, m_x):
        """
        Move the event the time distance, difftime, represented by the distance the
        mouse has moved since the last move (m_x - self.x).
        Events found above the center line are snapped to the grid.
        """
        difftime = self.drawing_algorithm.metrics.get_difftime(m_x, self.x)
        # Snap events found above the center line
        start = self.event.time_period.start_time + difftime
        end = self.event.time_period.end_time + difftime
        if not self.drawing_algorithm.event_is_period(self.event.time_period):
            halfperiod = (end - start) / 2
            middletime = self.drawing_algorithm.snap(start + halfperiod)
            start = middletime - halfperiod
            end = middletime + halfperiod
        else:
            width = start - end
            startSnapped = self.drawing_area.get_drawer().snap(start)
            endSnapped = self.drawing_area.get_drawer().snap(end)
            if startSnapped != start:
                # Prefer to snap at left edge (in case end snapped as well)
                start = startSnapped
                end = start - width
            elif endSnapped != end:
                end = endSnapped
                start = end + width
        # Update and redraw the event
        self.event.update_period(start, end)
        self.drawing_area.redraw_timeline()
        # Adjust the coordinates  to get a smooth movement of cursor and event.
        # We can't use event_with_rect_at() method to get hold of the rect since
        # events can jump over each other when moved.
        rect = self.drawing_algorithm.event_rect(self.event)
        if rect != None:
            self.x = rect.X + rect.Width / 2
        else:
            self.x = m_x

    def _hit(self, m_x, m_y):
        """
        Calculate the 'hit-for-move' coordinates and return True if
        the mouse is within this area. Otherwise return False.
        The 'hit-for-move' area is the are at the center of an event
        with a width of 2 * HIT_REGION_PX_WITH.
        """
        event_info = self.drawing_area.get_drawer().event_with_rect_at(m_x, m_y)
        if event_info == None:
            return False
        self.event, rect = event_info
        center = rect.X + rect.Width / 2
        if abs(m_x - center) <= HIT_REGION_PX_WITH:
            return True
        return False


class DrawingArea(wx.Panel):

    def __init__(self, parent, divider_line_slider, fn_handle_db_error):
        wx.Panel.__init__(self, parent, style=wx.NO_BORDER)
        self.controller = DrawingAreaController(self, divider_line_slider, fn_handle_db_error)
        self.surface_bitmap = None
        self._create_gui()

    def get_drawer(self):
        return self.controller.get_drawer()

    def get_timeline(self):
        return self.controller.get_timeline()

    def get_view_properties(self):
        return self.controller.get_view_properties()

    def get_current_image(self):
        return self.surface_bitmap

    def print_timeline(self, event):
        self.controller.print_timeline(event)

    def print_preview(self, event):
        self.controller.print_preview(event)

    def print_setup(self, event):
        self.controller.print_setup(event)

    def set_timeline(self, timeline):
        self.controller.set_timeline(timeline)

    def show_hide_legend(self, show):
        self.controller.show_hide_legend(show)

    def get_time_period(self):
        return self.controller.get_time_period()

    def navigate_timeline(self, navigation_fn):
        self.controller.navigate_timeline(navigation_fn)

    def redraw_timeline(self):
        self.controller.redraw_timeline()

    def set_size_cursor(self):
        self.controller.set_size_cursor()

    def set_move_cursor(self):
        self.controller.set_move_cursor()

    def set_default_cursor(self):
        self.controller.set_default_cursor()

    def balloon_visibility_changed(self, visible):
        self.controller.balloon_visibility_changed(visible)

    def redraw_surface(self, fn_draw):
        width, height = self.GetSizeTuple()
        self.surface_bitmap = wx.EmptyBitmap(width, height)
        memdc = wx.MemoryDC()
        memdc.SelectObject(self.surface_bitmap)
        memdc.BeginDrawing()
        memdc.SetBackground(wx.Brush(wx.WHITE, wx.SOLID))
        memdc.Clear()
        fn_draw(memdc)
        memdc.EndDrawing()
        del memdc
        self.Refresh()
        self.Update()

    def enable_disable_menus(self):
        wx.GetTopLevelParent(self).enable_disable_menus()

    def display_text_in_statusbar(self, text):
        wx.GetTopLevelParent(self).SetStatusText(text)

    def _create_gui(self):
        self.Bind(wx.EVT_ERASE_BACKGROUND, self._window_on_erase_background)
        self.Bind(wx.EVT_PAINT, self._window_on_paint)

    def _window_on_erase_background(self, event):
        # For double buffering
        pass

    def _window_on_paint(self, event):
        dc = wx.AutoBufferedPaintDC(self)
        dc.BeginDrawing()
        if self.surface_bitmap:
            dc.DrawBitmap(self.surface_bitmap, 0, 0, True)
        else:
            pass # TODO: Fill with white?
        dc.EndDrawing()


class DrawingAreaController(object):
    """
    The right part in TimelinePanel: a window on which the timeline is drawn.

    This class has information about what timeline and what part of the
    timeline to draw and makes sure that the timeline is redrawn whenever it is
    needed.

    Double buffering is used to avoid flicker while drawing. This is
    accomplished by always drawing to a background buffer: bgbuf. The paint
    method of the control thus only draws the background buffer to the screen.

    Scrolling and zooming of the timeline is implemented in this class. This is
    done whenever the mouse wheel is scrolled (_window_on_mousewheel).
    Moving also takes place when the mouse is dragged while pressing the left
    mouse key (_window_on_motion).

    Selection of a period on the timeline (period = any number of minor strips)
    is also implemented in this class. A selection is done in the following
    way: Press and hold down the Control key on the keyboard, move the mouse to
    the first minor strip to be selected and then press and hold down the left
    mouse key. Now, while moving the mouse over the timeline, the minor strips
    will be selected.

    What happens is that when the left mouse button is pressed
    (_window_on_left_down) the variable self._current_time is set to the
    time on the timeline where the mouse is. This is the anchor point for the
    selection. When the mouse is moved (_window_on_motion) and left mouse button
    is pressed and the Control key is held down the method
    self._mark_selected_minor_strips(evt.m_x) is called. This method marks all
    minor strips between the anchor point and the current point (evt.m_x).
    When the mouse button is released the selection ends.
    """

    def __init__(self, view, divider_line_slider, fn_handle_db_error):
        self.view = view
        self.divider_line_slider = divider_line_slider
        self.fn_handle_db_error = fn_handle_db_error
        self._create_gui()
        self._set_initial_values_to_member_variables()
        self._set_colors_and_styles()
        self.printData = wx.PrintData()
        self.printData.SetPaperId(wx.PAPER_A4)
        self.printData.SetPrintMode(wx.PRINT_MODE_PRINTER)
        self.printData.SetOrientation(wx.LANDSCAPE)

    def get_drawer(self):
        return self.drawing_algorithm

    def get_timeline(self):
        return self.timeline

    def get_view_properties(self):
        return self.view_properties

    def print_timeline(self, event):
        pdd = wx.PrintDialogData(self.printData)
        pdd.SetToPage(1)
        printer = wx.Printer(pdd)
        printout = printing.TimelinePrintout(self.view, False)
        frame = wx.GetApp().GetTopWindow()
        if not printer.Print(frame, printout, True):
            if printer.GetLastError() == wx.PRINTER_ERROR:
                wx.MessageBox(_("There was a problem printing.\nPerhaps your current printer is not set correctly?"), _("Printing"), wx.OK)
        else:
            self.printData = wx.PrintData( printer.GetPrintDialogData().GetPrintData() )
        printout.Destroy()

    def print_preview(self, event):
        data = wx.PrintDialogData(self.printData)
        printout_preview  = printing.TimelinePrintout(self.view, True)
        printout = printing.TimelinePrintout(self.view, False)
        self.preview = wx.PrintPreview(printout_preview, printout, data)
        if not self.preview.Ok():
            return
        frame = wx.GetApp().GetTopWindow()
        pfrm = wx.PreviewFrame(self.preview, frame, _("Print preview"))
        pfrm.Initialize()
        pfrm.SetPosition(frame.GetPosition())
        pfrm.SetSize(frame.GetSize())
        pfrm.Show(True)

    def print_setup(self, event):
        psdd = wx.PageSetupDialogData(self.printData)
        psdd.CalculatePaperSizeFromId()
        dlg = wx.PageSetupDialog(self.view, psdd)
        dlg.ShowModal()
        # this makes a copy of the wx.PrintData instead of just saving
        # a reference to the one inside the PrintDialogData that will
        # be destroyed when the dialog is destroyed
        self.printData = wx.PrintData( dlg.GetPageSetupData().GetPrintData() )
        dlg.Destroy()

    def set_timeline(self, timeline):
        """Inform what timeline to draw."""
        if self.timeline != None:
            self.timeline.unregister(self._timeline_changed)
        self.timeline = timeline
        if self.timeline:
            self.timeline.register(self._timeline_changed)
            try:
                self.view_properties.clear_db_specific()
                timeline.load_view_properties(self.view_properties)
                if self.view_properties.displayed_period is None:
                    default_tp = time_period_center(dt.now(), timedelta(days=30))
                    self.view_properties.displayed_period = default_tp
            except TimelineIOError, e:
                self.fn_handle_db_error(e)
                return
            self._redraw_timeline()
            self.view.Enable()
            self.view.SetFocus()
        else:
            self.view.Disable()

    def show_hide_legend(self, show):
        self.view_properties.show_legend = show
        if self.timeline:
            self._redraw_timeline()

    def get_time_period(self):
        """Return currently displayed time period."""
        if self.timeline == None:
            raise Exception(_("No timeline set"))
        return self.view_properties.displayed_period

    def navigate_timeline(self, navigation_fn):
        """
        Perform a navigation operation followed by a redraw.

        The navigation_fn should take one argument which is the time period
        that should be manipulated in order to carry out the navigation
        operation.

        Should the navigation operation fail (max zoom level reached, etc) a
        message will be displayed in the statusbar.

        Note: The time period should never be modified directly. This method
        should always be used instead.
        """
        if self.timeline == None:
            raise Exception(_("No timeline set"))
        try:
            navigation_fn(self.view_properties.displayed_period)
            self._redraw_timeline()
            self.view.display_text_in_statusbar("")
        except (ValueError, OverflowError), e:
            self.view.display_text_in_statusbar(ex_msg(e))

    def redraw_timeline(self):
        self._redraw_timeline()

    def _create_gui(self):
        self.view.Bind(wx.EVT_SIZE, self._window_on_size)
        self.view.Bind(wx.EVT_LEFT_DOWN, self._window_on_left_down)
        self.view.Bind(wx.EVT_RIGHT_DOWN, self._window_on_right_down)
        self.view.Bind(wx.EVT_LEFT_DCLICK, self._window_on_left_dclick)
        self.view.Bind(wx.EVT_MIDDLE_UP, self._window_on_middle_up)
        self.view.Bind(wx.EVT_LEFT_UP, self._window_on_left_up)
        self.view.Bind(wx.EVT_ENTER_WINDOW, self._window_on_enter)
        self.view.Bind(wx.EVT_MOTION, self._window_on_motion)
        self.view.Bind(wx.EVT_MOUSEWHEEL, self._window_on_mousewheel)
        self.view.Bind(wx.EVT_KEY_DOWN, self._window_on_key_down)
        self.view.Bind(wx.EVT_KEY_UP, self._window_on_key_up)
        self.divider_line_slider.Bind(wx.EVT_SLIDER, self._slider_on_slider)
        self.divider_line_slider.Bind(wx.EVT_CONTEXT_MENU,
                                      self._slider_on_context_menu)

    def _window_on_size(self, event):
        """
        Event handler used when the window has been resized.

        Called at the application start and when the frame is resized.

        Here we create a new background buffer with the new size and draw the
        timeline onto it.
        """
        self._redraw_timeline()

    def _window_on_left_down(self, evt):
        """
        Event handler used when the left mouse button has been pressed.

        This event establishes a new current time on the timeline.

        If the mouse hits an event that event will be selected.
        """
        self.mouse_x = evt.m_x
        try:
            self._set_new_current_time(evt.m_x)
            # If we hit the event resize area of an event, start resizing
            if EventSizer(self.view).sizing_starts(evt.m_x, evt.m_y):
                return
            # If we hit the event move area of an event, start moving
            if EventMover(self.view).move_starts(evt.m_x, evt.m_y):
                return
            # No resizing or moving of events...
            if not self.timeline.is_read_only():
                eventWithBalloon = self.drawing_algorithm.balloon_at(evt.m_x, evt.m_y)
                if eventWithBalloon: 
                    stick = not self.view_properties.event_has_sticky_balloon(eventWithBalloon)
                    self.view_properties.set_event_has_sticky_balloon(eventWithBalloon, has_sticky=stick)
                    if stick:
                        self._redraw_timeline()
                    else:
                        # This makes the sticky balloon unsticky
                        if self.view_properties.show_balloons_on_hover:
                            self._redraw_balloons(eventWithBalloon)
                        # This makes the balloon disapear
                        else:
                            self._redraw_balloons(None)
                else:        
                    posAtEvent = self._toggle_event_selection(evt.m_x, evt.m_y,
                                                              evt.m_controlDown)
                    if evt.m_controlDown:
                        self._set_select_period_cursor()
            evt.Skip()
        except TimelineIOError, e:
            self.fn_handle_db_error(e)

    def _window_on_right_down(self, evt):
        """
        Event handler used when the right mouse button has been pressed.

        If the mouse hits an event and the timeline is not readonly, the 
        context menu for that event is displayed.
        """
        if self.timeline.is_read_only():
            return
        self.context_menu_event = self.drawing_algorithm.event_at(evt.m_x, evt.m_y)
        if self.context_menu_event is None:
            return
        menu_definitions = [
            (_("Edit"), self._context_menu_on_edit_event),
            (_("Duplicate..."), self._context_menu_on_duplicate_event),
            (_("Delete"), self._context_menu_on_delete_event),
        ]
        if self.context_menu_event.has_data():
            menu_definitions.append((_("Sticky Balloon"), self._context_menu_on_sticky_balloon_event))
        menu = wx.Menu()
        for menu_definition in menu_definitions:
            text, method = menu_definition
            menu_item = wx.MenuItem(menu, wx.NewId(), text)
            self.view.Bind(wx.EVT_MENU, method, id=menu_item.GetId())
            menu.AppendItem(menu_item)
        self.view.PopupMenu(menu)
        menu.Destroy()
        
    def _context_menu_on_edit_event(self, evt):
        frame = wx.GetTopLevelParent(self.view)
        frame.edit_event(self.context_menu_event)

    def _context_menu_on_duplicate_event(self, evt):
        frame = wx.GetTopLevelParent(self.view)
        frame.duplicate_event(self.context_menu_event)
        
    def _context_menu_on_delete_event(self, evt):
        self.context_menu_event.selected = True
        self._delete_selected_events()

    def _context_menu_on_sticky_balloon_event(self, evt):
        self.view_properties.set_event_has_sticky_balloon(self.context_menu_event, has_sticky=True)
        self._redraw_timeline()
    
    def _window_on_left_dclick(self, evt):
        """
        Event handler used when the left mouse button has been double clicked.

        If the timeline is readonly, no action is taken.
        If the mouse hits an event, a dialog opens for editing this event. 
        Otherwise a dialog for creating a new event is opened.
        """
        self.mouse_x = evt.m_x
        if self.timeline.is_read_only():
            return
        # Since the event sequence is, 1. EVT_LEFT_DOWN  2. EVT_LEFT_UP
        # 3. EVT_LEFT_DCLICK we must compensate for the toggle_event_selection
        # that occurs in the handling of EVT_LEFT_DOWN, since we still want
        # the event(s) selected or deselected after a left doubleclick
        # It doesn't look too god but I havent found any other way to do it.
        self._toggle_event_selection(evt.m_x, evt.m_y, evt.m_controlDown)
        event = self.drawing_algorithm.event_at(evt.m_x, evt.m_y)
        if event:
            wx.GetTopLevelParent(self.view).edit_event(event)
        else:
            wx.GetTopLevelParent(self.view).create_new_event(self._current_time,
                                                        self._current_time)

    def _window_on_middle_up(self, evt):
        """
        Event handler used when the middle mouse button has been clicked.

        This will recenter the timeline to the area clicked on.
        """
        self._set_new_current_time(evt.m_x)
        self.navigate_timeline(lambda tp: tp.center(self._current_time))

    def _window_on_left_up(self, evt):
        """
        Event handler used when the left mouse button has been released.

        If there is an ongoing selection-marking, the dialog for creating an
        event will be opened, and the selection-marking will be ended.
        """
        if self.dragscroll_timer_running:
            self._stop_dragscroll_timer()
        self.mouse_x = evt.m_x
        if self.is_selecting:
            self._end_selection_and_create_event(evt.m_x)
        if self.is_zooming:
            self._end_selection_and_zoom(evt.m_x)
        self.is_selecting = False
        self.is_scrolling = False
        self.set_default_cursor()

    def _window_on_enter(self, evt):
        """
        Mouse event handler, when the mouse is entering the window.
        
        If there is an ongoing selection-marking (dragscroll timer running)
        and the left mouse button is not down when we enter the window, we 
        want to simulate a 'mouse left up'-event, so that the dialog for 
        creating an event will be opened or sizing, moving stops. 
        """
        if self.dragscroll_timer_running:
            if not evt.LeftIsDown():
                self._window_on_left_up(evt)

    def _window_on_motion(self, evt):
        """
        Event handler used when the mouse has been moved.

        If the mouse is over an event, the name of that event will be printed
        in the status bar.

        If the left mouse key is down one of two things happens depending on if
        the Control key is down or not. If it is down a selection-marking takes
        place and the minor strips passed by the mouse will be selected.  If
        the Control key is up the timeline will scroll.
        """
        self.mouse_x = evt.m_x
        if evt.m_leftDown:
            self._mouse_drag(evt.m_x, evt.m_y, evt.m_controlDown, evt.m_shiftDown)
        else:
            if not evt.m_controlDown:
                self._mouse_move(evt.m_x, evt.m_y)                
                
    def _mouse_drag(self, x, y, ctrl=False, shift=False):
        """
        The mouse has been moved.
        The left mouse button is depressed
        ctrl indicates if the Ctrl-key is depressed or not
        """
        if self.is_scrolling:
            self._scroll(x)
        elif self.is_selecting:
            self._mark_selected_minor_strips(x)
        # Resizing is only allowed if timeline is not readonly    
        elif EventSizer(self.view).is_sizing() and not self.timeline.is_read_only():
            EventSizer(self.view).resize(x)
            if self._in_scroll_zone(x):
                if not self.dragscroll_timer_running:
                    self._start_dragscroll_timer(DRAG_SIZE)

        # Moving is only allowed if timeline is not readonly    
        elif EventMover(self.view).is_moving() and not self.timeline.is_read_only():
            EventMover(self.view).move(x)
            if self._in_scroll_zone(x):
                if not self.dragscroll_timer_running:
                    self._start_dragscroll_timer(DRAG_MOVE)
        else:
            # Marking strips is only allowed if timeline is not readonly    
            if ctrl and not self.timeline.is_read_only():
                self._mark_selected_minor_strips(x)
                self.is_selecting = True
            elif shift:
                self._mark_selected_minor_strips(x)
                self.is_zooming = True
            else:
                self._scroll(x)
                self.is_scrolling = True
    
    def _mouse_move(self, x, y):
        """
        The mouse has been moved.
        The left mouse button is not depressed
        The Ctrl-key is not depressed
        """
        self._display_balloon_on_hover(x, y)
        self._display_eventinfo_in_statusbar(x, y)
        cursor_set = EventSizer(self.view).set_cursor(x, y)
        if not cursor_set:
            EventMover(self.view).set_cursor(x, y)
                
    def _window_on_mousewheel(self, evt):
        """
        Event handler used when the mouse wheel is rotated.

        If the Control key is pressed at the same time as the mouse wheel is
        scrolled the timeline will be zoomed, otherwise it will be scrolled.
        If the Shift key is pressed then the slider will scroll.
        """
        direction = _step_function(evt.m_wheelRotation)
        if evt.ControlDown():
            self._zoom_timeline(direction)
        elif evt.ShiftDown():
            self.divider_line_slider.SetValue(self.divider_line_slider.GetValue() + direction)
            self._redraw_timeline()
        else:
            self._scroll_timeline_view(direction)

    def _window_on_key_down(self, evt):
        """
        Event handler used when a keyboard key has been pressed.

        The following keys are handled:
        Key         Action
        --------    ------------------------------------
        Delete      Delete any selected event(s)
        Control     Change cursor
        """
        keycode = evt.GetKeyCode()
        if keycode == wx.WXK_DELETE:
            self._delete_selected_events()
        evt.Skip()

    def _window_on_key_up(self, evt):
        keycode = evt.GetKeyCode()
        if keycode == wx.WXK_CONTROL:
            self.set_default_cursor()

    def _slider_on_slider(self, evt):
        """The divider-line slider has been moved."""
        self._redraw_timeline()

    def _slider_on_context_menu(self, evt):
        """A right click has occured in the divider-line slider."""
        menu = wx.Menu()
        menu_item = wx.MenuItem(menu, wx.NewId(), _("Center"))
        self.view.Bind(wx.EVT_MENU, self._context_menu_on_menu_center,
                  id=menu_item.GetId())
        menu.AppendItem(menu_item)
        self.view.PopupMenu(menu)
        menu.Destroy()

    def _context_menu_on_menu_center(self, evt):
        """The 'Center' context menu has been selected."""
        self.divider_line_slider.SetValue(50)
        self._redraw_timeline()

    def _timeline_changed(self, state_change):
        if state_change == STATE_CHANGE_ANY:
            self._redraw_timeline()

    def _set_initial_values_to_member_variables(self):
        """
        Instance variables usage:

        _current_time       This variable is set to the time on the timeline
                            where the mouse button is clicked when the left
                            mouse button is used
        timeline            The timeline currently handled by the application
        view_properties     Runtime properties for this view
        drawing_algorithm   The algorithm used to draw the timeline
        bgbuf               The bitmap to which the drawing methods draw the
                            timeline. When the EVT_PAINT occurs this bitmap
                            is painted on the screen. This is a buffer drawing
                            approach for avoiding screen flicker.
        is_scrolling        True when scrolling with the mouse takes place.
                            It is set True in mouse_has_moved and set False
                            in left_mouse_button_released.
        is_selecting        True when selecting with the mouse takes place
                            It is set True in mouse_has_moved and set False
                            in left_mouse_button_released.
        timer1_running      Indicates if the balloon-timer-1 is running.
        timer2_running      Indicates if the balloon-timer-2 is running.
        mouse_x             The current pixel position of the mouse
        drag_object         The id of the object in play when dragging
        dragscroll_timer_running
                            Indicates if the drag-scroll-timer is running.
        """
        self._current_time = None
        self.drawing_algorithm = get_drawer()
        self.is_scrolling = False
        self.is_selecting = False
        self.is_zooming = False
        self.timeline = None
        self.view_properties = ViewProperties()
        self.view_properties.show_legend = config.get_show_legend()
        self.view_properties.show_balloons_on_hover = config.get_balloon_on_hover()
        self.timer1_running = False
        self.timer2_running = False
        self.mouse_x = 0
        self.drag_object = DRAG_NONE
        self.dragscroll_timer_running = False
        
    def _set_colors_and_styles(self):
        """Define the look and feel of the drawing area."""
        self.view.SetBackgroundColour(wx.WHITE)
        self.view.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.set_default_cursor()
        self.view.Disable()

    def _redraw_timeline(self, period_selection=None):
        def fn_draw(dc):
            try:
                self.drawing_algorithm.draw(dc, self.timeline, self.view_properties)
            except TimelineIOError, e:
                self.fn_handle_db_error(e)
        if self.timeline:
            self.view_properties.period_selection = period_selection
            self.view_properties.divider_position = (self.divider_line_slider.GetValue())
            self.view_properties.divider_position = (float(self.divider_line_slider.GetValue()) / 100.0)
            self.view.redraw_surface(fn_draw)
            self.view.enable_disable_menus()

    def _scroll(self, xpixelpos):
        if self._current_time:
            delta = (self.drawing_algorithm.metrics.get_time(xpixelpos) -
                        self._current_time)
            self._scroll_timeline(delta)

    def _set_new_current_time(self, current_x):
        self._current_time = self.drawing_algorithm.metrics.get_time(current_x)

    def _toggle_event_selection(self, xpixelpos, ypixelpos, control_down):
        """
        If the given position is within the boundaries of an event that event
        will be selected or unselected depending on the current selection
        state of the event. If the Control key is down all other events
        selection state are preserved. This means that previously selected
        events will stay selected. If the Control key is not down all other
        events will be unselected.

        If the given position isn't within an event all selected events will
        be unselected.

        Return True if the given position was within an event, otherwise
        return False.
        """
        event = self.drawing_algorithm.event_at(xpixelpos, ypixelpos)
        if event:
            selected = not self.view_properties.is_selected(event)
            if not control_down:
                self.view_properties.clear_selected()
            self.view_properties.set_selected(event, selected)
        else:
            self.view_properties.clear_selected()
        self._redraw_timeline()
        return event != None

    def _end_selection_and_create_event(self, current_x):
        period_selection = self._get_period_selection(current_x)
        start, end = period_selection
        wx.GetTopLevelParent(self.view).create_new_event(start, end)
        self._redraw_timeline()

    def _end_selection_and_zoom(self, current_x):
        self.is_zooming = False
        start, end = self._get_period_selection(current_x)
        td = end - start
        if (td.seconds > 3600) or (td.days > 0):
            """
            Don't zoom in to less than an hour which upsets things.
            """
            self.navigate_timeline(lambda tp: tp.update(start, end))
        self._redraw_timeline()

    def _display_eventinfo_in_statusbar(self, xpixelpos, ypixelpos):
        """
        If the given position is within the boundaries of an event, the name of
        that event will be displayed in the status bar, otherwise the status
        bar text will be removed.
        """
        event = self.drawing_algorithm.event_at(xpixelpos, ypixelpos)
        if event != None:
            self.view.display_text_in_statusbar(event.get_label())
        else:
            self.view.display_text_in_statusbar("")
            
    def _display_balloon_on_hover(self, xpixelpos, ypixelpos):
        """
        Show or hide balloons depending on current situation.
           self.current_event: The event pointed to, or None
           self.balloon_event: The event that belongs to the balloon pointed
                               to, or None.
        """
        # The balloon functionality is not enabled
        if not self.view_properties.show_balloons_on_hover:
            return
        self.current_event = self.drawing_algorithm.event_at(xpixelpos, ypixelpos)
        self.balloon_event = self.drawing_algorithm.balloon_at(xpixelpos, ypixelpos)
        # No balloon handling for selected events
        if self.current_event and self.view_properties.is_selected(self.current_event):
            return
        # Timer-1 is running. We have to wait for it to finish before doing anything
        if self.timer1_running:
            return
        # Timer-2 is running. We have to wait for it to finish before doing anything
        if self.timer2_running:
            return
        # We are pointing to an event... 
        if self.current_event is not None:
            # We are not pointing on a balloon...
            if self.balloon_event is None:
                # We have no balloon, so we start Timer-1
                if self.view_properties.hovered_event != self.current_event:
                    #print "Timer-1 Started ", self.current_event
                    self.timer1 = wx.Timer(self.view, -1)
                    self.view.Bind(wx.EVT_TIMER, self._on_balloon_timer1, 
                              self.timer1)
                    self.timer1.Start(milliseconds = 500, oneShot = True)
                    self.timer1_running = True
        # We are not pointing to any event....        
        else:
            # We have a balloon...
            if self.view_properties.hovered_event is not None:
                # When we are moving within our 'own' balloon we dont't start Timer-2
                # Otherwise Timer-2 is started.
                if self.balloon_event != self.view_properties.hovered_event:
                    #print "Timer-2 Started"
                    self.timer2 = wx.Timer(self.view, -1)
                    self.view.Bind(wx.EVT_TIMER, self._on_balloon_timer2, 
                              self.timer2)
                    self.timer2.Start(milliseconds = 100, oneShot = True)
                    
    def _on_balloon_timer1(self, event):
        """
        Timer-1 has timed out, which means we are ready to display the balloon
        for the current event.
        """
        self.timer1_running = False
        self._redraw_balloons(self.current_event)

    def _on_balloon_timer2(self, event):
        """
        Timer-2 has timed out, which means we are ready to delete the current
        balloon if we are no longer pointing to the current event or it's
        balloon.
        """
        self.timer2_running = False
        hevt = self.view_properties.hovered_event
        # If there is no balloon visible we don't have to do anything
        if hevt is None:
            return
        cevt = self.current_event
        bevt = self.balloon_event
        # If the visible balloon doesn't belong to the event pointed to
        # we remove the ballloon.
        if hevt != cevt and hevt != bevt: 
            self._redraw_balloons(None)
    
    def _redraw_balloons(self, event):
        self.view_properties.hovered_event = event
        self._redraw_timeline()
        
    def _mark_selected_minor_strips(self, current_x):
        """Selection-marking starts or continues."""
        period_selection = self._get_period_selection(current_x)
        self._redraw_timeline(period_selection)
        if self._in_scroll_zone(current_x):
            if not self.dragscroll_timer_running:
                self._start_dragscroll_timer(DRAG_SELECT)

    def _in_scroll_zone(self, x):
        """
        Return True if x is within the left hand or right hand area
        where timed scrolling shall start/continue.
        """
        width, height = self.view.GetSizeTuple()
        if width - x < SCROLL_ZONE_WIDTH or x < SCROLL_ZONE_WIDTH:
            return True
        return False
        
    def _on_dragscroll(self, event):
        """
        Timer event handler that scrolls the timeline.
        
        If the mouse is still in the autoscroll zone continue
        scrolling, otherwise stop the timer.
        """
        if not self._in_scroll_zone(self.mouse_x):
            self._stop_dragscroll_timer()
        else:    
            if self.mouse_x < SCROLL_ZONE_WIDTH:
                direction = 1
            else:
                direction = -1
            self._scroll_timeline_view(direction)
            if (self.drag_object == DRAG_MOVE):
                EventMover(self.view).move(self.mouse_x)
            elif (self.drag_object == DRAG_SIZE):
                EventSizer(self.view).resize(self.mouse_x)
            elif (self.drag_object == DRAG_SELECT):
                self._mark_selected_minor_strips(self.mouse_x)

    def _start_dragscroll_timer(self, drag_object):
        self.dragscroll_timer_running = True
        self.drag_object = drag_object
        self.dragscroll_timer = wx.Timer(self.view, -1)
        self.view.Bind(wx.EVT_TIMER, self._on_dragscroll, self.dragscroll_timer)
        self.dragscroll_timer.Start(milliseconds=DRAGSCROLL_TIMER_MSINTERVAL)

    def _stop_dragscroll_timer(self):
        self.dragscroll_timer_running = False
        self.drag_object = DRAG_NONE
        self.dragscroll_timer.Stop()
        
    def _scroll_timeline_view(self, direction):
            delta = mult_timedelta(self.view_properties.displayed_period.delta(), direction / 10.0)
            self._scroll_timeline(delta)

    def _scroll_timeline(self, delta):
        self.navigate_timeline(lambda tp: tp.move_delta(-delta))

    def _zoom_timeline(self, direction=0):
        self.navigate_timeline(lambda tp: tp.zoom(direction))

    def _delete_selected_events(self):
        """After acknowledge from the user, delete all selected events."""
        selected_event_ids = self.view_properties.get_selected_event_ids()
        nbr_of_selected_event_ids = len(selected_event_ids)
        if nbr_of_selected_event_ids > 1:
            text = _("Are you sure you want to delete %d events?" % 
                     nbr_of_selected_event_ids)
        else:
            text = _("Are you sure you want to delete this event?")
        if _ask_question(text, self.view) == wx.YES:
            try:
                for event_id in selected_event_ids:
                    self.timeline.delete_event(event_id)
            except TimelineIOError, e:
                self.fn_handle_db_error(e)

    def _get_period_selection(self, current_x):
        """Return a tuple containing the start and end time of a selection."""
        start = self._current_time
        end   = self.drawing_algorithm.metrics.get_time(current_x)
        if start > end:
            start, end = end, start
        period_selection = self.drawing_algorithm.snap_selection((start,end))
        return period_selection

    def _set_select_period_cursor(self):
        self.view.SetCursor(wx.StockCursor(wx.CURSOR_IBEAM))

    def _set_drag_cursor(self):
        self.view.SetCursor(wx.StockCursor(wx.CURSOR_HAND))

    def set_size_cursor(self):
        self.view.SetCursor(wx.StockCursor(wx.CURSOR_SIZEWE))

    def set_move_cursor(self):
        self.view.SetCursor(wx.StockCursor(wx.CURSOR_SIZING))

    def set_default_cursor(self):
        """
        Set the cursor to it's default shape when it is in the timeline
        drawing area.
        """
        self.view.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

    def balloon_visibility_changed(self, visible):
        self.view_properties.show_balloons_on_hover = visible
        # When display on hovering is disabled we have to make sure 
        # that any visible balloon is removed.
        # TODO: Do we really need that?
        if not visible:
            self._redraw_timeline()
