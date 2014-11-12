# encoding: utf-8

"""
This module represents the Application level for Kerminal
"""

import npyscreen2

from . import forms, __version__
from .communication import CommsThread
from functools import partial
from time import strftime

import logging

log = logging.getLogger('npyscreen2.kerminal')


#class KerminalHeader(npyscreen2.TextField):

    #def __init__(self, form, parent, *args, **kwargs):
        #super(KerminalHeader, self).__init__(form, parent, *args, **kwargs)

    #def feed(self):


def header_feed(thread):
    status = ' Kerminal v {0} - Sys. Time: {1} '.format(__version__,
                                                        strftime("%Y-%m-%d %H:%M:%S"))
    if thread.connected:
        status += '- Connected: {0} '.format(thread.data.get('v.name'))
    return status
    #self.value = status


class KerminalApp(npyscreen2.App):
    def __init__(self):
        super(KerminalApp, self).__init__(keypress_timeout_default=1)

    def on_start(self):
        self.stream = CommsThread()
        self.stream.start()
        self.main_form = self.add_form(KerminalForm, 'MAIN')
        self.main_form.header.feed = partial(header_feed, self.stream)


class KerminalForm(npyscreen2.Form):
    def __init__(self, *args, **kwargs):
        super(KerminalForm, self).__init__(*args, **kwargs)

        self.add(npyscreen2.Widget,
                 widget_id='dummy',
                 editable=True)

        self.top_bar = self.add(npyscreen2.BorderBox,
                                widget_id='top_bar',
                                preserve_instantiation_dimensions=False,
                                auto_manage=False,
                                top=True,
                                bottom=False,
                                left=False,
                                right=False,
                                max_height=self.max_height,
                                max_width=self.max_width)

        self.bot_bar = self.add(npyscreen2.BorderBox,
                                widget_id='bottom_bar',
                                preserve_instantiation_dimensions=False,
                                auto_manage=False,
                                top=True,
                                bottom=False,
                                left=False,
                                right=False,
                                max_height=self.max_height,
                                max_width=self.max_width)

        self.header = self.add(npyscreen2.TextField,
                               widget_id='header',
                               relx=self.relx + 1,
                               rely=self.rely,
                               height=1,
                               auto_manage=False,
                               editable=False,
                               value=' Kerminal Header ',
                               color='LABEL',
                               bold=True)

        self.cl_header = self.add(npyscreen2.TextField,
                                  widget_id='cl_header',
                                  relx=self.relx + 1,
                                  rely=self.rely,
                                  height=1,
                                  auto_manage=False,
                                  editable=False,
                                  value=' Kerminal Command Line ',
                                  color='LABEL',
                                  bold=True)

        self.command_line = self.add(npyscreen2.TextField,
                                     widget_id='command_line',
                                     relx=self.relx,
                                     rely=self.rely + self.height - 1,
                                     auto_manage=False,
                                     editable=True,
                                     value='Press ESC to enter commands')

        self.status_prefix = self.add(npyscreen2.TextField,
                                      widget_id='status_prefix',
                                      relx=self.relx,
                                      rely=self.rely + self.height - 3,
                                      auto_manage=True,
                                      editable=False,
                                      value='Status:',
                                      height=1,
                                      color='CONTROL')

        self.status = self.add(npyscreen2.TextField,
                               widget_id='status_prefix',
                               relx=self.relx,
                               rely=self.rely + self.height - 3,
                               auto_manage=True,
                               editable=False,
                               value='',
                               height=1,
                               feed_reset=True,
                               #feed_reset_time=10,
                               )

    def while_waiting(self):
        self.call_feed()
        self.display()

    def info(self, msg):
        self.status_prefix.value = 'INFO:'
        self.status.feed = lambda: msg

    def warning(self, msg):
        self.status_prefix.value = 'WARNING:'
        self.status.feed = lambda: msg

    def error(self, msg):
        self.status_prefix.value = 'ERROR:'
        self.status.feed = lambda: msg

    def critical(self, msg):
        self.status_prefix.value = 'CRITICAL:'
        self.status.feed = lambda: msg

    def resize(self):
        self.top_bar.multi_set(rely=self.rely,
                               relx=self.relx,
                               max_height=self.max_height,
                               max_width=self.max_width)
        self.bot_bar.multi_set(rely=self.rely + self.height - 2,
                               relx=self.relx,
                               max_height=self.max_height,
                               max_width=self.max_width)
        self.header.multi_set(rely=self.rely,
                              relx=self.relx + 1,
                              max_width=self.max_width,
                              max_height=1)
        self.cl_header.multi_set(rely=self.rely + self.height - 2,
                                 relx=self.relx + 1,
                                 max_width=self.max_width,
                                 max_height=1)
        self.command_line.multi_set(rely=self.rely + self.height - 1,
                                    relx=self.relx,
                                    max_height=1,
                                    max_width=self.max_width)
        self.status_prefix.multi_set(rely=self.rely + self.height - 3,
                                     relx=self.relx,
                                     max_width=self.max_width,
                                     max_height=1)
        status_offset = len(self.status_prefix.value) + 1
        self.status.multi_set(rely=self.rely + self.height - 3,
                              relx=self.relx + status_offset,
                              max_width=self.max_width - status_offset,
                              max_height=1)


