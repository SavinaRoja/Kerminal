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
                 rows=6,
                 cols=4,
                 fill_rows_first=True,
                 *args,
                 **kwargs):

        super(GridContainer, self).__init__(screen, *args, **kwargs)

        self.rows = rows
        self.cols = cols
        self.fill_rows_first = fill_rows_first

        self.initiate_grid()

    def add_widget(self, widget_class, widget_id=None, *args, **kwargs):
        #prevent the addition of more widgets than the grid can hold
        if len(self.contained) >= self.rows * self.cols:
            return False

        #Instantiate the widget with current position and dimensions
        col, row = self.convert_flat_index_to_grid(len(self.contained))
        rely, relx = self.grid_coords[col][row]
        max_height, max_width = self.grid_dim_hw[col][row]

        widget = super(GridContainer, self).add_widget(widget_class,
                                                       widget_id=widget_id,
                                                       rely=rely,
                                                       relx=relx,
                                                       max_height=max_height,
                                                       max_width=max_width,
                                                       #height=6,
                                                       #width=26,
                                                       *args,
                                                       **kwargs)
        self.update_grid()
        return widget

    def remove_widget(self, widget=None, widget_id=None):
        super(GridContainer, self).remove_widget(widget=widget,
                                                 widget_id=widget_id)
        self.update_grid()

    def get_next_yx(self):
        """
        Returns the y-x coordinates of the next available Widget/Container slot.
        """
        col, row = self.convert_flat_index_to_grid(len(self.contained))
        return self.grid_coords[col][row]

    def convert_flat_index_to_grid(self, index):
        if self.fill_rows_first:
            row = index // self.cols
            col = index % self.cols
        else:
            row = index % self.cols
            col = index // self.cols
        return col, row

    def convert_grid_indices_to_flat(self, col_index, row_index):
        if self.fill_rows_first:
            return col_index + row_index * self.cols
        else:
            return col_index * self.rows + row_index

    def _resize(self):
        #GridContainer expands to fill its entire allocated space
        self.height = self.max_height
        self.width = self.max_width

        self.resize_grid_coords()

        #GridContainer sets rely-relx and sets max height and width
        for index, widget in enumerate(self.contained):
            col, row = self.convert_flat_index_to_grid(index)
            widget.rely, widget.relx = self.grid_coords[col][row]
            widget.max_height, widget.max_width = self.grid_dim_hw[col][row]

    def initiate_grid(self):
        """
        Initiates the data structures for the grid and grid coordinates
        """

        self.grid = []
        self.grid_coords = []
        self.grid_dim_hw = []

        for i in range(self.cols):
            self.grid.append([None] * self.rows)
            self.grid_coords.append([[0, 0], ] * self.rows)
            self.grid_dim_hw.append([[0, 0], ] * self.rows)

        self.update_grid()

    def resize_grid_coords(self):
        def apportion(start, stop, n):
            locs = []
            cell_size = (stop - start + 1) / n
            for i in range(n):
                locs.append(start + round(i * cell_size))
            return locs

        #Define the start and stop locations
        rely_start = self.rely + self.top_margin
        rely_stop = self.rely + self.height - self.bottom_margin
        relx_start = self.relx + self.left_margin
        relx_stop = self.relx + self.width - self.right_margin

        relys = apportion(rely_start, rely_stop, self.rows)
        relxs = apportion(relx_start, relx_stop, self.cols)

        for col in range(self.cols):
            for row in range(self.rows):
                y, x = relys[row], relxs[col]
                #Set the grid coords matrix
                self.grid_coords[col][row] = [y, x]

        for col in range(self.cols):
            for row in range(self.rows):
                if row == (self.rows - 1):  # Last row
                    height = (self.rely + self.max_height) -\
                             (self.grid_coords[col][row][0] + self.bottom_margin)
                else:
                    height = self.grid_coords[col][row + 1][0] - self.grid_coords[col][row][0]

                if col == (self.cols - 1):  # Final column
                    width = (self.relx + self.max_width) -\
                            (self.grid_coords[col][row][1] + self.right_margin)
                else:
                    width = self.grid_coords[col + 1][row][1] - self.grid_coords[col][row][1]

                self.grid_dim_hw[col][row] = [height, width]

    def update_grid(self):
        #This puts the contained items into a grid for col-row accession
        for i in range(self.cols):
            for j in range(self.rows):
                flat_index = self.convert_grid_indices_to_flat(i, j)
                try:
                    item = self.contained[flat_index]
                except IndexError:
                    pass
                else:
                    self.grid[i][j] = item
