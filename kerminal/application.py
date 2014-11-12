# encoding: utf-8

"""
This module represents the Application level for Kerminal
"""

import npyscreen2

from .forms import KerminalForm
from .communication import CommsThread

import logging

log = logging.getLogger('npyscreen2.kerminal')


class KerminalApp(npyscreen2.App):
    def __init__(self):
        super(KerminalApp, self).__init__(keypress_timeout_default=1)

    def on_start(self):
        self.stream = CommsThread()
        self.stream.start()
        self.main_form = self.add_form(KerminalForm, 'MAIN')
