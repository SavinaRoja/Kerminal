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
        self.height = self.max_height
        self.width = self.max_width

        #self.rearrange_widgets()

        #The SmartContainer only sets the max_width and max_height of the
        #contained items according to its own maximums (less margins). As a
        #result of this and its management by height/width attrs, some thought
        #should be given to how contained items expand
        for widget in self.contained:
            widget.max_width = self.max_width -\
                               (self.left_margin + self.right_margin)
            widget.max_height = self.max_height -\
                               (self.top_margin + self.bottom_margin)

        self.rearrange_widgets()

    def rearrange_widgets(self):
        self.scheme_map[self.scheme]()

    def ffdh_top(self):
        #Re-ordering self.contained by descending height
        self.contained.sort(key=lambda widget: widget.height, reverse=True)

        start_y = self.rely + self.top_margin
        end_y = self.rely + self.height - self.bottom_margin
        start_x = self.relx + self.left_margin
        end_x = self.relx + self.width - self.right_margin
        width = end_x - start_x

        levels = [start_y]
        level_x = {start_y: 0}

        for widget in self.contained:
            for level in levels:
                if level + widget.height >= end_y:
                    widget.hidden = True
                    widget.relx = self.relx
                    widget.rely = self.rely
                    break
                widget.hidden = False
                x_cur = level_x[level]
                if widget.width <= width - x_cur:
                    widget.rely = level
                    widget.relx = x_cur + start_x
                    if x_cur == 0:
                        new_level = level + widget.height
                        levels.append(new_level)
                        level_x[new_level] = 0
                    level_x[level] += widget.width
                    break

    def ffdh_bottom(self):
        #Re-ordering self.contained by descending height
        self.contained.sort(key=lambda widget: widget.height, reverse=True)

        start_y = self.rely + self.height - self.bottom_margin
        end_y = self.rely + self.top_margin
        start_x = self.relx + self.left_margin
        end_x = self.relx + self.width - self.right_margin
        width = end_x - start_x

        levels = [start_y]
        level_x = {start_y: 0}

        for widget in self.contained:
            for level in levels:
                if level - widget.height <= end_y:
                    widget.hidden = True
                    widget.relx = self.relx
                    widget.rely = self.rely
                    break
                widget.hidden = False
                x_cur = level_x[level]
                if widget.width <= width - x_cur:
                    widget.rely = level - widget.height
                    widget.relx = x_cur + start_x
                    if x_cur == 0:
                        new_level = level - widget.height
                        levels.append(new_level)
                        level_x[new_level] = 0
                    level_x[level] += widget.width
                    break

    @property
    def scheme(self):
        return self._scheme

    @scheme.setter
    def scheme(self, val):
        if val.lower() in self.scheme_map.keys():
            self._scheme = val
        else:
            raise ValueError('{0} not in {1}'.format(val,
                                                     self.scheme_map.keys()))

    def calculate_area_needed(self):
        return 0, 0
