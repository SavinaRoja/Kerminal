# encoding: utf-8

"""
kerminal.commands handles the execution of commands in the Kerminal Command Line
"""

from .. import __version__

from docopt import docopt, DocoptExit
from functools import wraps, partial
import logging
import sys

from ..telemachus_api import orbit_plots_names, orbit_plotables

log = logging.getLogger('kerminal.commands')


def connect(args, widget_proxy, parent_form, stream):
    """
    connect

    Connect to a Telemachus server if not already connected.

    Usage:
      connect <host-address> <port>
    """

    if stream.connected:
        return

    try:
        port = int(args['<port>'])
    except ValueError:
        parent_form.wInfo.feed = 'Port must be a number'
        return

    #Instructions to the Communication Thread to make the connection
    stream.address = args['<host-address>']
    stream.port = port
    stream.make_connection.set()

    parent_form.wInfo.feed = 'Making connection...'

    #Wait for the Communication Thread to tell us it is done
    stream.connect_event.wait()
    stream.connect_event.clear()

    if not stream.connected:  # Failed
        parent_form.wInfo.feed = 'Could not connect'
    else:
        parent_form.wInfo.feed = 'Connected!'


def demo(args, widget_proxy, parent_form, stream):
    """
    demo

    Show a demonstration of data streaming if connected.

    Usage:
      demo
    """
    #Subscribe to the necessary data
    stream.msg_queue.put({'+': orbit_plotables})

    #Create a function that will update the multline widget's .values
    def multiline_feed(widget_instance):
        getter = lambda k: stream.data.get(k, 0)
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

    parent_form.wMain.feed = partial(multiline_feed, parent_form.wMain)
    parent_form.wInfo.feed = 'Showing Demo!'


def disconnect(args, widget_proxy, parent_form, stream):
    """
    disconnect

    Disconnect from the Telemachus server if currently connected.

    Usage:
      disconnect
    """
    if stream.loop is not None:
        stream.loop.stop()
    stream.make_connection.clear()


def haiku(args, widget_proxy, parent_form, stream):
    """
    haiku

    Puts a haiku on the screen.

    Usage:
      haiku
    """

    haiku = '''
 A field of cotton--
 as if the moon
 had flowered.
 - Matsuo Bashō (松尾 芭蕉)'''

    def multiline_feed(widget_instance):
        widget_instance.values = haiku.split('\n')
    parent_form.wMain.feed = partial(multiline_feed, parent_form.wMain)


def send(args, widget_proxy, parent_form, stream):
    """
    send

    Send an arbitrary JSON string to the Telemachus server (if connected).

    Usage:
      send <json-string>


    Being able to send arbitrary API strings during live execution is very
    handy for development.


    Examples:
      send {"+": ["v.altitude", "o.period"]}
      send {"rate": 2000, "+": ["t.universalTime"]}
      send {"run": ["f.stage"]}
    """
    if not stream.connected:
        return
    msg = args['<json-string>']
    log.debug(msg)
    try:
        msg_dict = json.loads(msg)
    except Exception as e:
        log.exception(e)
        log.debug('parse failed')
        return
    else:
        stream.msg_queue.put(msg_dict)


def sub(args, widget_proxy, parent_form, stream):
    """
    sub

    Subscribe to one or more Telemachus data variables (if connected).

    Usage:
      sub <api-variable> ...

    Example:
      sub v.altitude o.period
    """
    if not stream.connected:
        return

    stream.msg_queue.put({'+': args['<api-variable>']})


def unsub(args, widget_proxy, parent_form, stream):
    """
    unsub

    Unsubscribe from one or more Telemachus data variables (if connected).

    Usage:
      unsub <api-variable> ...

    Example:
      unsub v.altitude o.period
    """
    if not stream.connected:
        return

    stream.msg_queue.put({'-': args['<api-variable>']})


def quits(args, widget_proxy, parent_form, stream):
    """
    quit

    Shut down Kerminal.

    Usage:
      quit [options]

    Options:
      -h --help    Show this help message and exit
    """
    parent_form.parentApp.setNextForm(None)
    parent_form.parentApp.switchFormNow()
    #disconnect(args, widget_proxy, parent_form, stream)


class KerminalCommands(object):
    def __init__(self, parent=None):
        try:
            self.parent = weakref.proxy(parent)
        except:
            self.parent = parent
        #self._action_list = []
        self._commands = {'connect': connect,
                          'demo': demo,
                          'disconnect': disconnect,
                          'haiku': haiku,
                          'help': self.helps,
                          'send': send,
                          'sub': sub,
                          'unsub': unsub,
                          'quit': quits}
        #self.create()

    #def add_action(self, command, function, live):
        #self._action_list.append({'command': command,
                                  #'function': function,
                                  ##'live': live
                                  #})

    #def process_command_live(self, command_line, control_widget_proxy):
        ##No live command processing
        #pass

    def process_command_complete(self, command_line, control_widget_proxy):
        for comm in command_line.split(';'):
            argv = comm.split()
            try:
                command = argv.pop(0)
            except IndexError:
                return
            command_func = self._commands.get(command)
            if command_func is None:
                return
                #TODO: modify something in the state of parent
            try:
                args = docopt(command_func.__doc__,
                              version='Kerminal v {0}'.format(__version__),
                              argv=argv)
            except DocoptExit as e:
                #TODO: modify something in the state of parent
                log.debug(e)
            else:
                command_func(args,
                             control_widget_proxy,
                             self.parent,
                             self.parent.parentApp.stream)

    def helps(self, args, widget_proxy, parent_form, stream):
        """
        help

        Displays available commands with general information, or detailed
        information on a single command.

        Usage:
          help [<command>]

        Arguments:
          <command>       Command whose information should be displayed.
        """

        def doc_style(docstring):
            lines = docstring.splitlines()
            unindent = len(lines[1]) - len(lines[1].lstrip())
            new_lines = []
            for line in lines:
                if line.startswith(' ' * unindent):
                    new_lines.append(line[unindent:])
                else:
                    new_lines.append(line)
            return '\n'.join(['  ' + l if l.strip() else l for l in new_lines])
            #return '\n'.join(['\n'] + new_lines)

        if args['<command>']:
            if args['<command>'] not in self._commands:
                return
            help_msg = doc_style(self._commands[args['<command>']].__doc__)
        else:
            #TODO: Make thsi message generatable from the functions themselves
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
        parent_form.wMain.feed = partial(multiline_feed, parent_form.wMain)
