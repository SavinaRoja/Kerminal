# encoding: utf-8

from npyscreen.wgwidget import Widget
from npyscreen import TitleText, Textfield
from npyscreen.wgmultiline import MultiLine

import weakref
import curses
from functools import wraps
import logging
import time
import sys

log = logging.getLogger('kerminal.widget_bases')

#I see one major drawback with this approach, as opposed to simply using a
#special Form to extend any Widget into a LiveWidget, which is that one must
#explicitly create a new class for each npyscreen widget you want to use in
#order to inherit the LiveWidget functionality
class LiveWidget(Widget):
    """
    The LiveWidget differs from the Widget in only one substantial way: it has
    built-in support for a `feed` method which may be passed in with the "feed"
    keyword argument during instantiation, or modified elsewhere. Whenever
    `LiveWidget.feed` is called, it's return will be assigned to
    `LiveWidget.value` (no need to write this assignment yourself).

    Scheduling the calling of `LiveWidget.feed` is up to the designer. One motif
    of interest is using a special Form class to register LiveWidgets and then
    calling their feeds during `while_waiting`.
    """

    def __init__(self, screen, feed=None, *args, **kwargs):
        super(LiveWidget, self).__init__(screen, *args, **kwargs)
        if feed is not None:
            self.feed = feed

    def _feed(self):
        """
        The internal method for `feed`. This must simply return an appropriate
        value to be assigned to `LiveWidget.value`.
        """
        return ''

    @property
    def feed(self):
        """
        The method for updating the LiveWidget's value. Customize your widget by
        setting this to a function that returns the desired value from a live
        data source.
        """
        def _feed_wrapper(f):
            @wraps(f)
            def wrapper(*args, **kwds):
                self.value = f(*args, **kwds)
            return wrapper
        return _feed_wrapper(self._feed)

    @feed.setter
    def feed(self, func):
        if not callable(func):
            raise ValueError('LiveWidget.feed must be assigned a callable')
        self._feed = func


class LiveTitleText(TitleText, LiveWidget):
    pass


class LiveTextfield(Textfield, LiveWidget):
    pass


class ResettingLiveWidget(Widget):
    """
    This kind of live widget is distinguished from LiveWidget in that it is
    configured to return its value to a preset one after a certain length of
    time. Its interface for changing the feed is essentially the same as
    LiveWidget.
    """
    VALUE_PREFIX = 'INFO: '
    RESET_TIME = 5.0

    def __init__(self, screen, feed=None, *args, **kwargs):
        super(ResettingLiveWidget, self).__init__(screen, *args, **kwargs)
        if feed is not None:
            self.feed = feed

    def _feed(self):
        """
        The internal method for `feed`. This must simply return an appropriate
        value to be assigned to `LiveWidget.value`.
        """
        return self.VALUE_PREFIX

    @property
    def feed(self):
        """
        The method for updating the LiveWidget's value. Customize your widget by
        setting this to a function that returns the desired value from a live
        data source.
        """
        def _feed_wrapper(f):
            @wraps(f)
            def wrapper(*args, **kwds):
                self.value = f(*args, **kwds)
            return wrapper

        return _feed_wrapper(self._feed)

    @feed.setter
    def feed(self, val):
        #If this gets a value instead of a function, turn it into a function
        if not callable(val):
            func = lambda: val
            #raise ValueError('ResettingLiveWidget.feed must be assigned a callable')
        else:
            func = val

        def _feed_timeout(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                now = time.time()
                if (now - wrapper.started) > self.RESET_TIME:
                    return self.VALUE_PREFIX
                else:
                    return self.VALUE_PREFIX + f(*args, **kwargs)
            wrapper.started = time.time()
            return wrapper

        self._feed = _feed_timeout(func)
        log.debug(self._feed)


class ResettingLiveTextfield(Textfield, ResettingLiveWidget):
    pass


#This is as yet unimplemented, but the concept goes as such: WidgetContainers
#will be rectangular containers for collections of LiveWidgets and it is the
#WidgetTileLayer's job to arrange these containers so that they do not overlap
#or run off the window's edge. It should be dynamic enough to allow window
#resizing and the addition or removal of WidgetContainers without resetting
class WidgetTileLayer(Widget):
    """
    The WidgetTileLayer
    """
    def __init__(self):
        super(WidgetTileLayer, self).__init__()


class WidgetContainer(Widget):

    def __init__(self,
                 screen,
                 #begin_entry_at=16,
                 field_width=None,
                 #value=None,  # value is rather meaningless here
                 #use_two_lines=True,
                 hidden=False,
                 width=26,
                 height=6,
                 labelColor='LABEL',
                 label=None,
                 dynamic_y=False,  # Allowed to expand height for more widgets?
                 dynamic_x=False,  # Allowed to expand width for broad widget?
                 allow_override_begin_entry_at=True,
                 **kwargs):

        self.hidden = hidden
        self.width = width
        self.height = height
        self.field_width_request = field_width
        self.labelColor = labelColor
        self.allow_override_begin_entry_at = allow_override_begin_entry_at
        self.entry_widgets = []
        if label is None:
            self._label = 'UNLABELED'
        self.label_widget = None
        super(WidgetContainer, self).__init__(screen,
                                              width=width,
                                              height=height,
                                              **kwargs)

        #Contained widgets will inherit some, but not all of kwargs, _passon is
        #a filtered copy
        self._passon = kwargs.copy()
        dangerous_keys = ('relx', 'rely', 'value')
        for key in dangerous_keys:
            try:
                self._passon.pop(key)
            except KeyError:
                pass

        self.contained_widgets = []
        self.current_contained_rely = self.rely + 1

        self.make_label()

    def make_label(self):
        #If it overflows onto a widget, it will merely look bad. If it spills
        #out of the terminal window, it will cause a crash, so we sanitize
        max_label_length = self.width - 3 # Two for the corners, one for blank
        if len(self._label) > (max_label_length):
            label_text = 'TOO LONG!'[:max_label_length]
        else:
            label_text = self._label
        #Centering the label
        #x_offset = (self.width - len(label_text)) // 2
        x_offset = 1  # Left justified instead of centered
        self.label_widget = Textfield(self.parent,
                                      relx=self.relx + x_offset,
                                      rely=self.rely,
                                      width=len(label_text) + 1,
                                      value=label_text,
                                      color=self.labelColor)

    def add_widget(self, widget_class, **kwargs):
        pass_kwargs = self._passon.copy()
        pass_kwargs.update(kwargs)
        widget = widget_class(self.parent,
                              relx=self.relx + 2,
                              rely=self.current_contained_rely,
                              **pass_kwargs)
        self.current_contained_rely += 1
        self.contained_widgets.append(widget)

        widget_proxy = weakref.proxy(widget)
        return widget_proxy

    def remove_widget(self, widget):
        try:
            widget_position = self.contained_widgets.index(widget)
        except ValueError:  # Widget not a member in this container
            return False
        else:
            self.current_contained_rely -= 1
            for widget in self.contained_widgets[widget_position + 1:]:
                widget.rely -= 1
                widget.resize()
            self.contained_widgets.pop(widget_position)

    def update(self, clear=True):
        if clear:
            self.clear()
        if self.hidden:
            return False

        for contained in self.contained_widgets:
            contained.update()

        #Time to draw the box; First the bars
        self.parent.curses_pad.hline(self.rely, self.relx + 1,
                                     curses.ACS_HLINE, self.width - 2)
        self.parent.curses_pad.hline(self.rely + self.height - 1, self.relx + 1,
                                     curses.ACS_HLINE, self.width - 2)
        self.parent.curses_pad.vline(self.rely + 1, self.relx,
                                     curses.ACS_VLINE, self.height - 2)
        self.parent.curses_pad.vline(self.rely + 1, self.relx + self.width - 1,
                                     curses.ACS_VLINE, self.height - 2)

        #Now the corners

        #Note! The following is a workaround to fix a bug in Python 3.4.0;
        #It should probably be addressed in npyscreen internally
        #For reference: http://bugs.python.org/issue21088
        #               https://hg.python.org/cpython/rev/c67a19e11a71
        #Should be fixed in release candidate 1 of 3.4.1, so I only check for
        #3.4.0
        #The bug causes the y,x arguments to be inverted to x,y

        def custom_addch(y, x, ch):
            if sys.version_info[:3] == (3, 4, 0):
                y, x = x, y
            self.parent.curses_pad.addch(y, x, ch)

        custom_addch(self.rely, self.relx,
                     curses.ACS_ULCORNER)
        custom_addch(self.rely, self.relx + self.width - 1,
                     curses.ACS_URCORNER)
        custom_addch(self.rely + self.height - 1, self.relx,
                     curses.ACS_LLCORNER)
        custom_addch(self.rely + self.height - 1, self.relx + self.width - 1,
                     curses.ACS_LRCORNER)

        if self.editing:
            self.label_widget.show_bold = True
            self.label_widget.color = 'LABELBOLD'
        else:
            self.label_widget.show_bold = False
            self.label_widget.color = self.labelColor

        self.label_widget.update()

        #for contained in self.contained_widgets:
            #contained.update()

    def calculate_area_needed(self):
        return self.height, self.width

    @property
    def label(self):
        return self._label

    @label.setter
    def label(self, val):
        max_label_length = self.width - 3 # Two for the corners, one for blank
        if len(val) > (max_label_length):
            val = 'TOO LONG!'[:max_label_length]
        self._label = val
        self.label_widget.value = val
        self.label_widget.width = len(val) + 1
        self.label_widget.set_text_widths()
