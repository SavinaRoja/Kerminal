# encoding: utf-8

"""
kerminal.commands handles the execution of commands in the Kerminal Command Line
"""

from .. import __version__


from docopt import docopt, DocoptExit
#from functools import wraps, partial
import logging
#import os
import weakref
#import sys

#from ..communication import OrderedSet

#from ..telemachus_api import orbit_plots_names, plotables , orbit_plotables

log = logging.getLogger('kerminal.commands')


from functools import wraps


def invalid_if_not_connected(f):
    @wraps(f)
    def wrapper(args, widget_proxy, form, stream):
        if not stream.connected:
            form.error('Not connected!')
            return
        else:
            return f(args, widget_proxy, form, stream)
    return wrapper


from . import mechjeb
from . import basic
from . import logs


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

        self._commands = {'abort': basic.abort,
                          'action': basic.action,
                          'brakes': basic.brakes,
                          'connect': basic.connect,
                          'disconnect': basic.disconnect,
                          'fbw': basic.fbw,
                          'gear': basic.gear,
                          'haiku': basic.haiku,
                          'help': self.helps,
                          'lights': basic.lights,
                          'log': logs.logs,
                          'rate': basic.rate,
                          'rcs': basic.rcs,
                          'sas': basic.sas,
                          'sa': mechjeb.smartass,
                          'send': basic.send,
                          'stage': basic.stage,
                          'text': basic.text,
                          'telemetry': basic.telemetry,
                          'throttle': basic.throttle,
                          'quit': basic.quits,
                          'exit': basic.quits,  # overlaps with quit
                          }

    def process_command_complete(self, command_line, control_widget_proxy):
        for comm in command_line.split(';'):
            argv = comm.split()
            try:
                command = argv.pop(0)
            except IndexError:
                return
            command_func = self._commands.get(command)
            if command_func is None:
                self.form.error('command "{}" not recognized. See "help"'.format(command))
                return
            try:
                args = docopt(command_func.__doc__,
                              version='Kerminal v {}'.format(__version__),
                              argv=argv,
                              options_first=True
                              )  # Allow negative numbers as arguments in options
            except DocoptExit as e:
                self.form.error('command usage incorrect. See "help {}"'.format(command))
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

        if args['<command>']:
            if args['<command>'] not in self._commands:
                return
            help_msg = self._commands[args['<command>']].__doc__
        else:
            help_msg = '''\
Kerminal v {version} Command Listing

Each command with usage definition and brief description. Items in angle-
brackets like "<item>" are arguments, meant to be replace by appropriate text.
Arguments enclosed in brackets like "[<item>]" are optional; they may have
defaults or be unnecessary under some circumstances. Type "help <command>" to
see greater detail about any command.

abort
 -- Send signal to craft to execute Abort.
action <number>
 -- Send signal to craft to execute an Action Group command.
brakes (off | on)
 -- Enable or disable landing gear brakes.
connect <host-address> [<port>]
 -- Connect to a Telemachus server if not already connected.
disconnect
 -- Disconnect from the Telemachus server if currently connected.
fbw (on | off | [--yaw=<magnitude>] [--roll=<magnitude>] [--pitch=<magnitude>]))
 -- Utilize the Telemachus FlyByWire system. Not well suited to this interface!
gear (up | down | on | off)
 -- Raise or lower the landing gear.
help
 -- Print this help message.
lights (off | on)
 -- Turn the craft's lights on or off.
log [commands]
 -- Utilities for logging data to file; see "help log" for in depth details.
rcs (off | on)
 -- Enable or disable the craft's RCS.
sas (off | on)
 -- Enable or disable the craft's SAS.
sa [commands] [<arg>...]
 -- Utilize MechJeb SmartAss with various commands; disable with "off" command.
send <json_string>
 -- Send an arbitrary JSON string to the Telemachus server (if connected).
stage
 -- Tell the craft to stage.
telemetry
 -- Bring up the screen for telemetry information.
text
 -- Shows the most recent text on screen.
throttle (up | down | <percent>)
 -- Set the throttle of the craft to <percent>, or increment by +/-10%
quit
 -- Shut down Kerminal.
'''.format(version=__version__)
        form.show_text(msg=help_msg)
