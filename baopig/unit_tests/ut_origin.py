
from baopig import *


class DragableRectangle(Rectangle, DraggableByMouse):
    def __init__(self, parent, **kwargs):
        Rectangle.__init__(self, parent, **kwargs)
        DraggableByMouse.__init__(self, parent, **kwargs)


class DragableZone(Zone, DraggableByMouse):
    def __init__(self, parent, **kwargs):
        Zone.__init__(self, parent, **kwargs)
        DraggableByMouse.__init__(self, parent, **kwargs)


class UT_Origin_Zone(Zone):

    def __init__(self, *args, **kwargs):

        Zone.__init__(self, *args, **kwargs)

        # Magical show
        b = Rectangle(self, pos=(7, 7), ref=self, color=(0, 0, 0, 0), touchable=False,
                      border_color=(128, 10, 10), size=(100, 100), border_width=3)

        # Prisonner at center of the magical show
        z = DragableZone(self, sticky="midtop", size=(100, 100), background_color=(40, 34, 34), name="bottom")
        z.move_behind(b)
        DragableRectangle(z, color=(0, 128, 128), size=(30, 30), center=z.auto_rect.center, ref=b)

        # Prisonner inside magical show, at center of its zone
        z = DragableZone(self, sticky="topright", size=(100, 100), background_color=(40, 34, 34), name="bottomright")
        z.move_behind(b)
        z_window = Zone(z, size=("100%", "100%"), ref=b)
        DragableRectangle(z_window, color=(0, 128, 128), size=(30, 30), center=z.auto_rect.center, ref=z)

        # CLOCK
        z2 = DragableZone(self, midtop=("-50%", 186), refloc="topright",
                          size=(350, 350), background_color=(140, 140, 140), name="z3")
        z3 = DragableZone(z2, sticky="center",
                          size=(250, 250), background_color=(150, 150, 150), name="z2")
        ref = DragableRectangle(z3, center=("50%", "50%"), ref=self,
                                color=(128, 128, 0), size=(30, 30), name="ref")
        import math
        radius = 100
        step = int(math.degrees((2 * math.pi) / 8))
        for i in range(0, int(math.degrees(2 * math.pi)), step):
            Rectangle(z2, color=(150, 120, 0), size=ref.rect.size,
                      pos=(math.cos(math.radians(i)) * radius,
                           math.sin(math.radians(i)) * radius),
                      ref=ref, name="rect({})".format(i))
        for i in range(0, int(math.degrees(2 * math.pi)), step):
            i += step / 2
            Rectangle(z3, color=ref.color, size=ref.rect.size,
                      pos=(math.cos(math.radians(i)) * radius,
                           math.sin(math.radians(i)) * radius),
                      ref=ref, name="rect({})".format(i))

        # Family
        r1 = DragableRectangle(self, pos=(0, "50%"), color=(100, 50, 25), size=(30, 30), name="r1")
        r2 = DragableRectangle(self, pos=(40, 0), ref=r1, color=(50, 100, 25), size=(30, 30), name="r2")
        r3 = DragableRectangle(self, pos=(0, 40), ref=r2, color=(100, 50, 25), size=(30, 30), name="r3")
        DragableRectangle(self, pos=(-40, 0), ref=r3, color=(50, 100, 25), size=(30, 30), name="r4")
        DragableRectangle(self, pos=("50%", "50%"), ref=r1, color=(75, 75, 25), size=(40, 40))

        # CROSS
        Rectangle(self, color=(0, 0, 0), size=(6, 20), sticky="center")
        Rectangle(self, color=(0, 0, 0), size=(20, 6), sticky="center")

    def load_sections(self):
        self.parent.add_section(
            title="Selector",
            tests=[
                "the cross is always at the texting zone center, even after a resize",
                "the topright and midtop corners can be dragged",
                "the topright and midtop corners follow the testing zone resizing even after being moved",
                "if the topright corner is set inside the topleft border, a prisonner appears at corner's center",
                "if the midtop corner is set inside the topleft border, a prisonner appears at border'center",
                "when the midtop corner moves, the prisonner is visually static, even with low fps",
                "a prisonner can be dragged",
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
    from baopig.prefabs.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
