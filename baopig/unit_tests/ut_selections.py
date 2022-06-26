

from baopig import *


class UT_Selectable(Rectangle, Selectable):

    def __init__(self, parent, pos):

        Rectangle.__init__(self, parent, color="blue", size=(30, 30), pos=pos)
        Selectable.__init__(self)
        self.hightlighter = None
        self.timer = None

    def select(self):

        self.set_color("blue4")
        self.highlight("green")

    def unselect(self):

        self.set_color("blue")
        self.highlight("red")

    def highlight(self, color):

        def timeout():
            self.hightlighter.kill()
            self.hightlighter = None

        if self.hightlighter is not None:
            if self.hightlighter.color == Color(color):
                return
            self.timer.cancel()
            timeout()
        self.hightlighter = Highlighter(self.parent, self, color, 2)
        self.timer = Timer(.4, timeout)
        self.timer.start()


class UT_Selector(Zone, Selector):

    def __init__(self, *args, **kwargs):

        Zone.__init__(self, *args, **kwargs)
        Selector.__init__(self)
        self.enable_selecting(True)


class UT_Selections_Zone(UT_Selector):

    def __init__(self, *args, **kwargs):
        UT_Selector.__init__(self, *args, **kwargs)

        z = UT_Selector(self, size=(self.w/3, self.h - 20), background_color="gray",
                        pos=("50%", 10), pos_location="midtop")
        UT_Selectable(z, (10, 10))
        UT_Selectable(z, (50, 10))
        UT_Selectable(z, (90, 10))
        Text(z, "I am selectable", pos=(10, 50))
        TextEdit(z, width=z.w - 20, pos=(10, 75))  # TODO : Scrollable

        z2 = UT_Selector(z, size=(z.w-20, (z.h-40)/3), background_color=(128, 128, 128),
                         pos=(10, "50%"), pos_location="midleft")
        z2.enable_selecting(False)
        UT_Selectable(z2, (10, 10))
        UT_Selectable(z2, (50, 10))
        UT_Selectable(z2, (90, 10))
        Text(z2, "I am not selectable", pos=(10, 50))
        TextEdit(z2, width=z2.w - 20, pos=(10, 75))

        z3 = UT_Selector(z, size=(z.w-20, (z.h-40)/3), background_color=(128, 128, 128, 200),
                         pos=(10, -10), pos_location="bottom", pos_ref_location="bottom")
        z3.set_selectionrect_visibility(False)
        UT_Selectable(z3, (10, 10))
        UT_Selectable(z3, (50, 10))
        UT_Selectable(z3, (90, 10))
        Text(z3, "Selection rectangle ?", pos=(10, 50))
        TextEdit(z3, width=z3.w - 20, pos=(10, 75))

        UT_Selectable(self, (10, 10))
        UT_Selectable(self, (50, 10))
        UT_Selectable(self, (90, 10))
        Text(self, "I am selectable", pos=(10, 50))
        TextEdit(self, width=z.w - 20, pos=(10, 75))

        UT_Selectable(self, (z.right + 10, 10))
        UT_Selectable(self, (z.right + 50, 10))
        UT_Selectable(self, (z.right + 90, 10))
        Text(self, "I am selectable", pos=(z.right + 10, 50))
        TextEdit(self, width=z.w - 20, pos=(z.right + 10, 75))

    def load_sections(self):
        self.parent.add_section(
            title="Selector",
            tests=[
                "A Selector can be focused",
                "When receive Ctrl + A, calls the 'select_all' method",
                "The default implementation of 'select_all' selects all selectable children",
                "When receive link_motion, it creates a SelectionRect",
                "When receive Ctrl + C, calls the 'copy' method",
                "The default implementation of 'copy' collects data from selected Selectables, join into a string and send it to the clipboard",
                "When receive Ctrl + X, calls the 'cut' method (no default implementation)",
                "When receive Ctrl + V, calls the 'paste' method (no default implementation)",
                "The call of 'disable_selecting' will deactivate the selection ability",
            ]
            # TODO : zone=Zone(...)
        )

        self.parent.add_section(
            title="Selectable",
            tests=[
                "A Selectable's selector is the youngest Selector in Selectable's family tree",
                "For each selection rect movement, if it collide with a selectable, it calls the 'select' method",
                "At the time selection rect don't collide with a selectable anymore, 'unselect' is called",
            ]
        )

        self.parent.add_section(
            title="The selection rectangle",
            tests=[
                "A drag on a focused Selector create a selection rect",
                "A released drag will hide the selection rect",
                "The selection rect can be configured throught passing a subclass of SelectionRect in the Selector constructor",
                "The visibility of the selection rect can be edited -> set_selectionrect_visibility",
                "When setting an end position for the selection rect, a temporary visibility can be given in argument",
                "The selection rect is always fitting inside its parent",
            ]
        )


# For the PresentationScene import
ut_zone_class = UT_Selections_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
