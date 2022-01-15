

from baopig import *


class UT_Origin_Scene(Scene):

    def __init__(self):
        # TEST : the cross is always at the application center, even after a scene resize
        # TEST : the prisonner (light blue rect) is not visible inside the window (black border on topright corner)
        # TEST : the corners are still at the application corners after a scene resize
        # TEST : the bottomleft corner cannot be dragged, despite the set_dragable
        # TEST : the topright and bottom right corners can be dragged
        # TEST : the topright and bottom right corners follow the scene resizing even after being moved
        # TEST : if the topright corner is set inside the topleft blue border, the prisonner appears
        # TEST : the prisonner can only be seen trought the window
        # TEST : when the topright corner moves, the prisonner is visually static, even with low fps
        # TEST : the prisonner can be dragged
        # TEST : the prisonner can only be seen trought the window, once again
        # TEST : after the scene width changed, the clock abcissa is still at the center of the application
        # TEST : the clock (light gray surface at the center) can be dragged
        # TEST : if the clock has moved, after a scene resizing, it keeps the same distance from the scene's right
        # TEST : the yellow belt (yellow rects around the clock center) cannot be dragged
        # TEST : the yellow center (yellow rect at the clock center) can be dragged
        # TEST : the yellow belt follow the yellow center everywhere he goes
        # TEST : dragging the yellow center don't cause lag
        # TEST : when you drag one of the twins (brown and green rects at the application top), a RecursiveError is raised

        Scene.__init__(self)#, size=(400, 400))

        self.set_mode(pygame.RESIZABLE)

        # CORNERS
        z = Zone(self, origin=Origin(pos=(10, -10), location="bottom", reference_location="bottom", locked=True),
                 size=(100, 100), background_color=(0, 64, 64), name="bottom")
        Dragable.set_dragable(z)
        z = Zone(self, origin=Origin(pos=(-10, -10), location="bottomright", reference_location="bottomright"),
                 size=(100, 100), background_color=(10, 54, 54), name="bottomright")
        Dragable.set_dragable(z)

        # PRISONNER
        z = Zone(self, origin=Origin(pos=(-10, 10), location="right", reference_location="right"),
                 size=(100, 100), background_color=(0, 64, 64), name="right")
        Dragable.set_dragable(z)
        b = Border(self, origin=Origin(pos=(7, 7), reference_comp=self),
                   color=(0, 108, 108), size=(100, 100), width=3, surrounding=True)
        wb = Border(z, origin=Origin(pos=("50%", "50%"), location="center"),
                    size=[z.w-20]*2,
                    surrounding=True, color=(0, 0, 0), width=1)
        r = Rectangle(z, (0, 128, 128), (30, 30), origin=Origin(pos=b.center, location="center", reference_comp=self))
        Dragable.set_dragable(r)
        r.set_window(wb.interior)

        # TODO : tester from_hitbox

        # CLOCK
        z2 = Zone(self, origin=Origin(pos=("-50%", 100), location="midtop", reference_location="topright"),
                  size=(350, 350), background_color=(140, 140, 140), name="z3")
        Dragable.set_dragable(z2)
        z3 = Zone(z2, origin=Origin(pos=(0, 0), location="center", reference_location="center"),
                  size=(250, 250), background_color=(150, 150, 150), name="z2")
        Dragable.set_dragable(z3)
        ref = Rectangle(z3, origin=Origin(pos=("50%", "50%"), location="center", reference_comp=self),
                        color=(128, 128, 0), size=(30, 30), name="ref")
        Dragable.set_dragable(ref)
        import math
        radius = 100
        step = int(math.degrees((2*math.pi)/8))
        for i in range(0, int(math.degrees(2*math.pi)), step):
            r = Rectangle(z2, color=ref.color, size=ref.size,
                        origin=Origin(pos=(math.cos(math.radians(i)) * radius,
                                         math.sin(math.radians(i)) * radius),
                                    reference_comp=ref), name="rect({})".format(i))
        for i in range(0, int(math.degrees(2*math.pi)), step):
            i += step / 2
            r = Rectangle(z3, color=(150, 120, 0), size=ref.size,
                        origin=Origin(pos=(math.cos(math.radians(i)) * radius,
                                         math.sin(math.radians(i)) * radius),
                                    reference_comp=ref), name="rect({})".format(i))

        # TWINS
        r1 = Rectangle(self, pos=("50%", 0),                                    color=(100, 50, 25), size=(30, 30), name="r1")
        r2 = Rectangle(self, origin=Origin(pos=(40, 0), reference_comp=r1), color=(50, 100, 25), size=(30, 30), name="r2")
        r3 = Rectangle(self, origin=Origin(pos=(0, 40), reference_comp=r2),  color=(100, 50, 25), size=(30, 30), name="r3")
        r4 = Rectangle(self, origin=Origin(pos=(-40, 0), reference_comp=r3), color=(50, 100, 25), size=(30, 30), name="r4")
        r1.origin.config(pos=(0, -40), reference_comp=r4)
        Dragable.set_dragable(r1)
        Dragable.set_dragable(r2)
        Dragable.set_dragable(r3)
        Dragable.set_dragable(r4)
        r0 = Rectangle(self, origin=Origin(pos=("50%", "50%"), reference_comp=r1), color=(75, 75, 25), size=(40, 40))
        r0.move_behind(r1)

        # CROSS
        c1 = Rectangle(self, (0, 0, 0), size=(6, 20),
                       origin=Origin(pos=(0, 0), location="center", reference_location="center"))
        c2 = Rectangle(self, (0, 0, 0), size=(20, 6),
                       origin=Origin(pos=(0, 0), location="center", reference_location="center"))


if __name__ == "__main__":
    UT_Origin_Scene()
    launch()
