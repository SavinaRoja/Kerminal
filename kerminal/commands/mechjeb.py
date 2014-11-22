# -*- coding: utf-8 -*-

"""
Commands pertaining to the use of MechJeb via Telemachus
"""

#Only MechJeb stuff currently supported in Telemachus is SmartASS
#mj_actions = ['mj.smartassoff',    # Smart ASS Off
              #'mj.node',           # Points in the direction of next node
              #These are all with respect to orbiting body
              #'mj.prograde',       # Prograde
              #'mj.retrograde',     # Retrograde
              #'mj.normalplus',     # Normal Plus
              #'mj.normalminus',    # Normal Minus
              #'mj.radialplus',     # Radial Plus
              #'mj.radialminus',    # Radial Minus
              ##Only make sense with a target selected
              #'mj.targetplus',     # Target Plus
              #'mj.targetminus',    # Target Minus
              #'mj.relativeplus',   # Relative Plus
              #'mj.relativeminus',  # Relative Minus
              #'mj.parallelplus',   # Parallel Plus
              #'mj.parallelminus',  # Parallel Minus
              ##Is it preferred to use mj.surface2?
              #'mj.surface',        # Surface [float heading, float pitch]
              #'mj.surface2',       # Surface [double heading, double pitch]
              #]

#If you call a MechJeb SmartASS operation, the server will send a return code
#on the next pulse. If you send {"run":['mj.prograde']}, then on the next pulse
#you will received {'mj.prograde': <n>}. Here is an explanation of the codes:

# 0 = Success, Signal found
# 1 = Failure, Game is paused
# 2 = Failure, Possibly unpowered antenna
# 3 = Failure, Antenna is deactivated
# 4 = Failure, Unable to reach antenna (Used for Line of sight and delay mods?)
# 5 = Failure, MechJeb part not found


#from functools import wraps

#TODO: Implement status callbacks on MechJeb functions, it seems these could in
#theory also be employed for non-MJ actions
#def spawn_status_callback(f):
    #@wraps(f)
    #def wrapper(args, widget_proxy, form, stream):
        #return f(args, widget_proxy, form, stream)
    #return wrapper

from . import invalid_if_not_connected

@invalid_if_not_connected
def prograde(args, widget_proxy, form, stream):
    pass

