

import pygame
from .utilities import paint_lock
from .layer import Layer


class RowOrCol:

    def __init__(self, grid, index):

        assert isinstance(grid, GridLayer)
        assert isinstance(index, int) and index >= 0

        self._grid = grid
        self._grid_layer = grid._layer
        self._grid_data = grid._data  # shared ressource
        self._index = index

    def __contains__(self, item):

        for widget in self.ichildren:
            if widget is item:
                return True
        return False

    def __len__(self):

        length = 0
        for _ in self.ichildren:
            length += 1
        return length

    children = property(lambda self: tuple(widget for widget in self if widget is not None))
    ichildren = property(lambda self: (widget for widget in self if widget is not None))
    is_first = property(lambda self: self._index == 0)

    def is_empty(self):

        for _ in self.ichildren:
            return False
        return True


class Column(RowOrCol):
    """
    A Column can be seen as a list of cells with the same 'col' value.
    It is the manager of GridLayer.cols and can read GridLayer.data
    """

    def __init__(self, grid, index):

        RowOrCol.__init__(self, grid, index)

        self._width = grid.col_width
        if self.is_first:
            self._left = grid.padding.left
        else:
            self._left = self.get_previous_col().right + grid.children_margins.left

        grid._cols.append(self)

    def __iter__(self):

        for data_row in self._grid_data:
            yield data_row[self._index]

    def __getitem__(self, row):
        """
        Return the value of the cell in this col, indexed by 'col'
        """
        return self._grid_data[row][self._index]

    is_adaptable = property(lambda self: self._width is None)
    is_last = property(lambda self: self._index == len(self._grid.cols) - 1)
    left = property(lambda self: self._left)
    right = property(lambda self: self._left + self.get_width())

    def _update_width(self):
        """
        Adapt the col width to the required width
        Needed when, in an adaptative column, a widget is added, resized or removed
        NOTE : this is a heavy function, try to call it when you are sure it will change something
        """

        for widget in self.ichildren:
            self._grid._update_widget(widget)

        if not self.is_last:
            self.get_next_col()._update_left(self.left + self.get_width() + self._grid.children_margins.left)

    def _update_left(self, left):

        dx = left - self.left
        if dx == 0:
            return
        self._left = left
        for widget in self.ichildren:
            self._grid._update_widget(widget)

        if not self.is_last:
            self.get_next_col()._update_left(left + self.get_width() + self._grid.children_margins.left)

    def get_cell_rect(self, row):
        """
        Return the cell's position and size inside a tuple object
        """
        return self.left, self._grid.get_row(row).top, self.get_width(), self._grid.get_row(row).get_height()

    def get_next_col(self):

        if self.is_last:
            return
        return self._grid.get_col(self._index + 1)

    def get_previous_col(self):
        """
        Return the col above self
        """
        if self.is_first:
            return None
        return self._grid.get_col(self._index - 1)

    def get_width(self):

        if self._width is not None:
            return self._width

        if self.is_empty():
            return 0

        return max(widget.rect.w for widget in self if widget is not None)

    def set_width(self, width):
        """
        Set the col's width
        If width is None, the col will adapt to its widest widget
        """
        assert (width is None) or isinstance(width, (int, float)) and width >= 0
        if not self._grid.cols_are_adaptable:
            raise PermissionError("This grid has a fixed col_width : {}".format(self._grid.col_width))
        self._width = width
        self._update_width()


class Row(RowOrCol):
    """
    A Row can be seen as a list of cells with the same 'row' value.
    It is the manager of GridLayer.rows and can read GridLayer.data
    """
    def __init__(self, grid, index):

        RowOrCol.__init__(self, grid, index)

        self._height = grid.row_height
        if self.is_first:
            self._top = grid.padding.top
        else:
            self._top = self.get_previous_row().bottom + grid.children_margins.top

        grid._rows.append(self)

    def __contains__(self, item):

        return self._grid_data[self._index].__contains__(item)

    def __getitem__(self, col):
        """
        Return the value of the cell in this row, indexed by 'col'
        """
        return self._grid_data[self._index][col]

    def __iter__(self):

        return self._grid_data[self._index].__iter__()

    bottom = property(lambda self: self.top + self.get_height())
    is_adaptable = property(lambda self: self._height is None)
    is_last = property(lambda self: self._index == len(self._grid.rows)-1)
    top = property(lambda self: self._top)

    def _update_height(self):
        """
        Adapt the row height to the required height
        """

        for widget in self.ichildren:
            self._grid._update_widget(widget)

        if not self.is_last:
            self.get_next_row()._update_top(self.top + self.get_height() + self._grid.children_margins.top)

        # if not self.is_last:
        #     self.get_next_row()._update_top(top + h + self._grid.children_margins.top)

    def _update_top(self, top):

        dy = top - self.top
        if dy == 0:
            return
        self._top = top
        for widget in self.ichildren:
            self._grid._update_widget(widget)

        if not self.is_last:
            self.get_next_row()._update_top(top + self.get_height() + self._grid.children_margins.top)

    def get_cell_rect(self, col):
        """
        Return the cell's position and size inside a tuple object
        """
        return self._grid.get_col(col).left, self.top, self._grid.get_col(col).get_width(), self.get_height()

    def get_height(self):

        if self._height is not None:
            return self._height

        if self.is_empty():
            return 0

        return max(widget.rect.h for widget in self if widget is not None)

    def get_next_row(self):

        if self.is_last:
            return
        return self._grid.get_row(self._index+1)

    def get_previous_row(self):
        """
        Return the row above self
        """
        if self.is_first:
            return None
        return self._grid.get_row(self._index-1)

    def set_height(self, height):
        """
        Set the row's height
        If height is None, the row will adapt to its hightest widget
        """
        assert (height is None) or isinstance(height, (int, float)) and height >= 0
        if not self._grid.rows_are_adaptable:
            raise PermissionError("This grid has a fixed row_height : {}".format(self._grid.row_height))
        self._height = height
        self._update_height()


class GridLayer(Layer):
    """
    A GridLayer is a Layer who places its children itself, depending on their
    attributes 'row' and 'col'

    If nbrows is None, adding a widget will create missing rows if needed
    nbcols works the same

    A GridLayer dimension (row or column) have two implicit modes : adaptable and fixed
    If the dimension size (col_width or row_height) is set, the mode is fixed. Else,
    it is adaptable.
    Fixed means all cell have the same dimension size
    Adaptable means cells receive their dimension size from the largest cell in the
    dimension.
    Note that for one dimension, you can reset its size. It means yous can, in the
    same grid, have an adaptable row above a fixed row, as below :

    gl = GridLayer(some_parent, cols=None, rows=5, col_width=None, row_height=25)
    grid = gl.grid
                                       # All rows have the fixed mode
    grid.get_row(3).set_height(None)   # This row gets the adaptable mode
    grid.get_row(4).set_height(45)     # This row gets the fixed mode

    Two widgets can't fit in the same cell

    WARNING : manipulating a grid with multi-threading might cause issues
    """

    def __init__(self, *args, nbcols=None, nbrows=None, col_width=None, row_height=None, **kwargs):

        Layer.__init__(self, *args, **kwargs)

        if nbcols is not None:
            assert isinstance(nbcols, int) and nbcols > 0
        if nbrows is not None:
            assert isinstance(nbrows, int) and nbrows > 0

        self._layer = self
        self._nbcols = None
        self._nbrows = None
        self._col_width = col_width
        self._row_height = row_height

        self._data = [[None]]  # shared ressource initialized with one row and one column
        self._cols = []
        self._rows = []

        Row(self, 0)
        Column(self, 0)
        if nbcols:
            self.set_nbcols(nbcols)
        if nbrows:
            self.set_nbrows(nbrows)

    def __str__(self):
        return "{}(nbrows={}, nbcols={})".format(self.__class__.__name__, self.nbrows, self.nbcols)

    col_width = property(lambda self: self._col_width)
    cols = property(lambda self: self._cols)
    cols_are_adaptable = property(lambda self: self._col_width is None)
    nbcols = property(lambda self: self._nbcols if self._nbcols is not None else len(self._data[0]))
    nbrows = property(lambda self: self._nbrows if self._nbrows is not None else len(self._data))
    row_height = property(lambda self: self._row_height)
    rows = property(lambda self: self._rows)
    rows_are_adaptable = property(lambda self: self._row_height is None)

    def _update_widget(self, widget):
        """Updates window & position"""
        cell_rect = self.get_cell_rect(widget.row, widget.col)
        widget.resize(*cell_rect[2:])  # TODO : resize(size) ?
        # TODO : use size_hint
        # widget.set_window(cell_rect, follow_movements=False)
        widget.set_lock(origin=False)
        if widget.origin.location is not None:
            widget.origin.config(pos=getattr(pygame.Rect(cell_rect), widget.origin.location),
                                 loc=widget.origin.location)
        else:
            widget.origin.config(pos=cell_rect[:2])
        widget.set_lock(origin=True)

    def _update_size(self):

        with paint_lock:
            for row in self.rows:
                row._update_height()
            for col in self.cols:
                col._update_width()

    def accept(self, widget):
        """You must define at least the row or the column in order to insert a widget in a grid layer"""
        if (widget.col is None) or (widget.row is None):
            return False
        return super().accept(widget)

    def add(self, widget):

        if widget.origin.reference is not self.container:
            raise PermissionError("Cannot use other ref than parent in a GridLayer")
        if widget.origin.reference_location != "topleft":
            raise PermissionError("Cannot use other refloc than 'topleft' in a GridLayer")
        if (widget.col is None) or (widget.row is None):
            raise PermissionError(
                "You must define at least the row or the column in order to insert a widget in a GridLayer")
        try:
            super().add(widget)
            if self._nbcols is None and len(self.cols) - 1 < widget.col:
                self.set_nbcols(widget.col + 1)
                self._nbcols = None
            if self._nbrows is None and len(self.rows) - 1 < widget.row:
                self.set_nbrows(widget.row + 1)
                self._nbrows = None

            if self._data[widget.row][widget.col] is not None:
                raise PermissionError("Cannot insert {} at positon : row={}, col={}, because {} is already there"
                                      "".format(widget, widget.row, widget.col, self._data[widget.row][widget.col]))

            row = self.rows[widget.row]
            col = self.cols[widget.col]
            new_h = row.is_adaptable and widget.rect.height > row.get_height()
            new_w = col.is_adaptable and widget.rect.width > col.get_width()
            self._data[widget.row][widget.col] = widget
            if new_h:
                row._update_height()
            if new_w:
                col._update_width()

            if new_h or new_w or len(row) == 1 or len(col) == 1:
                self.pack()
            else:
                self._update_widget(widget)

            # don't need owner because, if the grid is killed,
            # it means the container is killed, so the widget is also killed
            widget.signal.RESIZE.connect(self._update_size, owner=self)
            widget.signal.KILL.connect(self._update_size, owner=self)

        except Exception as e:
            raise e

    def move(self, widget, col, row):  # TODO : invert col & row

        assert widget in self
        if self._data[row][col] is not None:
            if self._data[row][col] is widget:
                return
            raise PermissionError("This cell is already occupied by : " + str(self._data[row][col]))

        self._data[widget.row][widget.col] = None
        self._data[row][col] = widget
        widget._col = col
        widget._row = row
        if self.rows_are_adaptable or self.cols_are_adaptable:
            self.pack()
        else:
            self._update_widget(widget)

    def remove(self, widget):

        super().remove(widget)
        assert self._data[widget.row][widget.col] is widget

        col = self.get_col(widget.col)
        row = self.get_row(widget.row)
        old_col_width, old_row_height = None, None  # warning shut down
        if col.is_adaptable:
            old_col_width = col.get_width()
        if row.is_adaptable:
            old_row_height = row.get_height()

        widget.signal.RESIZE.disconnect(self._update_size)
        widget.signal.KILL.disconnect(self._update_size)
        self._data[widget.row][widget.col] = None

        if col.is_adaptable and (old_col_width != col.get_width()):
            col._update_width()
        if row.is_adaptable and (old_row_height != row.get_height()):
            row._update_height()

    def get_cell_rect(self, row, col):

        return self.get_col(col).get_cell_rect(row)

    def get_data(self, row, col):

        return self._data[row][col]

    def get_col(self, col_index):
        """
        Return the column from index
        """
        return self._cols[col_index]

    def get_row(self, row_index):
        """
        Return the row from index
        """
        return self._rows[row_index]

    def pack(self, start_pos=(0, 0), **kwargs):
        """
        Updates from children_margins, not col.width & row.height
        """
        if kwargs:
            raise PermissionError("GridLayer.pack() only supports 'start_pos' parameters")

        with paint_lock:

            for col in self._cols:
                if col.is_first:
                    col._left = self.padding.left + start_pos[0]
                else:
                    col._left = col.get_previous_col().right + self.children_margins.left

            for row in self._rows:
                if row.is_first:
                    row._top = self.padding.top + start_pos[1]
                else:
                    row._top = row.get_previous_row().bottom + self.children_margins.top

                for widget in row.ichildren:
                    self._update_widget(widget)

    def set_col_width(self, width):

        assert (width is None) or isinstance(width, (int, float)) and width >= 0

        self._col_width = None
        for col in self.cols:
            col.set_width(width)
        self._col_width = width

    def set_nbcols(self, nbcols):
        """
        Set the number of columns
        If nbcols is None, adding a widget will create missing columns if needed
        """
        assert isinstance(nbcols, int) and nbcols > 0, nbcols
        if nbcols is not None:
            nbnew = nbcols - self.nbcols
            if nbnew < 0:
                raise PermissionError("Cannot reduce nbcols")
            elif nbnew > 0:
                # Create new columns
                for row in self._data:
                    row += [None] * nbnew
                for i in range(nbnew):
                    Column(self, i + nbcols - nbnew)
        self._nbcols = nbcols

    def set_nbrows(self, nbrows):
        """
        Set the number of rows
        If nbrows is None, adding a widget will create missing rows if needed
        """
        assert isinstance(nbrows, int) and nbrows > 0
        if nbrows is not None:
            nbnew = nbrows - self.nbrows
            if nbrows < 0:
                raise PermissionError("Cannot reduce nbrows")
            elif nbnew > 0:
                # Create new rows
                for i in range(self.nbrows, nbrows):
                    self._data += [[None] * self.nbcols]
                    Row(self, i)
        self._nbrows = nbrows

    def set_row_height(self, height):

        assert (height is None) or isinstance(height, (int, float)) and height >= 0

        self._row_height = None
        for row in self.rows:
            row.set_height(height)
        self._row_height = height

    def swap(self, widget1, widget2):

        assert widget1 in self
        assert widget2 in self

        widget1.set_lock(origin=False)
        widget2.set_lock(origin=False)

        self._data[widget1.row][widget1.col] = widget2
        self._data[widget2.row][widget2.col] = widget1

        widget1._col, widget1._row, widget2._col, widget2._row = widget2._col, widget2._row, widget1._col, widget1._row

        if self.rows_are_adaptable or self.cols_are_adaptable:
            self.pack()
        else:
            self._update_widget(widget1)
            self._update_widget(widget2)
