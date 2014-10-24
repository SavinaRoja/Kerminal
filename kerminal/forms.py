# encoding: utf-8

"""

"""

from functools import partial
from time import strftime

from npyscreen import FixedText, TitleText
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
from .container.gridcontainer import GridContainer
from .container.boxcontainer import BoxContainer
from .container.smartcontainer import SmartContainer


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
        MAXY, MAXX = self.lines, self.columns

        self.wStatus1 = self.add(self.__class__.STATUS_WIDGET_CLASS,  rely=0,
                                 relx=self.__class__.STATUS_WIDGET_X_OFFSET,
                                 editable=False,
                                 )

        if self.__class__.MAIN_WIDGET_CLASS:
            self.wMain    = self.add(self.__class__.MAIN_WIDGET_CLASS,
                                     rely=self.__class__.MAIN_WIDGET_CLASS_START_LINE,
                                     relx=0,
                                     max_height=False,
                                     )
        self.wStatus2 = self.add(self.__class__.STATUS_WIDGET_CLASS,  rely=MAXY-2-self.BLANK_LINES_BASE,
                                        relx=self.__class__.STATUS_WIDGET_X_OFFSET,
                                        editable=False,
                                        )

        if not self.__class__.COMMAND_WIDGET_BEGIN_ENTRY_AT:
            self.wCommand = self.add(self.__class__.COMMAND_WIDGET_CLASS, name=self.__class__.COMMAND_WIDGET_NAME,
                                    rely = MAXY-1-self.BLANK_LINES_BASE, relx=0,)
        else:
            self.wCommand = self.add(self.__class__.COMMAND_WIDGET_CLASS,
                                     name=self.__class__.COMMAND_WIDGET_NAME,
                                     rely=MAXY - 1 - self.BLANK_LINES_BASE,
                                     relx=0,
                                     begin_entry_at=self.__class__.COMMAND_WIDGET_BEGIN_ENTRY_AT,
                                     allow_override_begin_entry_at=self.__class__.COMMAND_ALLOW_OVERRIDE_BEGIN_ENTRY_AT
                                     )

        self.wInfo = self.add(self.__class__.INFO_WIDGET_CLASS,
                              rely=MAXY - 3 - self.BLANK_LINES_BASE,
                              relx=0,
                              editable=False,
                              )

        self.wStatus1.important = True
        self.wStatus2.important = True
        self.wInfo.important = True
        self.nextrely = 3

    #def create(self):
        #self.wInfo = self.add(self.__class__.INFO_WIDGET_CLASS,
                              #rely=MAXY - 3 - self.BLANK_LINES_BASE,
                              #relx=0,
                              #editable=False,
                              #)
        #self.wMain.max_height = -3
        #self.wInfo.important = True
        #self.nextrely = 3

from random import randint

class KerminalForm(FormMuttActiveTraditionalWithInfo, FormWithLiveWidgets):
    STATUS_WIDGET_X_OFFSET = 1
    STATUS_WIDGET_CLASS = LiveTextfield
    ACTION_CONTROLLER = KerminalCommands
    #COMMAND_WIDGET_CLASS = SlashOnlyTextCommandBoxTraditional
    COMMAND_WIDGET_CLASS = TextCommandBoxToggled
    #MAIN_WIDGET_CLASS = BoxContainer
    MAIN_WIDGET_CLASS = GridContainer
    #MAIN_WIDGET_CLASS = SmartContainer
    FIX_MINIMUM_SIZE_WHEN_CREATED = False

    def __init__(self, *args, **kwargs):
        super(KerminalForm, self).__init__(*args, **kwargs)
        #self.wMain.interested_in_mouse_even_when_not_editable = False

        #Allow the recall of previous widget
        self.previous_widget = self.wMain
        #self.wMain.feed = lambda: ''
        self.wMain.editable = False
        self.wMain.fill_rows_first = True
        #self.wMain.max_height = 20
        #self.wMain.max_width = 30
        #self.wMain.height = 10
        #self.wMain.width = 20
        self.wMain.diagnostic = 'X'
        self.wMain.margin = 2
        #self.wMain.add_widget(FixedText, value='Box', widget_id='Box')

        for i in range(24):
            box = self.wMain.add_widget(BoxContainer)
            val = 'Box{0}'.format(i)
            box.add_widget(FixedText, value=val, widget_id=val)
            live = box.add_widget(LiveTextfield, name='Live', value='live')
            live.feed = lambda: strftime("%H:%M:%S")
            self.live_widgets.append(live)
        #sc = self.wMain.add_widget(SmartContainer, height=25, width=70, scheme='ffdh-bottom')
        #for i in range(15):
            #h = randint(4, 10)
            #w = randint(10, 15)
            #box = sc.add_widget(BoxContainer, height=h, width=w)
            #val = 'Box{0}'.format(i)
            #box.add_widget(FixedText, value=val, widget_id=val)
            #live = box.add_widget(LiveTextfield, name='Live', value='live')
            #live.feed = lambda: strftime("%H:%M:%S")
            #self.live_widgets.append(live)
        #grid = self.wMain.add_widget(GridContainer, rows=2, cols=2, diagnostic='Z')

    def go_back(self, *args, **kwargs):
        log.info('going back')
        self.wMain = self.previous_widget

    def while_waiting(self):
        #Updates all live widgets from their feed before updating
        for live_widget in self.live_widgets:
            live_widget.feed()
        #Here's the stuff for live updating the multiline widget
        #self.wMain.feed()
        self.display()

    def resize(self):
        super(FormMuttActiveTraditionalWithInfo, self).resize()

        self.wInfo.rely = self.lines - 3 - self.BLANK_LINES_BASE
        self.wStatus2.rely = self.lines - 2 - self.BLANK_LINES_BASE
        self.wMain.max_height = self.lines - 4 - self.BLANK_LINES_BASE
        self.wMain.max_width = self.columns
        self.wMain.resize()
        self.wInfo.resize()
        self.wStatus1.resize()
        self.wStatus2.resize()
        self.wCommand.resize()
        #self.wCommand.rely = self.columns-1-self.BLANK_LINES_BASE
