
from baopig import *


class DragableRectangle(Rectangle, Draggable):
    def __init__(self, parent, **kwargs):
        Rectangle.__init__(self, parent, **kwargs)
        Draggable.__init__(self, parent, **kwargs)


class DragableZone(Zone, Draggable):
    def __init__(self, parent, **kwargs):
        Zone.__init__(self, parent, **kwargs)
        Draggable.__init__(self, parent, **kwargs)


class UT_Origin_Zone(Zone):

    def __init__(self, *args, **kwargs):

        Zone.__init__(self, *args, **kwargs)

        # Magical show
        b = Rectangle(self, pos=(7, 7), pos_ref=self, color=(0, 0, 0, 0), touchable=False,
                      border_color=(128, 10, 10), size=(100, 100), border_width=3)

        # Prisonner at center of the magical show
        z = DragableZone(self, sticky="top", size=(100, 100), background_color=(40, 34, 34), name="bottom")
        z.move_behind(b)
        DragableRectangle(z, color=(0, 128, 128), size=(30, 30), pos=z.auto.center, pos_location="center", pos_ref=b)

        # Prisonner inside magical show, at center of its zone
        z = DragableZone(self, pos_location="topright", pos_ref_location="topright",
                         size=(100, 100), background_color=(40, 34, 34), name="bottomright")
        z.move_behind(b)
        r = DragableRectangle(z, color=(0, 128, 128), size=(30, 30), pos=z.auto.center, pos_location="center")
        def handle_motion(z, b, r, dx, dy):
            rect = pygame.Rect(b.abs)
            rect.top -= z.abs.top
            rect.left -= z.abs.left
            r.set_window(rect)
        z.signal.MOTION.connect(PrefilledFunction(handle_motion, z, b, r), owner=None)
        handle_motion(z, b, r, 0, 0)

        # PRISONNER
        z = DragableZone(self, sticky="right", size=(100, 100), background_color=(0, 64, 64), name="right")
        r = DragableRectangle(z, color=(0, 128, 128), size=(30, 30), pos=z.auto.center, pos_location="center")
        wb = Rectangle(z, pos=("50%", "50%"), pos_location="center", color=(0, 0, 0, 0),
                       size=[z.w-20]*2, border_color=(0, 0, 0), border_width=1, touchable=False)
        r.set_window(wb.rect)

        # CLOCK
        z2 = DragableZone(self, pos=("-50%", 186), pos_location="midtop", pos_ref_location="topright",
                          size=(350, 350), background_color=(140, 140, 140), name="z3")
        z3 = DragableZone(z2, pos=(0, 0), pos_location="center", pos_ref_location="center",
                          size=(250, 250), background_color=(150, 150, 150), name="z2")
        ref = DragableRectangle(z3, pos=("50%", "50%"), pos_location="center", pos_ref=self,
                                color=(128, 128, 0), size=(30, 30), name="ref")
        import math
        radius = 100
        step = int(math.degrees((2 * math.pi) / 8))
        for i in range(0, int(math.degrees(2 * math.pi)), step):
            r = Rectangle(z2, color=ref.color, size=ref.size,
                          pos=(math.cos(math.radians(i)) * radius,
                               math.sin(math.radians(i)) * radius),
                          pos_ref=ref, name="rect({})".format(i))
        for i in range(0, int(math.degrees(2 * math.pi)), step):
            i += step / 2
            r = Rectangle(z3, color=(150, 120, 0), size=ref.size,
                          pos=(math.cos(math.radians(i)) * radius,
                               math.sin(math.radians(i)) * radius),
                          pos_ref=ref, name="rect({})".format(i))

        # Family
        # These 5 rectangles are referenced to each other, forming a chain
        # The loop is broken by the fact that widget.move_at(widget.pos) does nothing
        r1 = DragableRectangle(self, pos=(0, "50%"), color=(100, 50, 25), size=(30, 30), name="r1")
        r2 = DragableRectangle(self, pos=(40, 0), pos_ref=r1, color=(50, 100, 25), size=(30, 30), name="r2")
        r3 = DragableRectangle(self, pos=(0, 40), pos_ref=r2, color=(100, 50, 25), size=(30, 30), name="r3")
        DragableRectangle(self, pos=(-40, 0), pos_ref=r3, color=(50, 100, 25), size=(30, 30), name="r4")
        DragableRectangle(self, pos=("50%", "50%"), pos_ref=r1, color=(75, 75, 25), size=(40, 40))

        # CROSS
        c1 = Rectangle(self, color=(0, 0, 0), size=(6, 20),
                       pos=(0, 0), pos_location="center", pos_ref_location="center")
        c2 = Rectangle(self, color=(0, 0, 0), size=(20, 6),
                       pos=(0, 0), pos_location="center", pos_ref_location="center")

    def load_sections(self):
        self.parent.add_section(
            title="Selector",
            tests=[
                "the cross is always at the texting zone center, even after a resize",
                "the topright and midtop corners can be dragged",
                "the topright and midtop corners follow the testing zone resizing even after being moved",
                "a prisonner can only be seen trought its window",
                "the first prisonner (light blue rect) is not visible outside the window (black border)",
                "if the topright corner is set inside the topleft border, a prisonner appears at corner's center",
                "if the midtop corner is set inside the topleft border, a prisonner appears at border'center",
                "when the midtop corner moves, the prisonner is visually static, even with low fps",
                "the first prisonner can be dragged",
                "the first prisonner can only be seen trought the window, once again",
                "the clock (light gray surface at the center) can be dragged",
                "after the scene width changed, the clock abcissa is still at the center of the application",
                "if the clock has moved, after a scene resizing, it keeps the same distance from the scene's right",
                "the belt (rects around the clock center) cannot be dragged",
                "the yellow center (yellow rect at the clock center) can be dragged",
                "the belt follow the yellow center everywhere he goes",
                "dragging the yellow center don't cause lag",
            ]
        )


# For the PresentationScene import
ut_zone_class = UT_Origin_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
