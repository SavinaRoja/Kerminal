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

from . import __version__
from .widget_bases import LiveTitleText, LiveTextfield
from .telemachus_api import orbit_plots_names, orbit_plotables


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
        command = command_line.split()[0]
        for action in self._action_list:
            if action['command'] == command:
                action['function'](command_line,
                                   control_widget_proxy,
                                   live=False)

    def create(self):
        self.add_action('quit', self.quit, False)
        self.add_action('connect', self.connect, False)
        self.add_action('disconnect', self.disconnect, False)
        self.add_action('send', self.send, False)
        self.add_action('sub', self.sub, False)
        self.add_action('unsub', self.unsub, False)
        self.add_action('help', self.help, False)
        self.add_action('demo', self.demo, False)
        self.add_action('haiku', self.haiku, False)

    def help(self, command_line, widget_proxy, live):
        """
        Prints a help message showing what commands are available and their
        basic usage profiles.
        """
        help_msg = '''\

  Kerminal v {version}

  These commands are available at the Kerminal Command Line. Type "help" to see
  this list, and type "help name" to find out more about the use of the command
  "name".

  Each command's usage definition will be given, followed by a brief description
  of its function. Items in angle-brackets like this "<item>" are called
  arguments and are meant to be replaced by appropriate text.

  connect <host-address>:<port>
   -- Connect to a Telemachus server if not already connected.
  demo
   -- Show a demonstration of data streaming if connected.
  disconnect
   -- Disconnect from the Telemachus server if currently connected.
  help
   -- Print this help message.
  send <json_string>
   -- Send an arbitrary JSON string to the Telemachus server (if connected).
  sub <api_variable> ...
   -- Subscribe to one or more Telemachus data variables (if connected).
  unsub <api_variable> ...
   -- Unsubscribe from one or more Telemachus data variables (if connected).
  quit
   -- Shut down Kerminal.
'''.format(version=__version__)

        def multiline_feed(widget_instance):
            widget_instance.values = help_msg.split('\n')
        self.parent.wMain.feed = partial(multiline_feed, self.parent.wMain)

    def demo(self, command_line, widget_proxy, live):
        #Subscribe to the necessary data
        self.put_dict_to_stream({'+': orbit_plotables})

        #Create a function that will update the multline widget's .values
        def multiline_feed(widget_instance):
            getter = lambda k: self.parent.parentApp.stream.data.get(k, 0)
            form = '''
 Relative Velocity  : {o_relativeVelocity:0.1f}   (m/s)
 Periapsis          : {o_PeA:0.1f} (m)
 Apoapsis           : {o_PeA:0.1f} (m)
 Time to Apoapsis   : {o_timeToAp:0.1f} (s)
 Time to Periapsis  : {o_timeToPe:0.1f} (s)
 Orbit Inclination  : {o_inclination:0.1f}
 Eccentricity       : {o_eccentricity:0.1f}
 Epoch              : {o_epoch:0.1f} (s)
 Orbital Period     : {o_period:0.1f} (s)
 Argument of Peri.  : {o_argumentOfPeriapsis:0.1f}
 Time to Trans1     : {o_timeToTransition1:0.1f} (s)
 Time to Trans2     : {o_timeToTransition2:0.1f} (s)
 Semimajor Axis     : {o_sma:0.1f}
 Long. of Asc. Node : {o_lan:0.1f}
 Mean Anomaly       : {o_maae:0.1f}
 Time of Peri. Pass : {o_timeOfPeriapsisPassage:0.1f} (s)
 True Anomaly       : {o_trueAnomaly:0.1f}
'''
            data = {key.replace('.', '_'): getter(key) for key in orbit_plotables}
            log.info(data)

            widget_instance.values = form.format(**data).split('\n')

        self.parent.wMain.feed = partial(multiline_feed, self.parent.wMain)

    def send(self, command_line, widget_proxy, live):
        """
        Sends a json formatted string to the telemachus server if connected.
        Being able to send arbitrary API strings during live execution is very
        handy for development.

        Usage:
            send <json_string>

        Examples:
            send {"+": ["v.altitude", "o.period"]}
            send {"rate": 2000, "+": ["t.universalTime"]}
            send {"run": ["f.stage"]}
        """
        if not self.parent.parentApp.stream.connected:
            return
        if len(command_line.split()) < 2:
            return
        msg = command_line.split(' ', 1)[1]
        log.debug(msg)
        try:
            msg_dict = json.loads(msg)
        except Exception as e:
            log.exception(e)
            log.debug('parse failed')
            return
        else:
            self.put_dict_to_stream(msg_dict)

    def put_dict_to_stream(self, msg_dict):
        self.parent.parentApp.stream.msg_queue.put(msg_dict)

    def sub(self, command_line, widget_proxy, live):
        """
        A convenience command for subscribing to any number of api variables.
        This will send the appropiate api string {"+": [<api_var> ...]} to the
        server.

        Usage:
            sub <api_var> ...

        Example:
            sub v.altitude o.period
        """
        if not self.parent.parentApp.stream.connected:
            return
        if len(command_line.split()) < 2:
            return
        api_vars = command_line.split()[1:]
        msg_dict = {'+': api_vars}
        self.put_dict_to_stream(msg_dict)

    def unsub(self, command_line, widget_proxy, live):
        """
        A convenience command for unsubscribing from any number of api
        variables. This will send the appropiate api string
        {"-": [<api_var> ...]} to the server.

        Usage:
            unsub <api_var> ...

        Example:
            unsub v.altitude o.period
        """
        if not self.parent.parentApp.stream.connected:
            return
        if len(command_line.split()) < 2:
            return
        api_vars = command_line.split()[1:]
        msg_dict = {'-': api_vars}
        self.put_dict_to_stream(msg_dict)

    def quit(self, command_line, widget_proxy, live):
        self.parent.parentApp.setNextForm(None)
        self.parent.parentApp.switchFormNow()

    #Setting the wCommand.value seems to have no effect, I need to look into
    #this later. I might actually prefer a separate info region anyway...
    def connect(self, command_line, widget_proxy, live):
        if self.parent.parentApp.stream.connected:
            return
        try:
            addr = command_line.split()[1]
            address, port = addr.split(':')
        except IndexError:
            self.parent.wCommand.value = 'Usage: connect <address>:<port>'
            return
        except ValueError:
            self.parent.wCommand.value = 'Usage: connect <address>:<port>'
            return

        try:
            port = int(port)
        except ValueError:
            self.parent.wCommand.value = 'Port must be a number'
            return

        #Instructions to the Communication Thread to make the connection
        self.parent.parentApp.stream.address = address
        self.parent.parentApp.stream.port = port
        self.parent.parentApp.stream.make_connection.set()

        self.parent.wCommand.value = 'Making connection...'

        #Wait for the Communication Thread to tell us it is done
        self.parent.parentApp.stream.connect_event.wait()
        self.parent.parentApp.stream.connect_event.clear()

        if not self.parent.parentApp.stream.connected:  # Failed
            self.parent.wCommand.value = 'Could not connect'
        else:
            self.parent.wCommand.value = 'Connected!'

    def disconnect(self, command_line, widget_proxy, live):
        if self.parent.parentApp.stream.loop is not None:
            self.parent.parentApp.stream.loop.stop()
        self.parent.parentApp.stream.make_connection.clear()

    def haiku(self, command_line, widget_proxy, live):
        haiku = '''
 A field of cotton--
 as if the moon
 had flowered.
 - Matsuo Bashō (松尾 芭蕉)'''
        def multiline_feed(widget_instance):
            widget_instance.values = haiku.split('\n')
        self.parent.wMain.feed = partial(multiline_feed, self.parent.wMain)


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
