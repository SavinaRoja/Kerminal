# encoding: utf-8

"""

"""

from functools import partial
from time import strftime

from npyscreen import ButtonPress, Form, FormMuttActiveTraditional
from npyscreen.fmFormMuttActive import TextCommandBoxTraditional
import npyscreen
import logging
import weakref

log = logging.getLogger('kerminal.forms')

from . import __version__
from .widget_bases import LiveTitleText, LiveTextfield
from .telemachus_api import orbit_plots_names


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


#I plan on overhauling the system for commands; I didn't like the regex
#implementation. I might see if I can just use docopt for the job
#This is a stand in for now
#Ideally, I would like to be able to press something like Esc to toggle between
#the widget interface and the commandline. Or I suppose maybe Ctrl+arrow
#could be used to navigate through command history
#I might have to tweak a bunch of the internals throughout to get things exactly
#as I want them, maybe something interesting will arise for npyscreen
class KerminalCommands(object):
    def __init__(self, parent=None):
        try:
            self.parent = weakref.proxy(parent)
        except:
            self.parent = parent
        self._action_list = []
        self.create()

    def add_action(self, command, function, live):
        self._action_list.append({'command': command,
                                  'function': function,
                                  'live': live
                                  })

    def process_command_live(self, command_line, control_widget_proxy):
        #No live command processing
        pass

    def process_command_complete(self, command_line, control_widget_proxy):
        command = command_line.split()[0][1:]
        for action in self._action_list:
            if action['command'] == command:
                action['function'](command_line, control_widget_proxy, live=False)

    def create(self):
        self.add_action('quit', self.quit, False)
        self.add_action('connect', self.connect, False)
        self.add_action('disconnect', self.disconnect, False)

    def quit(self, command_line, widget_proxy, live):
        self.parent.parentApp.setNextForm(None)
        self.parent.parentApp.switchFormNow()

    #Setting the wCommand.value seems to have no effect, I need to look into
    #this later. I might actually prefer a separate info region anyway...
    def connect(self, command_line, widget_proxy, live):
        addr = command_line.split()[1]
        try:
            address, port = addr.split(':')
        except ValueError:
            self.parent.wCommand.value = 'Usage: /connect <address>:<port>'
            self.parent.display()
            return

        try:
            port = int(port)
        except ValueError:
            self.parent.wCommand.value = 'Port must be a number'
            self.parent.display()
            return

        #Instructions to the Communication Thread to make the connection
        self.parent.parentApp.stream.address = address
        self.parent.parentApp.stream.port = port
        self.parent.parentApp.stream.make_connection.set()

        self.parent.wCommand.value = 'Making connection...'
        self.parent.display()

        #Wait for the Communication Thread to tell us it is done
        self.parent.parentApp.stream.connect_event.wait()
        self.parent.parentApp.stream.connect_event.clear()

        if not self.parent.parentApp.stream.connected:  # Failed
            self.parent.wCommand.value = 'Could not connect'
            self.parent.display()
        else:
            self.parent.wCommand.value = 'Connected!'

    def disconnect(self, command_line, widget_proxy, live):
        if self.parent.parentApp.stream.loop is not None:
            self.parent.parentApp.stream.loop.stop()
        self.parent.parentApp.stream.make_connection.clear()


class SlashOnlyTextCommandBoxTraditional(TextCommandBoxTraditional):
    BEGINNING_OF_COMMAND_LINE_CHARS = ("/",)


#The new "Mutt-like" basis for the Kerminal interface
class KerminalForm(FormMuttActiveTraditional, FormWithLiveWidgets):
    STATUS_WIDGET_X_OFFSET = 1
    STATUS_WIDGET_CLASS = LiveTextfield
    ACTION_CONTROLLER = KerminalCommands
    COMMAND_WIDGET_CLASS = SlashOnlyTextCommandBoxTraditional


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


class ConnectionButton(ButtonPress):

    def whenPressed(self):
        #Sanity checking of fields
        address = self.parent.address.value
        port = self.parent.port.value
        if not address or not port:
            self.parent.info.value = 'You must enter an address AND a port!'
            self.parent.display()
            return
        try:
            port = int(port)
        except ValueError:
            self.parent.info.value = 'The port must be a number!'
            self.parent.display()
            return

        #Instructions to the Communication Thread to make the connection
        self.parent.parentApp.stream.address = address
        self.parent.parentApp.stream.port = port
        self.parent.parentApp.stream.make_connection.set()

        self.parent.info.value = 'Making connection...'
        self.parent.display()

        #Wait for the Communication Thread to tell us it is done
        self.parent.parentApp.stream.connect_event.wait()
        self.parent.parentApp.stream.connect_event.clear()

        if self.parent.parentApp.stream.connected:  # Success
            self.parent.parentApp.switchForm('CONNECTION')
            self.parent.special_button = True  # See ConnectQuery.afterEditing

        else:  # Failed
            self.parent.info.value = 'Could not connect'
            self.parent.display()


class ConnectQuery(Form):
    OK_BUTTON_TEXT = 'EXIT'
    special_button = False
    FIX_MINIMUM_SIZE_WHEN_CREATED = True

    def create(self):
        self.add(npyscreen.FixedText,
                 value='Welcome to Kerminal {0}'.format(__version__),
                 editable=False)
        self.address = self.add(npyscreen.TitleText,
                                name='Address:',
                                value='')
        self.port = self.add(npyscreen.TitleText,
                             name='Port:',
                             value='8085')
        self.connect = self.add(ConnectionButton, name='Connect')
        self.info = self.add(npyscreen.FixedText,
                             value='',
                             editable=False)

    def beforeEditing(self):
        pass

    def afterEditing(self):
        #Contrary to the documentation, switchForm will not evade the exit
        #logic of the Form, so this check is needed
        if not self.special_button:
            self.parentApp.setNextForm(None)
        self.special_button = False
        self.info.value = ''
