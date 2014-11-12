# encoding: utf-8

"""
kerminal.commands handles the execution of commands in the Kerminal Command Line
"""

from .. import __version__
from .logs import logs

from docopt import docopt, DocoptExit
from functools import wraps, partial
import json
import logging
import os
import sys

from ..communication import OrderedSet

from ..telemachus_api import orbit_plots_names, plotables , orbit_plotables

log = logging.getLogger('kerminal.commands')
log.debug('commands')


#The docstrings for commands follow a modified PEP8! (80 + indent) characters
#this is to allow conformity of help messages regardless of indent level
def connect(args, widget_proxy, parent_form, stream):
    """
    connect

    Connect to a Telemachus server if not already connected.

    Usage:
      connect <host-address> [<port>]

    Arguments:
      <host-address>    The address of the computer acting as Telemachus server.
      <port>            The port for the connection. If not supplied, this command
                        will use the Telemachus default of 8085.

    Discussion and Examples:

    If you are using Kerminal on the same computer running Kerbal Space Program and
    Telemachus, your command will probably use "localhost".
      "connect localhost [<port>]"

    If you are connecting to a computer on your local network, you should use your
    local network address. For some, this address may look like "192.168.1.X".
      "connect 192.168.1.2 [<port>]"

    In order to connect over the internet, you will need to know the IP address of
    the computer in question. IP addresses may be hard to remember and can change
    over time, so it is recommended that you use a DNS service (free options exist).
    One will also likely need to configure port forwarding for the port being used.
      "connect myserver.domain.com [<port>]"
    """

    log.info('connect command called')

    if stream.connected:
        return

    if args['<port>'] is None:
        port = 8085
    else:
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

    log.info('demo command called')
    if not stream.connected:
        parent_form.wInfo.feed = 'Not connected!'
        return

    #Subscribe to the necessary data
    #stream.msg_queue.put({'+': orbit_plotables})
    for var in orbit_plotables:
        stream.subscription_manager.add(var)

    #Create a function that will update the multline widget's .values
    def multiline_feed(widget_instance):
        getter = lambda k: stream.data.get(k, 0)
        form = '''
 Relative Velocity  : {o_relativeVelocity:0.1f}   (m/s)
 Periapsis          : {o_PeA:0.1f} (m)
 Apoapsis           : {o_ApA:0.1f} (m)
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
    log.info('disconnect command called')
    if stream.loop is not None:
        stream.loop.stop()
        stream.make_connection.clear()
    else:
        parent_form.wInfo.feed = 'Not connected!'


def haiku(args, widget_proxy, parent_form, stream):
    """
    haiku

    Puts a haiku on the screen.

    Usage:
      haiku
    """

    log.info('haiku command called')

    haiku = '''
 A field of cotton--
 as if the moon
 had flowered.
 - Matsuo Bashō (松尾 芭蕉)'''

    def multiline_feed(widget_instance):
        widget_instance.values = haiku.split('\n')
    parent_form.wMain.feed = partial(multiline_feed, parent_form.wMain)


def rate(args, widget_proxy, parent_form, stream):
    """
    rate

    Change the rate at which Kerminal receives updates from Telemachus

    Usage:
      rate <interval>

    Arguments:
      <interval>    The interval length in milliseconds between messages from
                    Telemachus. Input should be an integer, will be rounded if a
                    decimal number is used. Divide 1 by this number to get the rate
                    in Hz.

    Examples:
      "rate 200": Kerminal will receive about 5 updates every second.
      "rate 2000": Kerminal will receive about 1 update every 2 seconds.
    """
    log.info('rate command called')
    if not stream.connected:
        parent_form.wInfo.feed = 'Not connected!'
        return

    try:
        interval = int(args['<interval>'])
    except ValueError:
        try:
            interval_f = float(args['<interval>'])
        except ValueError:
            parent_form.wInfo.feed = 'Rate interval must be a number!'
            return
        else:
            interval = round(interval_f)
    stream.msg_queue.put({'rate': interval})


def send(args, widget_proxy, parent_form, stream):
    """
    send

    Send an arbitrary JSON string to the Telemachus server (if connected).

    Usage:
      send <json-string>

    Being able to send arbitrary API strings during live execution is very handy for
    development.

    Examples:
      send {"+": ["v.altitude", "o.period"]}
      send {"rate": 2000, "+": ["t.universalTime"]}
      send {"run": ["f.stage"]}
    """

    log.info('info command called')

    if not stream.connected:
        parent_form.wInfo.feed = 'Not connected!'
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


def quits(args, widget_proxy, parent_form, stream):
    """
    quit

    Shut down Kerminal.

    Usage:
      quit [options]

    Options:
      -h --help    Show this help message and exit
    """

    log.info('quit command called')

    parent_form.parentApp.setNextForm(None)
    parent_form.parentApp.switchFormNow()
    disconnect(args, widget_proxy, parent_form, stream)


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
                          'log': logs,
                          'rate': rate,
                          'send': send,
                          'quit': quits,
                          'exit': quits}
        #self.create()

    def process_command_complete(self, command_line, control_widget_proxy):
        for comm in command_line.split(';'):
            argv = comm.split()
            try:
                command = argv.pop(0)
            except IndexError:
                return
            command_func = self._commands.get(command)
            if command_func is None:
                self.parent.wInfo.feed = 'command "{0}" not recognized. See "help"'.format(command)
                return
            try:
                args = docopt(command_func.__doc__,
                              version='Kerminal v {0}'.format(__version__),
                              argv=argv)
            except DocoptExit as e:
                self.parent.wInfo.feed = 'command usage incorrect. See "help {0}"'.format(command)
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

        log.info('help command called')

        #if parent_form.wMain

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

  connect <host-address> [<port>]
   -- Connect to a Telemachus server if not already connected.
  demo
   -- Show a demonstration of data streaming if connected.
  disconnect
   -- Disconnect from the Telemachus server if currently connected.
  help
   -- Print this help message.
  log [commands]
   -- Utilities for logging data to file; see "help log" for in depth details.
  send <json_string>
   -- Send an arbitrary JSON string to the Telemachus server (if connected).
  quit
   -- Shut down Kerminal.
'''.format(version=__version__)

        def multiline_feed(widget_instance):
            widget_instance.values = help_msg.split('\n')
        parent_form.wMain.feed = partial(multiline_feed, parent_form.wMain)
