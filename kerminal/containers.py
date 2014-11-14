# encoding: utf-8

import npyscreen2
from .widgets import SemiInteractiveText

import curses


class EscapeForwardingContainer(npyscreen2.Container):
    def set_up_exit_condition_handlers(self):
        super(EscapeForwardingContainer, self).set_up_exit_condition_handlers()
        self.how_exited_handlers.update({'escape': self.h_exit_escape})


class EscapeForwardingSmartContainer(EscapeForwardingContainer,
                                     npyscreen2.SmartContainer):
    pass


class EscapeForwardingGridContainer(EscapeForwardingContainer,
                                    npyscreen2.GridContainer):
    pass


#MultiLine widgets are likely to be built into npyscreen2 in the future, for now
#I am experimenting with them here
class KerminalMultiLineText(EscapeForwardingContainer, npyscreen2.Container):

    #def create(self):
        #self.above_indicator = self.add(npyscreen2.TextField,
                                        #editable=False,
                                        #auto_manage=False,
                                        #color='CONTROL',
                                        #value=' -- more -- ',
                                        #hidden=True)
        #self.below_indicator = self.add(npyscreen2.TextField,
                                        #editable=False,
                                        #auto_manage=False,
                                        #color='CONTROL',
                                        #value=' -- more -- ',
                                        #hidden=True)

    def resize(self):
        cur_y = self.rely + self.top_margin - self.show_from_y

        for i, widget in enumerate(self.autoables):
            widget.rely = cur_y + i
            widget.relx = self.relx + self.left_margin

    def build_contained_from_text(self, text, overwrite=True):
        if overwrite:
            self.contained = [w for w in self.contained if not w.auto_manage]
        for line in text.splitlines():
            self.add(SemiInteractiveText,
                     value=line.strip())

    def set_up_handlers(self):
        super(EscapeForwardingContainer, self).set_up_handlers()
        self.handlers.update({curses.KEY_NPAGE: self.h_scroll_page_down,
                              curses.KEY_PPAGE: self.h_scroll_page_up})

    def h_scroll_page_down(self, inpt=None):
        #Breaks the edit_loop of the current text field
        self.contained[self.edit_index].editing = False

        effective_page = self.height - (self.top_margin + self.bottom_margin)
        self.edit_index += effective_page

        #Avoid runoff
        if self.edit_index > len(self.contained):
            self.edit_index = len(self.contained) - 1

        #If the selected widget is not an autoable, move forward up to end
        if not self.contained[self.edit_index].auto_manage:
            for i, widget in enumerate(self.contained[self.edit_index + 1:]):
                if widget.auto_manage:
                    self.edit_index += i + 1
                    break

        #If the following is True, then the previous has failed and for whatever
        #reason, we were already passed the last autoable to begin with
        #So we'll just pick the last autoable
        if not self.contained[self.edit_index].auto_manage:
            self.edit_index = self.contained.index(self.autoables[-1])

    def h_scroll_page_up(self, inpt=None):
        self.contained[self.edit_index].editing = False

        effective_page = self.height - (self.top_margin + self.bottom_margin)
        self.edit_index -= effective_page

        #Avoid runoff
        if self.edit_index < 0:
            self.edit_index = 0

        #If the selected widget is not an autoable, move backwards up to begin
        if not self.contained[self.edit_index].auto_manage:
            for i, widget in enumerate(self.contained[:self.edit_index: -1]):
                if widget.auto_manage:
                    self.edit_index -= i + 1
                    break

        #If the following is True, then the previous has failed and for whatever
        #reason, we were already passed the first autoable to begin with
        #So we'll just pick the first autoable
        if not self.contained[self.edit_index].auto_manage:
            self.edit_index = self.contained.index(self.autoables[0])
