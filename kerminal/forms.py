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
import json

log = logging.getLogger('kerminal.forms')


from .widget_bases import LiveTitleText, LiveTextfield
from .telemachus_api import orbit_plots_names, orbit_plotables
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
                              curses.KEY_END: self.h_cursor_end,})

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


#The new "Mutt-like" basis for the Kerminal interface
class KerminalForm(FormMuttActiveTraditional, FormWithLiveWidgets):
    STATUS_WIDGET_X_OFFSET = 1
    STATUS_WIDGET_CLASS = LiveTextfield
    ACTION_CONTROLLER = KerminalCommands
    #COMMAND_WIDGET_CLASS = SlashOnlyTextCommandBoxTraditional
    COMMAND_WIDGET_CLASS = TextCommandBoxToggled
    #MAIN_WIDGET_CLASS   = MultiLine


    #I may actually just make a new class in the future to partially
    #re-implement the FormMuttActive.
    def __init__(self, *args, **kwargs):
        super(KerminalForm, self).__init__(*args, **kwargs)
        #This being set to True was causing trouble
        self.wMain.interested_in_mouse_even_when_not_editable = False
        #Allow the recall of previous widget
        self.previous_widget = self.wMain
        log.info(self.previous_widget)
        self.wMain.feed = lambda: ''

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


#Here be the older demo interface stuff; pre-Mutt-like
class Connection(FormWithLiveWidgets):
    OK_BUTTON_TEXT = 'DROP CONNECTION'

    def create(self):
        #self.parentApp.stream.start()
        self.add(npyscreen.FixedText, value='You have successfully connected!')
        feedf = lambda k: partial(self.parentApp.stream.data.get, k)
        self.time_w = self.add_live(LiveTitleText,
                                    name='Time',
                                    value='',
                                    editable=False,
                                    feed=partial(strftime, "%Y-%m-%d %H:%M:%S")
                                    )
        self.alt = self.add_live(LiveTitleText,
                                 name='V. Altitude',
                                 value='',
                                 editable=False,
                                 feed=feedf('v.altitude')
                                 )
        self.mission_time = self.add_live(LiveTitleText,
                                          name='V. Mission Time',
                                          value='',
                                          editable=False,
                                          feed=feedf('v.missionTime')
                                          )
        self.univ_time = self.add_live(LiveTitleText,
                                       name='Universal Time',
                                       value='',
                                       editable=False,
                                       feed=feedf('t.universalTime')
                                       )
        pausef = lambda f: 'True' if f() else 'False'
        self.paused = self.add_live(LiveTitleText,
                                    name='Game Paused',
                                    value='',
                                    editable=False,
                                    feed=partial(pausef, feedf('p.paused'))
                                    )

        #This illustrates that I am able to inject messages to be sent to the
        #server based on UI actions
        self.orbit = {}
        subscribe_keys = list(orbit_plots_names.keys())
        for key, nameval in orbit_plots_names.items():
            self.orbit[key] = self.add_live(LiveTitleText,
                                            name=nameval,
                                            editable=False,
                                            feed=feedf(key))

        self.parentApp.stream.msg_queue.put({'+': subscribe_keys})

    def afterEditing(self):
        self.parentApp.stream.loop.stop()
        self.parentApp.stream.make_connection.clear()
        #self.parentApp.stream.connect_event.clear()
        self.parentApp.setNextForm('MAIN')
