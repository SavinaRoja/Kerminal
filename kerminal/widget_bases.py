# encoding: utf-8

from npyscreen.wgwidget import Widget
from npyscreen import TitleText, Textfield#, FixedText
#from npyscreen.wgmultiline import MultiLine

#import weakref
import curses
from functools import wraps
import logging
import time
import sys

log = logging.getLogger('kerminal.widget_bases')


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


from .container import BaseContainer


#This is a re-implementation of the old WidgetContainer, starting from the
#ground-up as a BaseContainer subclass
class BoxContainer(BaseContainer):
    """
    A quite basic Container subclass, BoxContainer assumes all contained widgets
    will require one line, draws a box at its perimeter, and can optionally
    create a header and footer with one of (left, center, right) justification.
    """
    BORDER_MARGIN = 1
    #HEADER_JUSTIFY = 'left'  # left | center | right
    #FOOTER_JUSTIFY = 'left'  # left | center | right

    def __init__(self,
                 screen,
                 height=6,
                 width=26,
                 header=None,  # Header text
                 footer=None,  # Footer text
                 header_justify='right',  # str, one of (left, center, right)
                 footer_justify='center',  # str, one of (left, center, right)
                 header_color='LABEL',
                 footer_color='LABEL',
                 *args,
                 **kwargs):

        self.height = height
        self.width = width
        #self.header = header
        self.header = 'HEADER'
        #self.footer = footer
        self.footer = 'FOOTER'
        if header_justify in ('left', 'center', 'right'):
            self.header_justify = header_justify
        else:
            self.header_justify = 'left'
        if footer_justify in ('left', 'center', 'right'):
            self.footer_justify = footer_justify
        else:
            self.footer_justify = 'left'
        self.header_color = header_color
        self.footer_color = footer_color
        super(BoxContainer, self).__init__(screen,
                                           margin=self.__class__.BORDER_MARGIN,
                                           #height=6,
                                           #width=26,
                                           *args,
                                           **kwargs)
        self.make_header_and_footer()

    def make_header_and_footer(self):
        max_text_length = self.width - 3  # Two for the corners, one for blank
        justify_offsets = {'left': lambda x: 1,
                           'center': lambda x: (self.width - len(x)) // 2,
                           'right': lambda x: (self.width - len(x)) - 1}
        if self.header:
            if len(self.header) > (max_text_length):
                header_text = 'TOO LONG!'[:max_text_length]
            else:
                header_text = self.header
            x_offset = justify_offsets[self.header_justify](header_text)
            self.header_widget = Textfield(self.parent,
                                           relx=self.relx + x_offset,
                                           rely=self.rely,
                                           width=len(header_text) + 1,
                                           value=header_text,
                                           color=self.header_color)
        else:
            self.header_widget = None
        if self.footer:
            if len(self.footer) > (max_text_length):
                footer_text = 'TOO LONG!'[:max_text_length]
            else:
                footer_text = self.footer
            x_offset = justify_offsets[self.footer_justify](footer_text)
            self.footer_widget = Textfield(self.parent,
                                           relx=self.relx + x_offset,
                                           rely=self.rely + self.height - 1,
                                           width=len(footer_text) + 1,
                                           value=footer_text,
                                           color=self.footer_color)
        else:
            self.footer_widget = None

    def _resize(self):
        for i, widget in enumerate(self.contained):
            widget.relx = self.relx + self.left_margin
            widget.width = self.width - (self.right_margin + self.left_margin)
            widget.rely = self.rely + self.top_margin + i
            widget.resize()

    def update(self, clear=True):
        super(BoxContainer, self).update(clear)

        for contained in self.contained:
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
            if self.header_widget is not None:
                self.header_widget.show_bold = True
                self.header_widget.color = 'LABELBOLD'
            if self.footer_widget is not None:
                self.footer_widget.show_bold = True
                self.footer_widget.color = 'LABELBOLD'
        else:
            if self.header_widget is not None:
                self.header_widget.show_bold = False
                self.header_widget.color = self.header_color
            if self.footer_widget is not None:
                self.footer_widget.show_bold = False
                self.footer_widget.color = self.footer_color

        if self.header_widget is not None:
            self.header_widget.update()
        if self.footer_widget is not None:
            self.footer_widget.update()

    def calculate_area_needed(self):
        return self.height, self.width
        #return 0, 0


#Much of this was originally adapted from the code for TitleText
class WidgetContainer(BaseContainer):
    """
    """
    def __init__(self,
                 screen,
                 #field_width=None,
                 #hidden=False,
                 width=26,
                 height=6,
                 labelColor='LABEL',
                 label=None,
                 #dynamic_y=False,  # Allowed to expand height for more widgets?
                 #dynamic_x=False,  # Allowed to expand width for broad widget?
                 #allow_override_begin_entry_at=True,
                 **kwargs):

        #self.hidden = hidden
        self.width = width
        self.height = height
        #self.field_width_request = field_width
        self.labelColor = labelColor
        #self.allow_override_begin_entry_at = allow_override_begin_entry_at
        self.entry_widgets = []
        if label is None:
            self._label = 'UNLABELED'
        self.label_widget = None
        super(WidgetContainer, self).__init__(screen,
                                              width=width,
                                              height=height,
                                              **kwargs)

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

    def _resize(self):
        for i, widget in enumerate(self.contained):
            widget.relx = self.relx + 1
            widget.rely = self.rely + 1 + i
            widget.resize()

    def update(self, clear=True):
        super(WidgetContainer, self).update(clear)

        for contained in self.contained:
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

        #for contained in self.contained:
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
