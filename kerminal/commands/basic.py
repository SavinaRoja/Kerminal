# -*- coding: utf-8 -*-

import json
import logging

from . import invalid_if_not_connected

log = logging.getLogger('kerminal.commands')


@invalid_if_not_connected
def abort(args, widget_proxy, form, stream):
    """\
abort

Send a signal to the craft to execute Abort

Usage:
  abort

Your craft must have an abort action group defined or this will have no effect.
You may set the abort action during craft construction in either the VAB or SPH.
    """

    stream.msg_queue.put({'run': ['f.abort']})
    form.info('Sending Abort message')


@invalid_if_not_connected
def action(args, widget_proxy, form, stream):
    """\
action

Send a signal to execute a numbered Action Group command on the craft

Usage:
  action <number>

Arguments:
  <number>    Must be an integer from 1 to 10

Your craft must have an action group defined for this number or this command
will have no effect. You may define custom action groups during craft
construction in either the VAB or SPH.

Example:

To execute Action Group 5, do:
  "action 5"
    """

    try:
        group_number = int(args['<number>'])
    except ValueError:
        form.error('Action number must be an integer')
        return

    if 0 >= group_number >= 10:
        form.error('Action number must be an integer from 1 to 10')
        return

    stream.msg_queue.put({'run': ['f.ag{}'.format(group_number)]})
    form.info('Sending Action Group {} message'.format(group_number))


@invalid_if_not_connected
def brakes(args, widget_proxy, form, stream):
    """\
brakes

Enable or disable the landing gear brakes of the craft

Usage:
  brakes ([off | on])

Commands:
  off    Disable the craft's landing gear brakes
  on     Enable the craft's landing gear brakes
    """

    if args['on']:
        stream.msg_queue.put({'run': ['f.brake[True]']})
        form.info('Sending Brakes On message')

    elif args['off']:
        stream.msg_queue.put({'run': ['f.brake[False]']})
        form.info('Sending Brakes Off message')


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


@invalid_if_not_connected
def fbw(args, widget_proxy, form, stream):
    """\
fbw

Enable, disable, and set the Telemachus FlyByWire control system

Usage:
  fbw (on | off)
  fbw [--yaw=<magnitude>] [--roll=<magnitude>] [--pitch=<magnitude>]

Options:
  -y --yaw=<magnitude>      Set a new value for yaw
  -r --roll=<magnitude>     Set a new value for roll
  -p --pitch=<magnitude>    Set a new value for pitch

Commands:
  on     Enable FlyByWire
  off    Disable FlyByWire
"""
    if args['on']:
        stream.msg_queue.put({'run': ['v.setFbW[1]']})
        form.info('Sending Activate FlyByWire message')
        return
    elif args['off']:
        stream.msg_queue.put({'run': ['v.setFbW[0]']})
        form.info('Sending Deactivate FlyByWire message')
        return

    actions = []
    if args['--yaw'] is not None:
        try:
            yaw = float(args['--yaw'])
        except ValueError:
            form.error('Value for yaw must be a number')
        else:
            actions.append('v.setYaw[{}]'.format(yaw))
    if args['--roll'] is not None:
        try:
            roll = float(args['--roll'])
        except ValueError:
            form.error('Value for roll must be a number')
        else:
            actions.append('v.setRoll[{}]'.format(roll))
    if args['--pitch'] is not None:
        try:
            pitch = float(args['--pitch'])
        except ValueError:
            form.error('Value for pitch must be a number')
        else:
            actions.append('v.setPitch[{}]'.format(pitch))

    if not actions:
        form.error('fbw command received no instructions!')
    else:
        stream.msg_queue.put({'run': actions})


@invalid_if_not_connected
def gear(args, widget_proxy, form, stream):
    """\
gear

Raise of lower the landing gear of the craft

Usage:
  gear (up | down | on | off)

Commands:
  up      Raise the landing gear on the craft
  down    Lower the landing gear on the craft
  on      Synonym for down; lower the landing gear of the craft
  off     Synonym for up; raise the landing gear of the craft
    """

    if args['down'] or args['on']:
        stream.msg_queue.put({'run': ['f.gear[True]']})
        form.info('Sending Gear Down message')

    elif args['up'] or args['off']:
        stream.msg_queue.put({'run': ['f.gear[False]']})
        form.info('Sending Gear Up message')


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


@invalid_if_not_connected
def lights(args, widget_proxy, form, stream):
    """\
lights

Turn the lights of the craft on or off

Usage:
  lights (off | on)

Commands:
  off    Turn the lights of the craft off
  on     Turn the lights of the craft on
    """

    if args['on']:
        stream.msg_queue.put({'run': ['f.light[True]']})
        form.info('Sending Lights On message')

    elif args['off']:
        stream.msg_queue.put({'run': ['f.light[False]']})
        form.info('Sending Lights Off message')


@invalid_if_not_connected
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


@invalid_if_not_connected
def rcs(args, widget_proxy, form, stream):
    """\
rcs

Enable or disable RCS on the craft

Usage:
  rcs (off | on)

Commands:
  off    Disable RCS on the craft
  on     Enable RCS on the craft
    """

    if args['on']:
        stream.msg_queue.put({'run': ['f.rcs[True]']})
        form.info('Sending RCS On message')

    elif args['off']:
        stream.msg_queue.put({'run': ['f.rcs[False]']})
        form.info('Sending RCS Off message')


@invalid_if_not_connected
def sas(args, widget_proxy, form, stream):
    """\
sas

Enable or disable SAS on the craft

Usage:
  sas (off | on)

Commands:
  off    Disable SAS on the craft
  on     Enable SAS on the craft
    """
    if not stream.connected:
        form.error('Not connected!')
        return

    if args['on']:
        stream.msg_queue.put({'run': ['f.sas[True]']})
        form.info('Sending SAS On message')

    elif args['off']:
        stream.msg_queue.put({'run': ['f.sas[False]']})
        form.info('Sending SAS Off message')


@invalid_if_not_connected
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


@invalid_if_not_connected
def stage(args, widget_proxy, form, stream):
    """\
stage

Sends a signal to the craft to perform its next stage action

Usage:
  stage

Options:
  -h --help    Show this help message and exit
    """

    stream.msg_queue.put({'run': ['f.stage']})
    form.info('Sending Stage message')


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


@invalid_if_not_connected
def throttle(args, widget_proxy, form, stream):
    """\
throttle

Adjust the throttle value on the craft

Usage:
  throttle (up | down)
  throttle <percent>

Arguments:
  <percent>      Set the throttle to the specified percentage

Commands:
  up             Increase the throttle by 10%
  down           Decrease the throttle by 10%
    """

    if args['up']:
        stream.msg_queue.put({'run': ['f.throttleUp']})
        form.info('Increasing throttle by 10%')
    elif args['down']:
        stream.msg_queue.put({'run': ['f.throttleDown']})
        form.info('Decreasing throttle by 10%')
    elif args['<percent>']:
        try:
            value = float(args['<percent>'])
        except ValueError:
            form.error('Set Throttle value must be a number')
            return
        if value < 0:
            stream.msg_queue.put({'run': ['f.setThrottle[0.0]']})
            form.warning('Setting throttle to 0%, cannot go lower!')
        elif value > 100:
            stream.msg_queue.put({'run': ['f.setThrottle[1.0]']})
            form.warning('Setting throttle to 100%, cannot go higher!')
        else:
            mag = value / 100
            stream.msg_queue.put({'run': ['f.setThrottle[{}]'.format(mag)]})
            form.info('Setting throttle to {}%'.format(value))


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
