# encoding: utf-8

"""
"""

from . import __version__
from .commands import KerminalCommands
from .containers import EscapeForwardingSmartContainer
from .widgets import TextCommandBox, KerminalStatusText

import npyscreen2

#import curses
from functools import partial
from time import strftime


def header_feed(thread):
    status = ' Kerminal v {0} - Sys. Time: {1} '.format(__version__,
                                                        strftime("%Y-%m-%d %H:%M:%S"))
    if thread.connected:
        status += '- Connected: {0} '.format(thread.data.get('v.name'))
    return status


class KerminalForm(npyscreen2.Form):
    def __init__(self, *args, **kwargs):
        super(KerminalForm, self).__init__(*args, **kwargs)

        self.action_controller = KerminalCommands(self, self)

        self.main = self.add(EscapeForwardingSmartContainer,
                             widget_id='main',
                             editable=True,)
        self.main.add(npyscreen2.TextField,
                      value='Test1',
                      editable=True,
                      )
        self.main.add(npyscreen2.TextField,
                      value='Test2',
                      editable=True,
                      )

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
                               auto_manage=False,
                               editable=False,
                               value=' Kerminal Header ',
                               color='LABEL',
                               bold=True,
                               feed=partial(header_feed,
                                            self.form.parent_app.stream))

        self.cl_header = self.add(npyscreen2.TextField,
                                  widget_id='cl_header',
                                  auto_manage=False,
                                  editable=False,
                                  value=' Kerminal Command Line ',
                                  color='LABEL',
                                  bold=True)

        self.command_line = self.add(TextCommandBox,
                                     widget_id='command_line',
                                     auto_manage=False,
                                     editable=True,
                                     value='Press ESC to enter commands')

        self.status_prefix = self.add(npyscreen2.TextField,
                                      widget_id='status_prefix',
                                      auto_manage=False,
                                      editable=False,
                                      value='STATUS:',
                                      height=1,
                                      #color='CONTROL',
                                      bold=True)

        self.status = self.add(KerminalStatusText,
                               widget_id='status',
                               auto_manage=True,
                               editable=False,
                               value='',
                               feed_reset=True,
                               #feed_reset_time=10,
                               )

    def set_up_exit_condition_handlers(self):
        super(KerminalForm, self).set_up_exit_condition_handlers()
        self.how_exited_handlers.update({'escape': self.toggle_commands})

    def toggle_commands(self, inpt=None):
        main_index = self.contained.index(self.main)
        command_line_index = self.contained.index(self.command_line)
        if self.edit_index == main_index:
            self.edit_index = command_line_index
            self.command_line.value = ''
        else:
            self.edit_index = main_index
            self.command_line.value = 'Press ESC to enter commands'

    def while_waiting(self):
        self.call_feed()
        self.display()

    def info(self, msg):
        self.status_prefix.value = 'INFO:'
        self.status_prefix.color = 'LABEL'
        self.status.feed = lambda: msg
        self.resize_status_line()

    def warning(self, msg):
        self.status_prefix.value = 'WARNING:'
        self.status_prefix.color = 'CAUTION'
        self.status.feed = lambda: msg
        self.resize_status_line()

    def error(self, msg):
        self.status_prefix.value = 'ERROR:'
        self.status_prefix.color = 'DANGER'
        self.status.feed = lambda: msg
        self.resize_status_line()

    def critical(self, msg):
        self.status_prefix.value = 'CRITICAL:'
        self.status_prefix.color = 'CRITICAL'
        self.status.feed = lambda: msg
        self.resize_status_line()

    def resize(self):
        self.main.multi_set(rely=self.rely + 1,
                            relx=self.relx,
                            max_height=self.max_height - 3,
                            max_width = self.max_width)
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
        self.resize_status_line()

    def resize_status_line(self):
        self.status_prefix.multi_set(rely=self.rely + self.height - 3,
                                     relx=self.relx,
                                     max_width=self.max_width,
                                     max_height=1)

        status_offset = len(self.status_prefix.value) + 1
        self.status.multi_set(rely=self.rely + self.height - 3,
                              relx=self.relx + status_offset,
                              max_width=self.max_width - status_offset,
                              max_height=1)


