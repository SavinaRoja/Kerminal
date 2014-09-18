# encoding: utf-8

"""
kerminal.commands handles the execution of commands in the Kerminal Command Line
"""

from .. import __version__

from docopt import docopt, DocoptExit
from functools import wraps, partial
import json
import logging
import os
import sys

from ..communication import OrderedSet

from ..telemachus_api import orbit_plots_names, plotables

log = logging.getLogger('kerminal.commands')
log.debug('commands')


#The docstrings for commands follow a modified PEP8! (80 + indent) characters
#this is to allow conformity of help messages regardless of indent level
def connect(args, widget_proxy, parent_form, stream):
    """
    connect

    Connect to a Telemachus server if not already connected.

    Usage:
      connect <host-address> <port>
    """

    log.info('connect command called')

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

    log.info('demo command called')
    if not stream.connected:
        parent_form.wInfo.feed = 'Not connected!'
        return

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


#TODO: logs is big enough to deserve its own file
def logs(args, widget_proxy, parent_form, stream):
    """
    log

    The log command contains the utilities for configuring, displaying,
    enabling/disabling the logging of data to file from the connected craft. When
    data logging is ON logging parameters may not be changed (neither the filename
    nor the set of variables); turn data logging OFF before making changes.

    Usage:
      log [add <api-variable> ...| remove <api-variable> ...]
      log [off | on | all | none | status]
      log file <filename> [--overwrite | --append]

    File Options:
      -a --append       Append to the specified file if it already exists.
      -o --overwrite    Overwrite the specified file if it already exists.

    Commands:
      add       Add the api variables to the set to be logged.
      remove    Remove the api variables from the set to be logged.
      off       Disable data logging, no effect if already off.
      on        Enable data logging, no effect if already on.
      all       Add all plotable api variables to be logged.
      none      Remove all plotable api variables from being logged except for
                "t.universalTime", and "v.missionTime". These must be removed
                explicitly as they are common and critical.
      file      Choose the file location on disk to write to.
      status    Show the current logging configuration.

    The logging of data is a high priority asset of Kerminal, if you experience any
    problems or would like to see changes or new features, contact the developer!

    Kerminal is probably not going to handle all of your munging, but it should be
    able to generate your data a capably as possible.

    Examples:
      log add v.altitude o.period
        Adds "v.altitude" and "o.period" to the set of logged variables.
      log remove v.altitude o.period
        Removes "v.altitude" and "o.period" from the set of logged variables.
      log all; log file alldata.txt; log on
        Sets all variables to be logged, sets file to "alldata.txt", then starts the
        logging.
    """

    log.info('log command called')
    log.debug(args)

    #Status is a valid command regardless of connection status or log activity
    if args['status']:

        def multiline_feed(widget_instance):

            form = '''
 Data Logging Active : {0}
 Data Log File       : {1}
 Logging Variables   : \
'''.format(str(stream.data_log_on), os.path.abspath(stream.data_log_file))

            first = True
            for var in stream.data_log_vars:
                if first:
                    first = False
                    form += (var + '\n')
                else:
                    form += '                       {0}\n'.format(var)

            widget_instance.values = form.split('\n')

        parent_form.wMain.feed = partial(multiline_feed, parent_form.wMain)
        parent_form.wInfo.feed = 'Showing data logging status'

    #This makes sure that add, remove, all, none, and file cannot be used while
    #logging is active
    if stream.data_log_on and any([args['all'],
                                   args['none'],
                                   args['file'],
                                   args['add'],
                                   args['remove']]):
        parent_form.wInfo.feed = 'Parameters can\'t be changed while log is active'
        return

    #File cannot be changed while logging is on, but can be used
    if args['file']:
        if os.path.exists(args['<filename>']):
            if os.path.isdir(args['<filename>']):
                parent_form.wInfo.feed = 'Location is a directory!'
                return
            elif os.path.isfile(args['<filename>']):
                if args['--append']:  # Leave log file alone if appending
                    stream.data_log_file = args['<filename>']
                    parent_form.wInfo.feed = 'Log file set to {0}'.format(args['<filename>'])
                    return
                elif args['--overwrite']:  # Remove log file if overwriting
                    try:
                        os.remove(args['<filename>'])
                    except:
                        parent_form.wInfo.feed = 'Log file could not be overwritten'
                        return
                    else:
                        stream.data_log_file = args['<filename>']
                        return
                else:
                    parent_form.wInfo.feed = 'Could not set log file, already exists!'
                    return
        else:
            stream.data_log_file = args['<filename>']
            parent_form.wInfo.feed = 'Log file set to {0}'.format(args['<filename>'])
            return

    if args['none']:
        #Some values should not be removed by this command, however it shouldn't
        #add them if they are already missing
        preserve = OrderedSet(['t.universalTime', 'v.missionTime'])
        stream.data_log_vars = preserve.intersection(stream.data_log_vars)
        return

    if args['all']:
        for var in ['t.universalTime', 'v.missionTime', 'sys.time'] + plotables:
            stream.data_log_vars.add(var)
        return

    if args['add']:
        for var in args['<api-variable>']:
            stream.data_log_vars.add(var)

    if args['remove']:
        for var in args['<api-variable>']:
            try:
                stream.data_log_vars.remove(var)
            except KeyError:
                #TODO: set info message?
                pass

    #The following sub commands make no sense if we are not connected already
    if not stream.connected:
        parent_form.wInfo.feed = 'Not connected!'
        return

    if args['on']:
        if stream.data_log_on:
            parent_form.wInfo.feed = 'Logging already active'
        else:
            stream.data_log_on = True
            parent_form.wInfo.feed = 'Logging activated'
        return

    if args['off']:
        if not stream.data_log_on:
            parent_form.wInfo.feed = 'Logging already inactive'
        else:
            stream.data_log_on = False
            parent_form.wInfo.feed = 'Logging deactivated'
        return


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


def sub(args, widget_proxy, parent_form, stream):
    """
    sub

    Subscribe to one or more Telemachus data variables (if connected).

    Usage:
      sub (<api-variable> ... | --all)

    Options:
      -a --all    Subscribe to all plotable api variables.

    Example:
      sub v.altitude o.period
    """

    log.info('sub command called')

    if not stream.connected:
        parent_form.wInfo.feed = 'Not connected!'
        return

    import time

    if args['--all']:
        stream.msg_queue.put({'+': plotables})
    else:
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

    log.info('unsub command called')

    if not stream.connected:
        parent_form.wInfo.feed = 'Not connected!'
        return

    #Prohibit unsubbing from certain variables
    mandated = ['p.paused', 'v.name']
    removed = []
    kept = []
    for var in args['<api-variable>']:
        if var in mandated:
            removed.append(var)
        else:
            kept.append(var)

    if removed:
        log.debug('{0} prevented from being unsubbed'.format(removed))
        parent_stream.wInfo.feed = 'May not unsub: ' + ','.join(removed)

    stream.msg_queue.put({'-': kept})


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
                          'send': send,
                          'sub': sub,
                          'unsub': unsub,
                          'quit': quits,
                          'exit': quits}
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
  log [commands]
   -- Utilities for logging data to file; see "help log" for in depth details.
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
