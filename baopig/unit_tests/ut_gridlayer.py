
from baopig import *


# ------ TESTS TO ENFORCE ------
# TEST 01 : Any component from a GridLayer require 'row' and 'col' attributes
# TEST 02 : Can't define 'pos' and 'origin' attributes of components who will be stored in a grid
# TEST 03 : Default behavior is to create rows and columns automatically
# TEST 04 : When the nbrows is set, we can't add a component who would like to go outside, same for nbcols
# TEST 05 : A row without defined height adapt to its components, 0 if empty, same for columns
# TEST 06 : We can set a default size for rows and columns
# TEST 07 : A component's hitbox is always inside its cell -> the cell defines the window
# TEST 08 : We can resize a row without any visual bug inside the row, same for columns -> the window is updated
# TEST 09 : Resizing a row moves the rows located below, same for columns
# TEST 10 : Components in a grid can't manage their position themself (non-dragable)

# ------ TESTS TO APPLY ------
# TODO : write unit tests with the removable rects

# TODO : rethink : can a component located in a grid move itself (via Dragable for example)

class UT_GridLayer_Zone(Zone):

    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        Layer(self, name="zones_layer", adaptable=False)  # TODO : test adaptable
        z1 = Zone(self, size=(self.w-20, 130), background_color=(150, 150, 150), pos=(10, 10))
        z2 = Zone(self, size=(self.w-20, 130), background_color=(150, 150, 150),
                  pos=(0, 10), pos_ref=z1, pos_ref_location="bottomleft")
        z3 = Zone(self, size=(self.w-20, 400), background_color=(150, 150, 150),
                  pos=(0, 10), pos_ref=z2, pos_ref_location="bottomleft")
        z3.set_style_for(Button, padding=2)

        z1.grid = GridLayer(z1, name="grid_layer", row_height=40, col_width=100)
        assert z1.layers_manager.default_layer == z1.grid
        for row in range(2):
            for col in range(5):
                text = "row:{}\ncol:{}".format(row, col)
                Text(z1, text, row=row, col=col, name=text)

        z2.grid = GridLayer(z2, name="grid_layer")  # TODO : solve : some text disappear when selected, warn_change problem
        for row in range(3):
            for col in range(5):
                text = "row:{}\ncol:{}".format(row, col)
                Text(z2, text, row=row, col=col, name=text)

        class DragableRectangle(Rectangle, Dragable):
            def __init__(self, **kwargs):
                Rectangle.__init__(self, **kwargs)
                Dragable.__init__(self)
        r = DragableRectangle(parent=z2, color=(130, 49, 128), size=(30, 30))
        Text(z2, "HI", col=6, row=0)
        Text(z2, "HI", col=7, row=1)
        r = DragableRectangle(parent=z2, color=(130, 49, 128), size=(30, 30), col=8, row=2)
        Button(z2, "Update sizes", command=z2.grid._update_size, col=0, row=3)

        grid = GridLayer(z3, name="grid_layer", nbrows=10, nbcols=10)
        class RemovableRect(Rectangle, Linkable):
            def __init__(self, *args, **kwargs):
                Rectangle.__init__(self, *args, **kwargs)
                Linkable.__init__(self)
                def update(*args):
                    if self.collidemouse() and isinstance(mouse.linked_comp, RemovableRect):
                        self.kill()
                self.signal.LINK.connect(self.kill, owner=self)
                mouse.signal.DRAG.connect(update, owner=None)
                self.parent.signal.RESIZE.connect(update, owner=self)
        import random
        random_color = lambda: [int(random.random() * 255)] * 2 + [128]
        def toggle_col_size(col_index):
            col = grid.get_col(col_index)
            if col.is_adaptable:  col.set_width(40)
            elif col.get_width() == 40: col.set_width(20)
            else:                 col.set_width(None)
            if col.is_adaptable:  col[-1].kill()
        def toggle_row_size(row_index):
            row = grid.get_row(row_index)
            if row.is_adaptable:   row.set_height(40)
            elif row.get_height() == 40: row.set_height(20)
            else:                  row.set_height(None)
            if row.is_adaptable:   row[-1].kill()
        def add_rect():
            for row in range(grid.nbrows):
                for col in range(grid.nbcols):
                    if grid._data[row][col] is None:
                        if row is grid.nbrows-1:
                            Button(z3, "TOG", row=row, col=col, size=(30, 30), catching_errors=True,
                                   command=PrefilledFunction(toggle_col_size, col))
                        elif col is grid.nbcols-1:
                            Button(z3, "TOG", row=row, col=col, size=(30, 30), catching_errors=True,
                                   command=PrefilledFunction(toggle_row_size, row))
                        else:
                            RemovableRect(z3, color=random_color(), size=(30, 30), col=col, row=row)
        Button(z3, "ADD", row=0, col=0, command=add_rect, width=30, height=30)
        def fix():
            if grid.cols_are_adaptable:
                grid.set_row_height(30)
                grid.set_col_width(30)
            else:
                grid.set_row_height(None)
                grid.set_col_width(None)
        Button(z3, "FIX", row=0, col=1, command=fix)

        # self.handle_event[mouse.LEFTBUTTON_DOWN].add(print)
        # self.handle_event[mouse.DRAG].add(print)
        # self.handle_event[mouse.RELEASEDRAG].add(print)


# For the PresentationScene import
ut_zone_class = UT_GridLayer_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
