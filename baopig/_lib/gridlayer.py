

import threading
import pygame
from baopig.pybao.objectutilities import TypedList
from .widget import debug_with_assert
from .layer import Layer


# TODO : many widgets in one cell ?


class Cell:

    def __init__(self, grid, row_index, col_index):

        self._grid = grid
        self._col_index = col_index
        self._row_index = row_index

    col = property(lambda self: self._grid.get_col(self._col_index))
    row = property(lambda self: self._grid.get_row(self._row_index))

    def get_data(self):
        """
        Return a cell's content
        None, a Widget or a list of components (if implemented, but not yet)
        """
        with self._grid._lock:
            return self._grid._data[self._row_index][self._col_index]

    def get_rect(self):
        """
        Return the cell's position and size inside a rectstyle object
        """
        return pygame.Rect(self.col.left, self.row.top, self.col.width, self.row.height)


class Column:
    """
    A Column can be seen as a list of cells with the same 'col' value.
    It is the manager of GridLayer.cols and can read GridLayer.data
    """

    def __init__(self, grid, index):

        assert isinstance(grid, GridLayer)
        assert isinstance(index, int) and index >= 0
        if debug_with_assert: assert index == len(grid._cols)  # maybe not, if col inserted, but not implemented yet

        self._grid = grid
        self._grid_layer = grid._layer
        self._grid_data = grid._data  # shared ressource
        self._col_index = index
        self._width = grid.col_width
        if self.is_first: self._left = 0
        else: self._left = self.get_previous_col().right  # TODO : + margin

        grid._cols.append(self)  # TODO : insert ?

    def __getitem__(self, row):
        """
        Return the value of the cell in this col, indexed by 'col'
        """
        return self._grid_data[row][self._col_index]

    def __iter__(self):

        for data_row in self._grid_data:
            yield data_row[self._col_index]

    def __contains__(self, item):

        for data_row in self._grid_data:
            if data_row[self._col_index] is item:
                return True
        return False

    components = property(lambda self: tuple(comp for comp in self if comp is not None))
    icomponents = property(lambda self: (comp for comp in self if comp is not None))
    is_adaptable = property(lambda self: self._width is None)
    is_first = property(lambda self: self._col_index is 0)
    is_last = property(lambda self: self._col_index is len(self._grid.cols) - 1)
    left = property(lambda self: self._left)
    right = property(lambda self: self.left + self.width)

    def _update_width(self):
        """
        Adapt the col width to the required width
        """
        w = self.width
        if not self.is_last and self.get_next_col().left == self.left + w:
            return
        if debug_with_assert:
            if self.components:
                has_window = self.components[0].window is not None
            for comp in self.icomponents:
                assert has_window == (comp.window is not None)

        left = self.left
        for comp in self.icomponents:
            row = self._grid.get_row(comp.row)
            comp.set_window((left, row.top, w, row.height), follow_movements=True)
            if comp.sticky is not None:
                comp.origin.unlock()
                comp.origin.config(pos=getattr(self.get_cell(comp.row).get_rect(), comp.sticky))
                comp.origin.lock()
            if debug_with_assert: assert comp.window == self.get_cell_rect(comp.row)

        if not self.is_last:
            self.get_next_col()._update_left(left + w)

    def _update_left(self, left):

        dx = left - self.left
        if dx is 0: return
        self._left = left
        for comp in self.icomponents:
            comp.origin.unlock()
            comp.move(dx=dx)
            comp.origin.lock()

        if not self.is_last:
            self.get_next_col()._update_left(left + self.width)

    def is_empty(self):

        for cell in self:
            if cell is not None:
                return False
        return True

    def get_cell(self, row):
        """
        Return the cell whose column is indexed by 'col'
        """
        return Cell(self._grid, row, self._col_index)

    def get_cell_rect(self, row):
        """
        Optimized shortcut instead of col.get_cell(...).get_rect()
        """
        return self.left, self._grid.get_row(row).top, self.width, self._grid.get_row(row).height

    def get_next_col(self):

        if self.is_last: return
        return self._grid.get_col(self._col_index + 1)

    def get_previous_col(self):
        """
        Return the col above self
        """
        if self.is_first: return None
        return self._grid.get_col(self._col_index - 1)

    def get_rect(self):
        """
        Return the col's position (relative to the container) and size inside a rectstyle object
        """
        return self.left, self._grid_layer.container.top, self.width, self._grid_layer.container.h

    def get_width(self):

        if self._width is not None:
            return self._width

        if self.is_empty():
            return 0

        return max(comp.rect.w for comp in self if comp is not None)

    width = property(get_width)

    def set_width(self, width):
        """
        Set the col's width
        If width is None, the col will adapt to its widest component
        """
        assert (width is None) or isinstance(width, (int, float)) and width >= 0
        if not self._grid.cols_are_adaptable:
            raise PermissionError("This grid has a fixed col_width : {}".format(self._grid.col_width))
        self._width = width
        self._update_width()


class Row:
    """
    A Row can be seen as a list of cells with the same 'row' value.
    It is the manager of GridLayer.rows and can read GridLayer.data
    """
    def __init__(self, grid, index):

        assert isinstance(grid, GridLayer)
        assert isinstance(index, int) and index >= 0
        if debug_with_assert: assert index == len(grid._rows)  # maybe not, if row inserted, but not implemented yet

        self._grid = grid
        self._grid_layer = grid._layer
        self._grid_data = grid._data  # shared ressource
        self._row_index = index
        self._height = grid.row_height
        if self.is_first: self._top = 0
        else: self._top = self.get_previous_row().bottom

        grid._rows.append(self)

    def __getitem__(self, col):
        """
        Return the value of the cell in this row, indexed by 'col'
        """
        return self._grid_data[self._row_index][col]

    def __iter__(self):

        return self._grid_data[self._row_index].__iter__()

    def __contains__(self, item):

        return self._grid_data[self._row_index].__contains__(item)

    bottom = property(lambda self: self.top + self.height)
    components = property(lambda self: tuple(comp for comp in self if comp is not None))
    icomponents = property(lambda self: (comp for comp in self if comp is not None))
    is_adaptable = property(lambda self: self._height is None)
    is_first = property(lambda self: self._row_index is 0)
    is_last = property(lambda self: self._row_index is len(self._grid.rows)-1)
    top = property(lambda self: self._top)

    def _update_height(self):
        """
        Adapt the row height to the required height
        """
        h = self.height
        if self.components and self.components[0].window and self.components[0].window[3] == h:
            if debug_with_assert:
                for comp in self.icomponents: assert self.components[0].window[3] == h

        top = self.top
        for comp in self.icomponents:
            col = self._grid.get_col(comp.col)
            comp.set_window((col.left, top, col.width, h), follow_movements=True)
            if comp.sticky is not None:
                comp.origin.unlock()
                comp.origin.config(pos=getattr(self.get_cell(comp.col).get_rect(), comp.sticky))
                comp.origin.lock()

        if not self.is_last:
            self.get_next_row()._update_top(top + h)

    def _update_top(self, top):

        dy = top - self.top
        if dy is 0: return
        self._top = top
        for comp in self.icomponents:
            comp.origin.unlock()
            comp.move(dy=dy)
            comp.origin.lock()

        if not self.is_last:
            self.get_next_row()._update_top(top + self.height)

    def is_empty(self):

        for cell in self:
            if cell is not None:
                return False
        return True

    def get_cell(self, col):
        """
        Return the cell whose column is indexed by 'col'
        """
        return Cell(self._grid, self._row_index, col)

    def get_cell_rect(self, col):
        """
        Optimized shortcut instead of row.get_cell(...).get_rect()
        """
        return self._grid.get_col(col).left, self.top, self._grid.get_col(col).width, self.height

    def get_height(self):

        if self._height is not None:
            return self._height

        if self.is_empty():
            return 0

        return max(comp.rect.h for comp in self if comp is not None)

    height = property(get_height)

    def get_next_row(self):

        if self.is_last: return
        return self._grid.get_row(self._row_index+1)

    def get_previous_row(self):
        """
        Return the row above self
        """
        if self.is_first: return None
        return self._grid.get_row(self._row_index-1)

    def get_rect(self):
        """
        Return the row's position (relative to the container) and size inside a rectstyle object
        """
        return self._grid_layer.container.left, self.top, self._grid_layer.container.w, self.height

    def set_height(self, height):
        """
        Set the row's height
        If height is None, the row will adapt to its hightest component
        """
        assert (height is None) or isinstance(height, (int, float)) and height >= 0
        if not self._grid.rows_are_adaptable:
            raise PermissionError("This grid has a fixed row_height : {}".format(self._grid.row_height))
        self._height = height
        self._update_height()


class GridLayer(Layer):
    """
    A GridLayer is a Layer who places its components itself, depending on their
    attributes 'row' and 'col'

    If nbrows is None, adding a component will create missing rows if needed
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

    Two components can't fit in the same cell

    WARNING : manipulating a grid with multi-threading might cause issues
    """

    def __init__(self, *args, nbcols=None, nbrows=None, col_width=None, row_height=None, **kwargs):

        Layer.__init__(self, *args, **kwargs)

        if nbcols is not None: assert isinstance(nbcols, int) and nbcols > 0
        if nbrows is not None: assert isinstance(nbrows, int) and nbrows > 0

        self._layer = self
        self._nbcols = None
        self._nbrows = None
        self._col_width = col_width
        self._row_height = row_height

        self._data = [[None]]  # shared ressource initialized with one row and one column
        self._cols = TypedList(Column)
        self._rows = TypedList(Row)

        Row(self, 0)
        Column(self, 0)
        if nbcols: self.set_nbcols(nbcols)
        if nbrows: self.set_nbrows(nbrows)

        if debug_with_assert:
            try:
                assert self.nbcols == len(self._data[0]) == len(self.cols)
                assert self.nbrows == len(self._data) == len(self.rows)
            except AssertionError as e:
                raise e

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

    def _find_place_for(self, comp):
        """
        Renvoie le topleft de la cellule qui pourrait accueillir comp
        """
        1/0
        return (0, 0)  # les coordonnees seront redefines dans GridLayer.add

        if debug_with_assert: assert comp.col is not None and comp.row is not None

        if self.nbcols-1 < comp.col:
            if self._nbcols is not None:
                raise PermissionError("Cannot add {} inside {}, its col value is too big : {}"
                                      "".format(comp, self, comp.col))
            x = self.cols[-1].right
            col = self.get_col(-1)
        else:
            x = self.cols[comp.col].left if self.col_width is None else comp.col * self.col_width
            col = self.get_col(comp.col)

        if self.nbrows-1 < comp.row:
            if self._nbrows is not None:
                raise PermissionError("Cannot add {} inside {}, its row value is too big : {}"
                                      "".format(comp, self, comp.row))
            y = self.rows[-1].bottom
            row = self.nbrows-1
        else:
            y = self.rows[comp.row].top if self.row_height is None else comp.row * self.row_height
            row = comp.col

        if comp._sticky is not None:
            cell = col.get_cell(row)
            # rect = cell.get_rect()
            # pos = getattr(cell.get_rect(), comp._sticky)
            return getattr(cell.get_rect(), comp._sticky)

        return (x, y)

    def _update_size(self, *args):

        for row in self.rows:
            row._update_height()
        for col in self.cols:
            col._update_width()

    def accept(self, comp):
        """You must define at least the row or the column in order to insert a widget in a grid layer"""
        if (comp.col is None) or (comp.row is None):
            return False
        return super().accept(comp)

    def add(self, comp):

        # TODO : solve : sticky positions are not updated when the grid is resized

        if (comp.col is None) or (comp.row is None):
            raise PermissionError(
                "You must define at least the row or the column in order to insert a widget in a GridLayer")
        try:
            super().add(comp)
            if self._nbcols is None and len(self.cols)-1 < comp.col:
                self.set_nbcols(comp.col+1)
                self._nbcols = None
            if self._nbrows is None and len(self.rows)-1 < comp.row:
                self.set_nbrows(comp.row+1)
                self._nbrows = None

            if self._data[comp.row][comp.col] is not None:
                raise PermissionError("Cannot insert {} at positon : row={}, col={}, because {} is already there"
                                      "".format(comp, comp.row, comp.col, self._data[comp.row][comp.col]))

            if debug_with_assert: assert not comp.has_locked.origin, "This should be checked in Widget.__init__()"
            # comp.move_at(key="topleft", value=self._find_place_for(comp))
            if comp.sticky is not None:

                # Here, the grid layer has to be the only one who gives a position to the widget

                pos = getattr(self.get_cell(comp.row, comp.col).get_rect(), comp.sticky)
                comp.origin.config(
                    pos=pos, location=comp.sticky, reference_comp=self.container,
                    reference_location="topleft", locked=True
                )
            else:
                pos = self.get_cell(comp.row, comp.col).get_rect().topleft
                comp.origin.config(
                    pos=pos, location="topleft", reference_comp=self.container,
                    reference_location="topleft", locked=True
                )
            # if debug_with_assert:
            #     if comp._sticky is None:
            #         assert comp.topleft == self._find_place_for(comp)

            row = self.rows[comp.row]
            col = self.cols[comp.col]
            new_h = row.is_adaptable and comp.height > row.height
            new_w = col.is_adaptable and comp.width > col.width
            self._data[comp.row][comp.col] = comp
            if new_h: row._update_height()
            if new_w: col._update_width()
            if comp.window is None:
                comp.set_window(row.get_cell_rect(comp.col))
            if debug_with_assert: assert comp.window is not None, comp

            if debug_with_assert: assert self.nbcols == len(self._data[0]) == len(self.cols)
            if debug_with_assert: assert self.nbrows == len(self._data) == len(self.rows)

            # don't need owner because, if the grid is killed,
            # it means the container is killed, so the comp is also killed
            self.connect("_update_size", comp.signal.RESIZE)
            self.connect("_update_size", comp.signal.KILL)

        except Exception as e:
            raise e

    def move(self, widget, col, row):

        assert widget in self
        if self._data[row][col] is not None:
            if self._data[row][col] is widget:
                return
            raise PermissionError("This cell is already occupied by : "+str(self._data[row][col]))

        self._data[widget.row][widget.col] = None
        self._data[row][col] = widget
        widget._col = col
        widget._row = row

        widget.origin.unlock()
        if widget.sticky is not None:
            pos = getattr(self.get_cell(widget.row, widget.col).get_rect(), widget.sticky)
        else:
            pos = self.get_cell(widget.row, widget.col).get_rect().topleft
        widget.origin.config(pos=pos, locked=True)
        widget.set_window(self.rows[widget.row].get_cell_rect(widget.col))

    def remove(self, comp):

        super().remove(comp)
        assert self._data[comp.row][comp.col] is comp
        self._data[comp.row][comp.col] = None

    def get_cell(self, row, col):

        return self.get_col(col).get_cell(row)

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

    def pack(self):
        """
        Remove all empty rows and columns
        """
        for row in tuple(self.rows):
            if row.is_empty():
                self._data.pop(row.row_index)
                self.rows.remove(row)
        for col in tuple(self.cols):
            if col.is_empty():
                for data_row in self._data:
                    data_row.pop(col.col_index)
                self.cols.remove(col)

    def set_col_width(self, width):

        assert (width is None) or isinstance(width, (int, float)) and width >= 0

        self._col_width = None
        for col in self.cols:
            col.set_width(width)
        self._col_width = width

    def set_nbcols(self, nbcols):
        """
        Set the number of columns
        If nbcols is None, adding a component will create missing columns if needed
        """
        assert isinstance(nbcols, int) and nbcols > 0, nbcols
        if nbcols is not None:
            nbnew = nbcols - self.nbcols
            if nbnew < 0:
            # Delete extra columns
                if debug_with_assert: assert nbnew > 0, "A grid must have at least 1 column"
                for i in range(nbcols, self.nbcols):
                    if not self._cols[i].is_empty():
                        raise PermissionError("Cannot reduce nbcols, at least one extra column contains something")
                    self._cols[i].kill()  # TODO : implement
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
        If nbrows is None, adding a component will create missing rows if needed
        """
        assert isinstance(nbrows, int) and nbrows > 0
        if nbrows is not None:
            nbnew = nbrows - self.nbrows
            if nbrows < 0:
            # Delete extra columns
                if debug_with_assert: assert nbrows > 0, "A grid must have at least 1 row"
                for i in range(nbrows, self.nbrows):
                    if not self._rows[i].is_empty():
                        raise PermissionError("Cannot reduce nbrows, at least one row to delete contains something")
                    self._rows[i].kill()  # TODO : implement
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

        widget1.origin.unlock()
        widget2.origin.unlock()

        self._data[widget1.row][widget1.col] = widget2
        self._data[widget2.row][widget2.col] = widget1

        widget1._col, widget1._row, widget2._col, widget2._row = widget2._col, widget2._row, widget1._col, widget1._row

        for widget in widget1, widget2:
            if widget.sticky is not None:
                pos = getattr(self.get_cell(widget.row, widget.col).get_rect(), widget.sticky)
            else:
                pos = self.get_cell(widget.row, widget.col).get_rect().topleft
            widget.origin.config(pos=pos, locked=True)
            widget.set_window(self.rows[widget.row].get_cell_rect(widget.col))


