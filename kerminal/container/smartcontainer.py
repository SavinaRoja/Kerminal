# encoding: utf-8


from . import BaseContainer


class SmartContainer(BaseContainer):
    """
    The SmartContainer will have the ability to use various rectangle packing
    algorithms to dynamically arrange widgets (as they may be added or removed)
    and possibly minimize empty space.

    The scheme attribute controls which packing algorithm the SmartContainer
    will use.

    The following schemes are available:
        ffdh-top  :  First-Fit Decreasing Height (from the top)
        ffdh-bottom  :  First-Fit Decreasing Height (from the bottom)

    As a general rule, this Container treats the sizes of the contained widgets
    as static (or independent) and does not control or adjust their sizes. It
    will do its best to arrange their locations so that they fit on the screen
    without changing the dimensions.
    """

    def __init__(self,
                 screen,
                 scheme='ffdh-top',
                 *args,
                 **kwargs):

        self.scheme_map = {'ffdh-top': self.ffdh_top,
                           'ffdh-bottom': self.ffdh_bottom,
                           }
        self.scheme = scheme

        super(SmartContainer, self).__init__(screen, *args, **kwargs)

    def add_widget(self, widget_class, widget_id=None, *args, **kwargs):
        w = super(SmartContainer, self).add_widget(widget_class,
                                                   widget_id=widget_id,
                                                   *args,
                                                   **kwargs)
        self._resize()
        return w

    def _resize(self):
        self.scheme_map[self.scheme]()

    def ffdh_top(self):
        #Re-ordering self.contained by descending height
        self.contained.sort(key=lambda widget: widget.height, reverse=True)

        levels = [self.rely]
        level_x = {self.rely: 0}

        for widget in self.contained:
            for level in levels:
                if level >= self.height:
                    widget.hidden = True  # this aint what I think it is
                    break
                x_cur = level_x[level]
                if widget.width <= self.width - x_cur:
                    widget.rely = level
                    widget.relx = x_cur
                    if x_cur == 0:
                        new_level = level + widget.height
                        levels.append(new_level)
                        level_x[new_level] = 0
                    level_x[level] += widget.width
                    break

    def ffdh_bottom(self):
        #Re-ordering self.contained by descending height
        self.contained.sort(key=lambda widget: widget.height, reverse=True)

        levels = [self.rely + self.height]
        level_x = {self.rely + self.height: 0}

        for widget in self.contained:
            for level in levels:
                if level <= self.rely:
                    widget.hidden = True  # this aint what I think it is
                    break
                x_cur = level_x[level]
                if widget.width <= self.width - x_cur:
                    widget.rely = level - widget.height
                    widget.relx = x_cur
                    if x_cur == 0:
                        new_level = level - widget.height
                        levels.append(new_level)
                        level_x[new_level] = 0
                    level_x[level] += widget.width
                    break


    #def update(self, clear=True):
        #super(SmartContainer, self).update(clear)

        #for contained in self.contained:
            #contained.update()

        #if self.diagnostic:
            #for col_n in range(self.cols):
                #for row_n in range(self.rows):
                    #y, x = self.grid_coords[col_n][row_n]
                    #self.parent.curses_pad.addch(y, x, self.diagnostic)

    @property
    def scheme(self):
        return self._scheme

    @scheme.setter
    def scheme(self, val):
        if val.lower() in self.scheme_map.keys():
            self._scheme = val
        else:
            pass