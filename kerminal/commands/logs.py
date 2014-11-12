# encoding: utf-8

"""
"""

from functools import partial
import logging
import os

log = logging.getLogger('kerminal.commands')
log.debug('commands')


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
        return

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
        preserve = ['t.universalTime', 'v.missionTime']
        for var in stream.data_log_vars:
            if var not in preserve:
                stream.data_log_vars.remove(var)
                stream.subscription_manager.drop(var)
        return

    if args['all']:
        for var in ['t.universalTime', 'v.missionTime', 'sys.time'] + plotables:
            stream.data_log_vars.add(var)

        return

    if args['add']:
        for var in args['<api-variable>']:
            stream.data_log_vars.add(var)
            #stream.subscription_manager.add(var)

    if args['remove']:
        for var in args['<api-variable>']:
            try:
                stream.data_log_vars.remove(var)
                #stream.data_log_vars.discard(var)
            except KeyError:
                parent_form.wInfo.feed = 'Log variable already not in use'
            else:
                stream.subscription_manager.drop(var)

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
