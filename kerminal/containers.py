# encoding: utf-8

import npyscreen2


class EscapeForwardingContainer(npyscreen2.Container):
    def set_up_exit_condition_handlers(self):
        super(EscapeForwardingContainer, self).set_up_exit_condition_handlers()
        self.how_exited_handlers.update({'escape': self.h_exit_escape})


class EscapeForwardingSmartContainer(EscapeForwardingContainer,
                                     npyscreen2.SmartContainer):
    pass