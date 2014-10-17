# encoding: utf-8


from . import BaseContainer


class SmartContainer(BaseContainer):
    """
    The SmartContainer will have the ability to use various rectangle packing
    algorithms to dynamically arrange widgets (as they may be added or removed)
    and possibly minimize empty space.
    """

    def __init__(self,
                 screen,
                 scheme=None,
                 *args,
                 **kwargs):
        self.scheme = scheme
        super(SmartContainer, self).__init__(screen, *args, **kwargs)