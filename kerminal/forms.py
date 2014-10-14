# encoding: utf-8

"""

"""

from functools import partial
from time import strftime

from npyscreen import ButtonPress, Form, FormMuttActiveTraditional
from npyscreen.fmFormMuttActive import TextCommandBoxTraditional,\
                                       TextCommandBox
from npyscreen.wgmultiline import MultiLine
import npyscreen
import logging
import weakref
import curses

log = logging.getLogger('kerminal.forms')


from .widget_bases import LiveTitleText, LiveTextfield, ResettingLiveTextfield
from .telemachus_api import orbit_plots_names
from .commands import KerminalCommands


#The FormWithLiveWidgets class represents one of the first strategies for
#improving the means by which live widgets are integrated with forms. I highly
#suspect that other strategies may be explored, especially as I consider the
#topic of widget clusters. I'll need to delve into the source code for Widgets
#and the `add` method, it might be that I should just add an attribute to a
#base implementation for a LiveWidget and let `add` assign the function
class FormWithLiveWidgets(Form):
    """
    The `FormWithLiveWidgets` modifies the basic `Form` in a small way to
    enhance the convenience of working with "live" widgets.

    For live-updating data, the form's `while_waiting` method will be employed
    to instruct all live widgets to update their values and then the screen will
    be updated. Live widgets need to have a special method, known as `feed`,
    which is called to update the widget's value, and the live widgets must be
    registered with the Form so that each widget's `feed` method can be called
    appropriately.

    """
    live_widgets = []

    def add_live(self, *args, **kwargs):
        live_widget = self.add(*args, **kwargs)
        self.live_widgets.append(live_widget)
        return live_widget

    def while_waiting(self):
        #Updates all live widgets from their feed before updating
        for live_widget in self.live_widgets:
            live_widget.feed()
        self.display()


class TextCommandBoxToggled(TextCommandBox):

    def __init__(self,
                 screen,
                 history=True,
                 history_max=100,
                 set_up_history_keys=True,
                 *args, **kwargs):
        super(TextCommandBoxToggled,
              self).__init__(screen,
                             history=history,
                             history_max=history_max,
                             set_up_history_keys=set_up_history_keys,
                             *args, **kwargs
                             )
        self.linked_widget = None
        self.always_pass_to_linked_widget = []
        self.command_active = False
        self.value = 'Press TAB to enter commands'
        self.toggle_handler = curses.ascii.TAB
        self.handlers.update({curses.KEY_HOME: self.h_cursor_beginning,
                              curses.KEY_END: self.h_cursor_end,
                              })

    def h_cursor_beginning(self, *args, **kwargs):
        self.cursor_position = 0

    def h_cursor_end(self, *args, **kwargs):
        self.cursor_position= len(self.value)
        if self.cursor_position < 0:
            self.cursor_position = 0

    def toggle_command_active(self, *args, **kwargs):
        self.command_active = not self.command_active
        if self.command_active:
            self.value = ''
        else:
            self.value = 'Press TAB to enter commands'
            self.h_cursor_end()
        self.update()

    def handle_input(self, inputch):
        if inputch == self.toggle_handler:
            self.toggle_command_active()
            return
        try:
            inputchstr = chr(inputch)
        except:
            inputchstr = False

        try:
            input_unctrl = curses.ascii.unctrl(inputch)
        except TypeError:
            input_unctrl = False

        if not self.linked_widget:
            return super(TextCommandBoxTraditional, self).handle_input(inputch)

        if (inputch in self.always_pass_to_linked_widget) or \
            (inputchstr in self.always_pass_to_linked_widget) or \
            (input_unctrl in self.always_pass_to_linked_widget):
            rtn = self.linked_widget.handle_input(inputch)
            self.linked_widget.update()
            return rtn

        if self.command_active:
            return super(TextCommandBoxToggled, self).handle_input(inputch)

        rtn = self.linked_widget.handle_input(inputch)
        self.linked_widget.update()
        return rtn

    #Modifying this allows evasion of live editing altogether
    def when_value_edited(self):
        super(TextCommandBox, self).when_value_edited()
        #if self.editing:
            #self.parent.action_controller.process_command_live(self.value, weakref.proxy(self))
        #else:
        if not self.editing:
            self.parent.action_controller.process_command_complete(self.value, weakref.proxy(self))


class SlashOnlyTextCommandBoxTraditional(TextCommandBoxTraditional):
    BEGINNING_OF_COMMAND_LINE_CHARS = ("/",)


class FormMuttActiveTraditionalWithInfo(FormMuttActiveTraditional):
    """
    A minor hack on FormMuttActiveTraditional to give me a status info bar
    """
    INFO_WIDGET_CLASS = ResettingLiveTextfield

    def draw_form(self):
        super(FormMuttActiveTraditionalWithInfo, self).draw_form()
        MAXY, MAXX = self.lines, self.columns
        self.curses_pad.hline(MAXY-3-self.BLANK_LINES_BASE, 0, curses.ACS_BULLET, MAXX - 1)

    def create(self):
        super(FormMuttActiveTraditionalWithInfo, self).create()
        MAXY, MAXX = self.lines, self.columns
        self.wInfo = self.add(self.__class__.INFO_WIDGET_CLASS,
                              rely=MAXY - 3 - self.BLANK_LINES_BASE,
                              relx=0,
                              editable=False,
                              )
        self.wMain.max_height = -3
        self.wInfo.important = True
        self.nextrely = 3


### START EXPERIMENTAL SECTION ###
from npyscreen.wgwidget import Widget
from npyscreen.wgtextbox import Textfield
import npyscreen.wgtextbox as textbox


class ContainerWidget(Widget):
    _entry_type = Textfield
    def __init__(self,
                 screen,
                 begin_entry_at=16,
                 field_width=None,
                 value=None,
                 #use_two_lines=True,
                 hidden=False,
                 labelColor='LABEL',
                 allow_override_begin_entry_at=True,
                 **kwargs):

        self.hidden = hidden
        self.text_field_begin_at = begin_entry_at
        self.field_width_request = field_width
        self.labelColor = labelColor
        self.allow_override_begin_entry_at = allow_override_begin_entry_at
        self.entry_widgets = []
        super(ContainerWidget, self).__init__(screen, **kwargs)

        if self.name is None:
            self.name = 'NoName'

        #if use_two_lines is None:
            #if len(self.name) + 2 >= begin_entry_at:
                #self.use_two_lines = True
            #else:
                #self.use_two_lines = False
        #else:
            #self.use_two_lines = use_two_lines

        self._passon = kwargs.copy()
        for dangerous in ('relx', 'rely', 'value',):  # 'width','max_width'):
            try:
                self._passon.pop(dangerous)
            except KeyError:
                pass

        if self.field_width_request:
            self._passon['width'] = self.field_width_request
        else:
            if 'max_width' in self._passon.keys():
                if self._passon['max_width'] > 0:
                    if self._passon['max_width'] < self.text_field_begin_at:
                        raise ValueError("The maximum width specified is less than the text_field_begin_at value.")
                    else:
                        self._passon['max_width'] -= self.text_field_begin_at + 1

        if 'width' in self._passon:
            #if 0 < self._passon['width'] < self.text_field_begin_at:
            #    raise ValueError("The maximum width specified %s is less than the text_field_begin_at value %s." % (self._passon['width'], self.text_field_begin_at))
            if self._passon['width'] > 0:
                self._passon['width'] -= self.text_field_begin_at + 1

        #if self.use_two_lines:
            #if 'max_height' in self._passon and self._passon['max_height']:
                #if self._passon['max_height'] == 1:
                    #raise ValueError("I don't know how to resolve this: max_height == 1 but widget using 2 lines.")
                #self._passon['max_height'] -= 1
            #if 'height' in self._passon and self._passon['height']:
                #raise ValueError("I don't know how to resolve this: height == 1 but widget using 2 lines.")
                #self._passon['height'] -= 1

        self.make_contained_widgets()
        self.value = value

    def resize(self):
        super(ContainerWidget, self).resize()
        self.label_widget.relx = self.relx
        self.label_widget.rely = self.rely
        for i, e_w in enumerate(self.entry_widgets):
            e_w.relx = self.relx + 2
            e_w.rely = self.rely + i + 1
            e_w.resize()
        self.label_widget._resize()
        #self.entry_widget._resize()
        self.recalculate_size()

    def make_contained_widgets(self):
        #This is the name/label of the container
        self.label_widget = textbox.Textfield(self.parent,
                                              relx=self.relx,
                                              rely=self.rely,
                                              width=len(self.name) + 1,
                                              value=self.name,
                                              color=self.labelColor)

        #If the label itself is taking up two lines and
        #if self.label_widget.on_last_line and self.use_two_lines:
            ## we're in trouble here.
            #if len(self.name) > 12:
                #ab_label = 12
            #else:
                #ab_label = len(self.name)
            #self.use_two_lines = False
            #self.label_widget = textbox.Textfield(self.parent, relx=self.relx, rely=self.rely, width=ab_label+1, value=self.name)
            #if self.allow_override_begin_entry_at:
                #self.text_field_begin_at = ab_label + 1
        #if self.use_two_lines:
            #self._contained_rely_offset = 1
        #else:
            #self._contained_rely_offset = 0
        #self._contained_rely_offset = 1
        for i in range(3):
            e_w = self.__class__._entry_type(self.parent,
                                             relx=(self.relx + 2),
                                             rely=(self.rely + i + 1),
                                             value=self.value,
                                             **self._passon)
            e_w.parent_widget = weakref.proxy(self)
            self.entry_widgets.append(e_w)

        #self.entry_widget = self.__class__._entry_type(self.parent,
                                                       #relx=(self.relx + self.text_field_begin_at),
                                                       #rely=(self.rely+self._contained_rely_offset),
                                                       #value=self.value,
                                                       #**self._passon)
        #self.entry_widget.parent_widget = weakref.proxy(self)
        self.recalculate_size()


    def recalculate_size(self):
        self.height = 4
        self.width = self.entry_widgets[0].width + self.text_field_begin_at
        #self.height = self.entry_widget.height
        #if self.use_two_lines: self.height += 1
        #else: pass
        #self.width = self.entry_widget.width + self.text_field_begin_at

    def edit(self):
        self.editing=True
        self.display()
        #self.entry_widget.edit()
        #self.value = self.textarea.value
        #self.how_exited = self.entry_widget.how_exited
        self.how_exited = 1
        self.editing=False
        self.display()

    def update(self, clear = True):
        if clear: self.clear()
        if self.hidden: return False
        if self.editing:
            self.label_widget.show_bold = True
            self.label_widget.color = 'LABELBOLD'
        else:
            self.label_widget.show_bold = False
            self.label_widget.color = self.labelColor
        self.label_widget.update()
        for e_w in self.entry_widgets:
            e_w.update()
        #self.entry_widget.update()

    def handle_mouse_event(self, mouse_event):
        if self.entry_widget.intersted_in_mouse_event(mouse_event):
            self.entry_widget.handle_mouse_event(mouse_event)

    @property
    def value(self):
        if hasattr(self, 'entry_widget'):
            return self.entry_widget.value
        elif hasattr(self, '__tmp_value'):
            return self.__tmp_value
        else:
            return None

    @value.setter
    def value(self, value):
        if hasattr(self, 'entry_widgets'):
            for e_w in self.entry_widgets:
                e_w.value = value
            #self.entry_widget.value = value
        else:
            # probably trying to set the value before the textarea is initialised
            self.__tmp_value = value

    @value.deleter
    def value(self):
        del self.entry_widget.value

    @property
    def editable(self):
        try:
            return self.entry_widget.editable
        except AttributeError:
            return self._editable

    @editable.setter
    def editable(self, value):
        self._editable = value
        try:
            self.entry_widget.editable = value
        except AttributeError:
            self._editable = value
### END EXPERIMENTAL SECTION ###


class KerminalForm(FormMuttActiveTraditionalWithInfo, FormWithLiveWidgets):
    STATUS_WIDGET_X_OFFSET = 1
    STATUS_WIDGET_CLASS = LiveTextfield
    ACTION_CONTROLLER = KerminalCommands
    #COMMAND_WIDGET_CLASS = SlashOnlyTextCommandBoxTraditional
    COMMAND_WIDGET_CLASS = TextCommandBoxToggled
    MAIN_WIDGET_CLASS   = ContainerWidget

    #I may actually just make a new class in the future to partially
    #re-implement the FormMuttActive.
    def __init__(self, *args, **kwargs):
        super(KerminalForm, self).__init__(*args, **kwargs)
        #This being set to True was causing trouble
        self.wMain.interested_in_mouse_even_when_not_editable = False
        #Allow the recall of previous widget
        self.previous_widget = self.wMain
        self.wMain.feed = lambda: ''
        self.wMain.value = 'Spam'
        self.wMain.editable = True

    def go_back(self, *args, **kwargs):
        log.info('going back')
        self.wMain = self.previous_widget

    #It looks like interacting with MultiLine widgets is going to necessitate
    #a variation in technique
    def while_waiting(self):
        #Updates all live widgets from their feed before updating
        for live_widget in self.live_widgets:
            live_widget.feed()
        #Here's the stuff for live updating the multiline widget
        self.wMain.feed()
        self.display()

    def resize(self):
        super(FormMuttActiveTraditionalWithInfo, self).resize()
        self.wInfo.rely = self.lines - 3 - self.BLANK_LINES_BASE
