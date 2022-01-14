
from baopig import *


class UT_Focusable_Frame(Zone):
    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        class PosButton(Button):
            def __init__(self, parent, pos):
                Button.__init__(self, parent, pos=pos, text="({}, {})".format(*pos))

        b1 = PosButton(self, pos=(10, 10))
        b0 = PosButton(self, pos=(10, 45))
        b0 = PosButton(self, pos=(80, 10))
        b2 = PosButton(self, pos=(80, 45))
        b0 = PosButton(self, pos=(10, 80))
        b0 = PosButton(self, pos=(80, 80))
        Dragable.set_dragable(b0)

        z = Zone(self, pos=(-5, 5), sticky="topright",
                 size=(self.w-155, self.h-10), background_color=(10, 30, 20, 128))
        import random
        for i in range(10):
            x = random.randrange(z.w - b0.w)
            y = random.randrange(z.h - b0.h)
            PosButton(z, pos=(x, y))

ut_scenes = [
    UT_Focusable_Frame,
]


if __name__ == "__main__":
    from baopig.unit_tests.TesterScene import TesterScene
    app = Application()
    for scene in ut_scenes:
        TesterScene(app, scene)
    app.launch()
