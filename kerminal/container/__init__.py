# encoding: utf-8

"""
"""

from npyscreen.wgwidget import Widget

import logging
import weakref


log = logging.getLogger('kerminal.container')


#Should certain style attributes cascade to the contained?


class BaseContainer(Widget):
    """
    The BaseContainer defines a basis for a system of Containers (or Layout
    Managers as some might call them).
    """
    def __init__(self,
                 screen,
                 margin=0,  # Applies to all sides unless they are specified
                 top_margin=None,
                 bottom_margin=None,
                 left_margin=None,
                 right_margin=None,
                 diagnostic=False,
                 *args,
                 **kwargs):

        self._max_height = 0
        self._max_width = 0
        self._height = 0
        self._width = 0

        super(BaseContainer, self).__init__(screen,
                                            *args,
                                            **kwargs)

        self.contained = []  # Holds Widgets and Containers
        self.contained_map = {}

        self.diagnostic = diagnostic

        self.margin = margin
        self.top_margin = top_margin
        self.bottom_margin = bottom_margin
        self.left_margin = left_margin
        self.right_margin = right_margin

    def add_widget(self, widget_class, widget_id=None, *args, **kwargs):
        """
        Add a Widget or Container (which is just another sort of Widget) to the
        Container. This will create an instance of `widget_class` along with
        specified args and kwargs.

        The created instance of `widget_class` will be added to `self.contained`
        and positioned on the screen per the Container's rules.

        If the optional `widget_id` keyword argument is used and provided a
        hashable value, then the widget instance will also be placed in the
        `self.contained_map` dictionary.
        """
        #Should consider scenarios where certain keyword arguments should be
        #inherited from the parent Container unless overridden. I suppose this
        #was the impetus for _passon in some npyscreen library classes

        #num_contained = len(self.contained)
        widget = widget_class(self.parent,
                              relx=self.relx + self.left_margin,
                              rely=self.rely + self.top_margin,
                              *args,
                              **kwargs)
        self.contained.append(widget)

        #I considered putting this in a try statement to catch TypeError on
        #unhashable values of widget_id, but I think it's better to choke on it
        if widget_id is not None:
            self.contained_map[widget_id] = widget

        widget_proxy = weakref.proxy(widget)
        return widget_proxy

    def remove_widget(self, widget=None, widget_id=None):
        """
        `remove_widget` can be used in two ways: the first is to pass in a
        reference to the widget intended to be removed, the second is to pass in
        it's id (registered in `self.contained_map`).

        This method will return True if the widget was found and successfully
        removed, False otherwise. This method will automatically call
        `self.resize` upon a successful removal.
        """
        if widget is None and widget_id is None:
            raise TypeError('remove_widget requires at least one argument')

        #By ID
        if widget_id is not None:
            if widget_id not in self.contained_map:
                return False
            widget = self.contained_map[widget_id]
            self.contained.remove(widget)
            del self.contained_map[widget_id]
            self.resize()
            return True

        #By widget reference
        try:
            self.contained.remove(widget)
        except ValueError:  # Widget not a member in this container
            return False
        else:
            #Looking for values in a dict is weird, but seems necessary
            map_key = None
            for key, val in self.contained_map.items():
                if val == widget:
                    map_key = key
                    break
            if map_key is not None:
                del self.contained_map[map_key]
            self.resize()
            return True

    def resize(self):
        """
        It is taken as a general contract that when a Container is resized then
        it should in turn resize everything it contains whether it is another
        Container or a Widget. Since Containers are in fact a special type of
        Widget, this is not so strange. As such, this base definition of
        `resize` calls the `resize` method of all items in `self.contained`.

        For subclassing Containers, it is advised that this method is left
        unmodified and that the specifics of resizing for that Container be
        placed in `_resize`.
        """
        self._resize()
        for widget in self.contained:
            widget.resize()

    def _resize(self):
        """
        It is the job of `_resize` to appropriately modify the `rely` and `relx`
        attributes of each item in `self.contained`. It should also modify the
        `max_height` and `max_width` attributes as appropriate. Rarely, if ever,
        should this method directly set the `height` and `width` attributes of
        its contained Widgets and Containers directly.

        This is the method you should probably be modifying if you are making a
        new Container subclass.

        As this method should generally be encapsulated by `resize`, it should
        not be necessary to call the `resize` method of the items in
        `self.contained`.
        """
        pass

    def feed(self):
        """
        A Container does not have a meaningful value, so a feed method for a
        Container does not behave like a feed method for a LiveWidget. Instead,
        the feed method of a container must call the feed methods for each
        contained Widget or Container that has a feed method.
        """
        for widget in self.contained:
            if hasattr(widget, 'feed'):
                widget.feed()

    def update(self, clear=True):
        for contained in self.contained:
            contained.update()

        if self.diagnostic:
            for col_n in range(self.cols):
                for row_n in range(self.rows):
                    y, x = self.grid_coords[col_n][row_n]
                    self.parent.curses_pad.addch(y, x, self.diagnostic)

    #These protocols for max_height and max_width should ideally be a part of
    #the base Widget definition
    @property
    def max_height(self):
        return self._max_height

    @max_height.setter
    def max_height(self, val):
        """
        max_height should never be allowed to extend past the available screen
        area.
        """
        max_h = self.parent.curses_pad.getmaxyx()[0] - self.rely - 1
        if val > max_h:
            val = max_h
        self._max_height = val
        #if self.height > self._max_height:
            #self.height = self._max_height

    @property
    def max_width(self):
        return self._max_width

    @max_width.setter
    def max_width(self, val):
        """
        max_width should never be allowed to extend past the available screen
        area.
        """
        max_w = self.parent.curses_pad.getmaxyx()[1] - self.relx -1
        if val > max_w:
            val = max_w
        self._max_width = val
        #if self._max_width > self.width:
            #self.width = self._max_width

    @property
    def height(self):
        """
        Returns the smallest of [self._height, self._max_height].
        """
        if self._height > self.max_height:
            return self.max_height
        else:
            return self._height

    @height.setter
    def height(self, val):
        if val > self._max_height:
            val = self._max_height
        self._height = val

    @property
    def width(self):
        """
        Returns the smallest of [self._width, self._max_width]
        """
        if self._width > self.max_width:
            return self.max_width
        else:
            return self._width

    @width.setter
    def width(self, val):
        if val > self._max_width:
            val = self._max_width
            self._width = val

    @property
    def margin(self):
        return self._margin

    @margin.setter
    def margin(self, val):
        self._margin = val

    @property
    def top_margin(self):
        #None indicates unset
        if self. _top_margin is None:
            return self.margin
        return self._top_margin

    @top_margin.setter
    def top_margin(self, val):
        self._top_margin = val

    @property
    def bottom_margin(self):
        #None indicates unset
        if self. _bottom_margin is None:
            return self.margin
        return self._bottom_margin

    @bottom_margin.setter
    def bottom_margin(self, val):
        self._bottom_margin = val

    @property
    def left_margin(self):
        #None indicates unset
        if self. _left_margin is None:
            return self.margin
        return self._left_margin

    @left_margin.setter
    def left_margin(self, val):
        self._left_margin = val

    @property
    def right_margin(self):
        #None indicates unset
        if self. _right_margin is None:
            return self.margin
        return self._right_margin

    @right_margin.setter
    def right_margin(self, val):
        self._right_margin = val
