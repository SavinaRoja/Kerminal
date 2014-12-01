# -*- coding: utf-8 -*-

"""
Commands pertaining to the use of MechJeb via Telemachus
"""

from functools import partial

from . import invalid_if_not_connected


def mj_callback(form, key, msg):
    actions = {None: partial(form.critical, 'No Response from MJ!'),
               0: partial(form.info, 'SmartASS action success.'),
               1: partial(form.error, 'SmartASS failed: Game paused.'),
               2: partial(form.error, 'SmartASS failed: Antenna unpowered?'),
               3: partial(form.error, 'SmartASS failed: Antenna inactive.'),
               4: partial(form.error, 'SmartASS failed: Antenna unreachable.'),
               5: partial(form.error, 'SmartASS failed: No MechJeb part.')}
    response_code = msg.pop(key, None)
    actions[response_code]()


@invalid_if_not_connected
def smartass(args, widget_proxy, form, stream):
    """\
sa

Utilize MechJeb SmartASS to lock orientation vector. Disable with the "off"
subcommand.

Usage:
  sa (off | node | prograde | retrograde | normalplus | normalminus |
      radialplus | radialminus | targetplus | targetminus | relativeplus |
      relativeminus | parallelplus | parallelminus)
  sa surface <heading> <pitch> <roll>

Standard Commands (no target required):
  off            Disable SmartASS.
  node           Orient along next node.
  prograde       Orient along orbital velocity prograde.
  retrograde     Orient along orbital velocity retrograde.
  normalplus     Orient along orbital velocity normal plus.
  normalminus    Orient along orbital velocity normal minus.
  radialplus     Orient along the orbital velocity radial plus.
  radialminus    Orient along the orbital velocity radial minus.
  surface <heading> <pitch> <roll>    Set orientation based on surface angles.

Targeted Commands (target required):
  targetplus       Orient towards the target.
  targetminus      Orient away from the target.
  relativeplus     Orient along relative velocity.
  relativeminus    Orient against relative velocity.
  parallelplus     Orient along parallel velocity component.
  parallelminus    Orient against parallel velocity component.

Comments:
  When in a prograde orbit, "normalplus" corresponds to "up"/"north" while
  "normalminus" corresponds to "down"/"south". This is reversed in a retrograde
  orbit.

  Conversely, "radialplus" will correspond to "away from orbited body" in both
  prograde and retrograde orbits and "radialminus" will correspond to "towards
  orbited body".

  Targeted Commands will not work unless there is a target selected. Selecting
  a target with Telemachus is unfortunately impossible at this time and must be
  done manually in KSP. In the future, Kerminal may warn about the use of these
  commands while nothing is targeted.
    """

    if args['surface']:
        try:
            heading = float(args['<heading>'])
        except ValueError:
            form.error('Value for heading must be a number!')
            return
        try:
            pitch = float(args['<pitch>'])
        except ValueError:
            form.error('Value for pitch must be a number!')
            return
        try:
            roll = float(args['<roll>'])
        except ValueError:
            form.error('Value for roll must be a number!')
            return
        signal = 'mj.surface2[{},{},{}]'.format(heading, pitch, roll)

    elif args['off']:
        signal = 'mj.smartassoff'

    elif args['node']:
        signal = 'mj.node'

    elif args['prograde']:
        signal = 'mj.prograde'

    elif args['retrograde']:
        signal = 'mj.retrograde'

    elif args['normalplus']:
        signal = 'mj.normalplus'

    elif args['normalminus']:
        signal = 'mj.normalminus'

    elif args['radialplus']:
        signal = 'mj.radialplus'

    elif args['radialminus']:
        signal = 'mj.radialminus'

    elif args['targetplus']:
        signal = 'mj.targetplus'

    elif args['targetminus']:
        signal = 'mj.targetminus'

    elif args['relativeplus']:
        signal = 'mj.relativeplus'

    elif args['relativeminus']:
        signal = 'mj.relativeminus'

    elif args['parallelplus']:
        signal = 'mj.parallelplus'

    elif args['parallelminus']:
        signal = 'mj.parallelminus'

    stream.msg_queue.put({'run': [signal]})
    stream.add_callback(partial(mj_callback, signal))
