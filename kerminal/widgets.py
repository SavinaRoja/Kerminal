# encoding: utf-8

import npyscreen2

import collections
import curses
import weakref


class TextCommandBox(npyscreen2.TextField):
    def __init__(self,
                 form,
                 parent,
                 history=True,
                 history_max=100,
                 toggle_val=curses.ascii.ESC,
                 *args,
                 **kwargs):

        self.history = history
        super(TextCommandBox, self).__init__(form,
                                             parent,
                                             *args,
                                             **kwargs)

        self.history = history
        self._history_store = collections.deque(maxlen=history_max)
        self._current_history_index = None
        self._current_command = ''

        self.toggle_val = toggle_val

    def set_up_handlers(self):
        super(TextCommandBox, self).set_up_handlers()
        self.handlers.update({curses.ascii.NL: self.h_execute_command,
                              curses.ascii.CR: self.h_execute_command,
                              })
        if self.history:
            self.handlers.update({"^P": self.h_get_previous_history,
                                  "^N": self.h_get_next_history,
                                  curses.KEY_UP: self.h_get_previous_history,
                                  curses.KEY_DOWN: self.h_get_next_history, })

    def h_get_previous_history(self, ch):
        if self._current_history_index is None:
            self._current_command = self.value
            _current_history_index = -1
        else:
            _current_history_index = self._current_history_index - 1
        try:
            self.value = self._history_store[_current_history_index]
        except IndexError:
            return True
        self.cursor_position = len(self.value)
        self._current_history_index = _current_history_index
        self.display()

    def h_get_next_history(self, ch):
        if self._current_history_index is None:
            return True
        elif self._current_history_index == -1:
            self.value = self._current_command
            self._current_history_index = False
            self.cursor_position = len(self.value)
            self.display()
            return True
        else:
            _current_history_index = self._current_history_index + 1
        try:
            self.value = self._history_store[_current_history_index]
        except IndexError:
            return True
        self.cursor_position = len(self.value)
        self._current_history_index = _current_history_index
        self.display()

    def h_execute_command(self, *args, **kwargs):
        if self.history:
            self._history_store.append(self.value)
            self._current_history_index = False
        self.form.action_controller.process_command_complete(self.value, weakref.proxy(self))
        self.value = ''
        self.cursor_position = 0

    def when_value_edited(self):
        super(TextCommandBox, self).when_value_edited()
        if not self.editing:
            self.form.action_controller.process_command_complete(self.value,
                                                                 weakref.proxy(self))

        self.command_active = False

    def toggle_command_active(self, *args, **kwargs):
        self.command_active = not self.command_active
        if self.command_active:
            self.value = ''
        else:
            self.value = 'Press TAB to enter commands'
            self.h_cursor_end()
        self.update()


class KerminalStatusText(npyscreen2.TextField):
    def when_feed_resets(self):
        #Returns itself to a standard view when the feed has completed
        self.form.status_prefix.value = 'STATUS:'
        self.form.status_prefix.color = 'DEFAULT'


class SemiInteractiveText(npyscreen2.TextField):

    def __init__(self,
                 form,
                 parent,
                 *args,
                 **kwargs):
        super(SemiInteractiveText, self).__init__(form,
                                                  parent,
                                                  show_cursor=False,
                                                  editable=True,
                                                  *args,
                                                  **kwargs)

    def set_up_handlers(self):
        """
        This function should be called somewhere during object initialisation
        (which all library-defined widgets do). You might like to override this
        in your own definition, but in most cases the `add_handlers` or
        `add_complex_handlers` methods are what you want.
        """
        self.handlers = {curses.ascii.NL: self.h_exit_down,
                         curses.ascii.CR: self.h_exit_down,
                         curses.ascii.TAB: self.h_exit_down,
                         #curses.KEY_BTAB: self.h_exit_up,
                         curses.KEY_DOWN: self.h_exit_down,
                         curses.KEY_UP: self.h_exit_up,
                         curses.KEY_LEFT: self.h_exit_left,
                         curses.KEY_RIGHT: self.h_exit_right,
                         "^P": self.h_exit_up,
                         "^N": self.h_exit_down,
                         curses.ascii.ESC: self.h_exit_escape,
                         #curses.KEY_MOUSE: self.h_exit_mouse,
                         }
        self.complex_handlers = []

    def pre_edit(self):
        self.highlight = True

    def post_edit(self):
        self.highlight = False

