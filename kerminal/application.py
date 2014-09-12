# encoding: utf-8

"""
This module represents the Application level for Kerminal
"""

from npyscreen import NPSAppManaged

from . import forms, __version__
from .communication import CommsThread
from functools import partial
from time import strftime

#Original demo
#class KerminalApp(NPSAppManaged):
#    keypress_timeout_default = 1  # this is as short as possible
#    #keypress_timeout = 1
#
#    def onStart(self):
#        self.stream = CommsThread()
#        self.stream.start()
#        self.addForm('MAIN', forms.ConnectQuery)
#        self.addFormClass('CONNECTION', forms.Connection)

import logging

log = logging.getLogger('Kerminal.application')


def status_line1(thread):
    status = ' Kerminal v {0} - Sys. Time: {1} '.format(__version__,
                                                        strftime("%Y-%m-%d %H:%M:%S"))
    if thread.connected:
        status += '- Connected: {0} '.format(thread.data.get('v.name'))
    return status


class KerminalApp(NPSAppManaged):
    keypress_timeout_default = 1

    def onStart(self):
        self.stream = CommsThread()
        self.stream.start()
        self.main_form = self.addForm('MAIN', forms.KerminalForm)

        #This gets around the use of a standard form class not having the
        #add_live method
        self.main_form.live_widgets.append(self.main_form.wStatus1)
        self.main_form.live_widgets.append(self.main_form.wStatus2)
        self.main_form.wStatus1.feed = partial(status_line1, self.stream)
        self.main_form.wStatus2.feed = lambda: ' Kerminal Command Line '
