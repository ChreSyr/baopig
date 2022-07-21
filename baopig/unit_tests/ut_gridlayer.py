
from baopig import *


class UT_GridLayer_Zone(Zone):

    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        Layer(self, name="zones_layer", spacing=10)
        z1 = Zone(self, size=("100%", 130), background_color=(150, 150, 150))
        z2 = Zone(self, size=("100%", 130), background_color=(150, 150, 150))
        z3 = Zone(self, size=("100%", 155), background_color=(150, 150, 150))
        z4 = Zone(self, size=("100%", 120), background_color=(150, 150, 150))
        self.default_layer.pack()
        z3.set_style_for(Button, padding=2)

        # Z1
        z1.grid = GridLayer(z1, name="grid_layer", row_height=40, col_width=100)
        assert z1.layers_manager.default_layer == z1.grid
        for row in range(2):
            for col in range(5):
                text = "row:{}\ncol:{}".format(row, col)
                Text(z1, text, row=row, col=col, name=text)

        # Z2
        z2.grid = GridLayer(z2, name="grid_layer")
        for row in range(3):
            for col in range(5):
                text = "row:{}\ncol:{}".format(row, col)
                Text(z2, text, row=row, col=col, name=text)

        class DraggableRectangle(Rectangle, DraggableByMouse):
            def __init__(self, parent, **kwargs):
                Rectangle.__init__(self, parent, **kwargs)
                DraggableByMouse.__init__(self, parent, **kwargs)

        DraggableRectangle(parent=z2, color=(130, 49, 128), size=(30, 30))
        Text(z2, "HI", col=6, row=0)
        Text(z2, "HI", col=7, row=1)
        DraggableRectangle(parent=z2, color=(130, 49, 128), size=(30, 30), col=8, row=2)

        # Z3
        grid = GridLayer(z3, nbrows=5, nbcols=10)

        class RemovableRect(Rectangle, LinkableByMouse):
            def __init__(self, *args, **kwargs):
                Rectangle.__init__(self, *args, **kwargs)
                LinkableByMouse.__init__(self, *args)

            def handle_link(self):
                self.kill()

        import random
        random_color = lambda: [int(random.random() * 255)] * 2 + [128]

        def toggle_col_size(col_index):
            col = grid.get_col(col_index)
            if col.is_adaptable:
                col.set_width(40)
            elif col.get_width() == 40:
                col.set_width(20)
            else:
                col.set_width(None)
            if col.is_adaptable:
                col[-1].kill()

        def toggle_row_size(row_index):
            row = grid.get_row(row_index)
            if row.is_adaptable:
                row.set_height(40)
            elif row.get_height() == 40:
                row.set_height(20)
            else:
                row.set_height(None)
            if row.is_adaptable:
                row[-1].kill()

        def add_rect():
            for row in range(grid.nbrows):
                for col in range(grid.nbcols):
                    if grid._data[row][col] is None:
                        if row is grid.nbrows - 1:
                            Button(z3, "TOG", row=row, col=col, size=(30, 30), catching_errors=True,
                                   command=PrefilledFunction(toggle_col_size, col))
                        elif col is grid.nbcols - 1:
                            Button(z3, "TOG", row=row, col=col, size=(30, 30), catching_errors=True,
                                   command=PrefilledFunction(toggle_row_size, row))
                        else:
                            RemovableRect(z3, color=random_color(), size=(30, 30), col=col, row=row, loc="center")
        Button(z3, "ADD", row=0, col=0, command=add_rect, width=30, height=30)

        def fix():
            if grid.cols_are_adaptable:
                grid.set_row_height(30)
                grid.set_col_width(30)
            else:
                grid.set_row_height(None)
                grid.set_col_width(None)
        Button(z3, "FIX", row=0, col=1, command=fix)

        # Z4
        grid4 = GridLayer(z4, Rectangle, nbrows=4, nbcols=10, row_height=30, col_width=30)
        for row in range(grid4.nbrows):
            for col in range(grid4.nbcols):
                Rectangle(z4, color=(130, 49, 128), row=row, col=col, size=("33%", "33%"), loc="topright")

        buttons_layer = GridLayer(z4, nbrows=3, nbcols=3)

        def click():
            for w in grid4:
                w.set_lock(pos=False)  # TODO : remove ?
                w.pos_manager.config(loc=mouse.hovered_widget.text_widget.text)
                w.set_lock(pos=True)
            grid4.pack()
        Button(z4, row=0, col=0, command=click, text="topleft")
        Button(z4, row=1, col=0, command=click, text="midleft")
        Button(z4, row=2, col=0, command=click, text="bottomleft")
        Button(z4, row=0, col=1, command=click, text="midtop")
        Button(z4, row=1, col=1, command=click, text="center")
        Button(z4, row=2, col=1, command=click, text="midbottom")
        Button(z4, row=0, col=2, command=click, text="topright")
        Button(z4, row=1, col=2, command=click, text="midright")
        Button(z4, row=2, col=2, command=click, text="bottomright")
        buttons_layer.pack(start_pos=(320, 8))

    def load_sections(self):
        self.parent.add_section(
            title="Selector",
            tests=[
                "Any widget from a GridLayer requires 'row' and 'col' attributes",
                "Can't define 'pos' attribute of widgets who will be stored in a grid",
                "Default behavior is to create rows and columns automatically",
                "When the nbrows is set, we can't add a widget who would like to go outside, same for nbcols",
                "A row without defined height adapts to its children, 0 if empty, same for columns",
                "We can set a default size for rows and columns",
                "A widget's hitbox is always inside its cell -> the cell defines the window",
                "We can resize a row without any visual bug inside the row, same for columns -> the window is updated",
                "Resizing a row moves the rows located below, same for columns",
                "Widgets in a grid can't manage their position themselves (non-dragable)",
            ]
        )


# For the PresentationScene import
ut_zone_class = UT_GridLayer_Zone

if __name__ == "__main__":
    from baopig.prefabs.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
