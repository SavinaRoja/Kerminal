# encoding: utf-8

"""
"""

from . import BaseContainer


class GridContainer(BaseContainer):
    """
    The GridContainer will evenly divide its allocated space into a rectangular
    grid according to the number of rows and columns specified. This will result
    in (rows * columns) maximum positions to be filled by Widgets/Containers.
    """

    def __init__(self,
                 screen,
                 rows=3,
                 cols=4,
                 fill_rows_first=True,
                 diagnostic=False,
                 *args,
                 **kwargs):
        self.rows = rows
        self.cols = cols
        self.fill_rows_first = fill_rows_first
        self.diagnostic = diagnostic

        super(GridContainer, self).__init__(screen, *args, **kwargs)

        self.initiate_grid()

    #This is one approach to controlling whether addition of new widgets to a
    #container is allowed. One concern I have is whether it will be ideal or
    #sufficient in cases where one will want to determine validity of addition
    #based on the required/requested size of the new widget. AFAIK, the new
    #widget will need to be instantiated prior to calculating the size
    def add_widget(self, widget_class, widget_id=None, *args, **kwargs):
        if len(self.contained) >= self.rows * self.cols:
            return False
        widget = super(GridContainer, self).add_widget(widget_class,
                                                       widget_id=widget_id,
                                                       *args,
                                                       **kwargs)
        self.update_grid()
        return widget

    def remove_widget(self, widget=None, widget_id=None):
        super(GridContainer, self).remove_widget(widget=widget,
                                                 widget_id=widget_id)
        self.update_grid()

    def _resize(self):
        def apportion(start, stop, n):
            locs = []
            for i in range(n):
                locs.append(round(start + i * ((stop - start + 1) / n)))
            return locs

        #Define the start and stop locations
        rely_start = self.rely + self.top_margin
        rely_stop = self.rely + self.height - self.bottom_margin
        relx_start = self.relx + self.left_margin
        relx_stop = self.relx + self.width - self.right_margin

        relys = apportion(rely_start, rely_stop, self.rows)
        relxs = apportion(relx_start, relx_stop, self.cols)

        for col_n in range(self.cols):
            for row_n in range(self.rows):
                y, x = relys[row_n], relxs[col_n]
                #Set the grid coords matrix
                self.grid_coords[col_n][row_n] = [y, x]
                widget = self.grid[col_n][row_n]
                if widget is not None:
                    try:
                        height = relys[row_n + 1] - y
                    except IndexError:
                        height = self.space_available()[0] - y - 1
                    try:
                        width = relxs[col_n + 1] - x - 1
                    except IndexError:
                        width = self.space_available()[1] - x - 1
                    widget.rely, widget.relx = relys[row_n], relxs[col_n]
                    widget.max_height, widget.max_width = height, width

        #The old code for this, commented prior to later removal
        #Set rely along row slices
        #rely_start = self.rely + self.top_margin
        #rely_stop = self.rely + self.height - self.bottom_margin
        #relys = apportion(rely_start, rely_stop, self.rows)
        #for row_n, rely in enumerate(relys):
            #for cell in [col[row_n] for col in self.grid]:
                #if cell is not None:
                    #cell.rely = rely

        ##Set relx along col slices
        #relx_start = self.relx + self.left_margin
        #relx_stop = self.relx + self.width - self.right_margin
        #relxs = apportion(relx_start, relx_stop, self.cols)
        #for col_n, relx in enumerate(relxs):
            #for cell in self.grid[col_n]:
                #if cell is not None:
                    #cell.relx = relx
        #for each in self.contained:
            #each.resize()

    def initiate_grid(self):
        """
        Initiates the data structures for the grid and grid coordinates
        """

        self.grid = []
        self.grid_coords = []

        for i in range(self.cols):
            self.grid.append([None] * self.rows)
            self.grid_coords.append([[0, 0], ] * self.rows)

        self.update_grid()

    def update_grid(self):

        if self.fill_rows_first:
            flat_index = lambda i, j: i + j * self.cols
        else:
            flat_index = lambda i, j: i * self.rows + j

        for i in range(self.cols):
            for j in range(self.rows):
                try:
                    item = self.contained[flat_index(i, j)]
                except IndexError:
                    pass
                else:
                    self.grid[i][j] = item

    def update(self, clear=True):
        super(GridContainer, self).update(clear)

        for contained in self.contained:
            contained.update()

        if self.diagnostic:
            for col_n in range(self.cols):
                for row_n in range(self.rows):
                    y, x = self.grid_coords[col_n][row_n]
                    self.parent.curses_pad.addch(y, x, self.diagnostic)

