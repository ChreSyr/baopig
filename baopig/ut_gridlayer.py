
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

class UT_GridLayer_Scene(Zone):

    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        self.set_mode(RESIZABLE)

        Layer(self, "zones_layer", adaptable=False)  # TODO : test adaptable
        z1 = Zone(self, size=(self.w-20, 130), background_color=(150, 150, 150), pos=(10, 10))
        z2 = Zone(self, size=(self.w-20, 130), background_color=(150, 150, 150),
                  origin=Origin(pos=(0, 10), reference_comp=z1, reference_location="bottomleft"))
        z3 = Zone(self, size=(self.w-20, 400), background_color=(150, 150, 150),
                  origin=Origin(pos=(0, 10), reference_comp=z2, reference_location="bottomleft"))

        z1.grid = GridLayer(z1, "grid_layer", row_height=40, col_width=100)
        assert z1.layers_manager.default_layer == z1.grid
        for row in range(2):
            for col in range(5):
                text = "row:{}\ncol:{}".format(row, col)
                Text(z1, text, row=row, col=col, name=text)

        z2.grid = GridLayer(z2, "grid_layer")
        for row in range(3):
            for col in range(5):
                text = "row:{}\ncol:{}".format(row, col)
                Text(z2, text, row=row, col=col, name=text)
        r = Rectangle(z2, (130, 49, 128), size=(30, 30), col=5, row=0)
        Dragable.set_dragable(r)
        Text(z2, "HI", col=6, row=0)
        Text(z2, "HI", col=7, row=1)
        r = Rectangle(z2, (130, 49, 128), size=(30, 30), col=8, row=2)
        Dragable.set_dragable(r)
        Button(z2, "Update sizes", command=z2.grid._update_size, col=0, row=3)

        grid = GridLayer(z3, "grid_layer", nbrows=3, nbcols=3)
        class RemovableRect(Rectangle, Linkable):
            def __init__(self, *args, **kwargs):
                Rectangle.__init__(self, *args, **kwargs)
                Linkable.__init__(self)
                def update(*args):
                    if self.collidemouse() and isinstance(mouse.linked_comp, RemovableRect):
                        self.kill()
                self.connect("kill", self.signal.LINK)
                mouse.signal.DRAG.add_command(update)
                self.parent.signal.RESIZE.add_command(update)
        import random
        color = lambda: [int(random.random() * 255)] * 2 + [128]
        def toggle_col_size(col_index):
            col = grid.get_col(col_index)
            if col.is_adaptable:  col.set_width(40)
            elif col.width == 40: col.set_width(20)
            else:                 col.set_width(None)
            if col.is_adaptable:  col[-1].kill()
        def toggle_row_size(row_index):
            row = grid.get_row(row_index)
            if row.is_adaptable:   row.set_height(40)
            elif row.height == 40: row.set_height(20)
            else:                  row.set_height(None)
            if row.is_adaptable:   row[-1].kill()
        def add_rect():
            for row in range(grid.nbrows):
                for col in range(grid.nbcols):
                    if grid._data[row][col] is None:
                        if row is grid.nbrows-1:
                            Button(z3, "TOG", row=row, col=col,
                                   command=PrefilledFunction(toggle_col_size, col),
                                   catch_errors=False, w=30, h=30)
                        elif col is grid.nbcols-1:
                            Button(z3, "TO\nG", row=row, col=col,
                                   command=PrefilledFunction(toggle_row_size, row),
                                   catch_errors=False, w=30, h=30)
                        else:
                            RemovableRect(z3, color(), (30, 30), col=col, row=row)
        Button(z3, "ADD", row=0, col=0, command=add_rect, catch_errors=True, w=30, h=30)
        def fix():
            if grid.cols_are_adaptable:
                grid.set_row_height(30)
                grid.set_col_width(30)
            else:
                grid.set_row_height(None)
                grid.set_col_width(None)
        Button(z3, "FIX", row=0, col=1, command=fix, catch_errors=False)

        # self.handle_event[mouse.LEFTBUTTON_DOWN].add(print)
        # self.handle_event[mouse.DRAG].add(print)
        # self.handle_event[mouse.RELEASEDRAG].add(print)


ut_scenes = [
    UT_GridLayer_Scene,
]


if __name__ == "__main__":
    from baopig.unit_tests.TesterScene import TesterScene
    app = Application()
    for scene in ut_scenes:
        TesterScene(app, scene)
    app.launch()


