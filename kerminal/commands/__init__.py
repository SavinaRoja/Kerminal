# encoding: utf-8

"""
kerminal.commands handles the execution of commands in the Kerminal Command Line
"""

from .. import __version__
from .logs import logs

from docopt import docopt, DocoptExit
#from functools import wraps, partial
import json
import logging
#import os
import weakref
#import sys

#from ..communication import OrderedSet

#from ..telemachus_api import orbit_plots_names, plotables , orbit_plotables

log = logging.getLogger('kerminal.commands')


#The docstrings for commands are *functional*, they define how the command may
#be called and provide the help for the command. As such they are formatted in
#an unconventional (not PEP8) manner
def connect(args, widget_proxy, form, stream):
    """\
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
        form.warning('Could not connect, already connected to a server!')
        return

    if args['<port>'] is None:
        port = 8085
    else:
        try:
            port = int(args['<port>'])
        except ValueError:
            form.error('Port must be a number')
            return

    #Instructions to the Communication Thread to make the connection
    stream.address = args['<host-address>']
    stream.port = port
    stream.make_connection.set()

    form.info('Making connection to {}:{}'.format(args['<host-address>'],
                                                  port))

    #Wait for the Communication Thread to tell us it is done
    stream.connect_event.wait()
    stream.connect_event.clear()

    if not stream.connected:  # Failed
        form.error('Could not connect')
    else:
        form.info('Connected!')

    form.show_smart()


def disconnect(args, widget_proxy, form, stream):
    """\
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
        form.warning('Not currently connected!')
        return

    form.show_text()


#TODO: Figure out why full unicode support is missing in npyscreen2
def haiku(args, widget_proxy, form, stream):
    """\
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

    form.show_text(msg=haiku)

    #def multiline_feed(widget_instance):
        #widget_instance.values = haiku.split('\n')
    #form.main.feed = partial(multiline_feed, form.main)


def rate(args, widget_proxy, form, stream):
    """\
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
        form.error('Not connected!')
        return

    try:
        interval = int(args['<interval>'])
    except ValueError:
        try:
            interval_f = float(args['<interval>'])
        except ValueError:
            form.error('Rate interval must be a number!')
            return
        else:
            interval = round(interval_f)
    stream.msg_queue.put({'rate': interval})


def send(args, widget_proxy, form, stream):
    """\
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
        form.error('Not connected!')
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


def text(args, widget_proxy, form, stream):
    """\
text

Shows the most recently displayed text on screen

Usage:
  text [options]

Options:
  -h --help    Show this help message and exit
    """
    form.show_text()


def telemetry(args, widget_proxy, form, stream):
    """\
telemetry

Brings up the telemetry screen

Usage:
  smart [options]

Options:
  -h --help    Show this help message and exit
    """
    form.show_smart()


def quits(args, widget_proxy, form, stream):
    """\
quit

Shut down Kerminal.

Usage:
  quit [options]

Options:
  -h --help    Show this help message and exit
    """

    log.info('quit command called')

    form.parent_app.set_next_form(None)
    form.parent_app.switch_form_now()
    disconnect(args, widget_proxy, form, stream)


class KerminalCommands(object):
    def __init__(self, form, parent):
        try:
            self.form = weakref.proxy(form)
        except TypeError:
            self.form = form

        try:
            self.parent = weakref.proxy(parent)
        except TypeError:
            self.parent = parent

        self._commands = {'connect': connect,
                          'disconnect': disconnect,
                          'haiku': haiku,
                          'help': self.helps,
                          'log': logs,
                          'rate': rate,
                          'send': send,
                          'text': text,
                          'telemetry': telemetry,
                          'quit': quits,
                          'exit': quits}

    def process_command_complete(self, command_line, control_widget_proxy):
        for comm in command_line.split(';'):
            argv = comm.split()
            try:
                command = argv.pop(0)
            except IndexError:
                return
            command_func = self._commands.get(command)
            if command_func is None:
                self.form.error('command "{0}" not recognized. See "help"'.format(command))
                return
            try:
                args = docopt(command_func.__doc__,
                              version='Kerminal v {0}'.format(__version__),
                              argv=argv)
            except DocoptExit as e:
                self.form.error('command usage incorrect. See "help {0}"'.format(command))
                log.debug(e)
            else:
                command_func(args,
                             control_widget_proxy,
                             self.form,
                             self.form.parent_app.stream)

    def helps(self, args, widget_proxy, form, stream):
        """\
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
            help_msg = '''\
Kerminal v {version} Command Listing

Each command with usage definition and brief description. Items in angle-
brackets like "<item>" are arguments, meant to be replace by appropriate text.
Arguments enclosed in brackets like "[<item>]" are optional; they may have
defaults or be unnecessary under some circumstances. Type "help <command>" to
see greater detail about any command.

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
telemetry
 -- Bring up the screen for telemetry information
text
 -- Shows the most recent text on screen
quit
 -- Shut down Kerminal.
'''.format(version=__version__)
        form.show_text(msg=help_msg)

        #def multiline_feed(widget_instance):
            #widget_instance.values = help_msg.split('\n')
        #form.main.feed = partial(multiline_feed, form.main)
