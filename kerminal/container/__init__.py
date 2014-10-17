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
                 margin=0,  # Margin to be applied on all sides
                 top_margin=0,  # Additional margin to be applied on top
                 bottom_margin=0,  # Additional margin to be applied on bottom
                 left_margin=0,  # Additional margin to be applied on left
                 right_margin=0,  # Additional margin to be applied on right
                 *args,
                 **kwargs):

        self.contained = []  # Holds Widgets and Containers
        self.contained_map = {}

        #Margins: each side summed with general margin
        self.margin = margin
        self.top_margin = top_margin + self.margin
        self.bottom_margin = bottom_margin + self.margin
        self.left_margin = left_margin + self.margin
        self.right_margin = right_margin + self.margin

        super(BaseContainer, self).__init__(screen,
                                            *args,
                                            **kwargs)

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

        num_contained = len(self.contained)
        widget = widget_class(self.parent,
                              relx=self.relx + 2,
                              rely=num_contained + 1,
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
        attributes of each item in `self.contained`.

        This is the method you should probably be modifying if you are making a
        new Container subclass.

        As this method should generally be encapsulated by `resize`, it should
        not be necessary to call the `resize` method of the items in
        `self.contained`.
        """
        pass
