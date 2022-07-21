
from baopig import *


class UT_Focusable_Zone(Zone):
    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        class PosButton(Button):
            def __init__(self, parent, pos):
                Button.__init__(self, parent, pos=pos, text="({}, {})".format(*pos))

        PosButton(self, pos=(10, 10))
        PosButton(self, pos=(10, 45))
        PosButton(self, pos=(80, 10))
        PosButton(self, pos=(80, 45))
        PosButton(self, pos=(10, 80))
        b0 = PosButton(self, pos=(80, 80))

        z = Zone(self, pos=(-5, 5), sticky="topright",
                 size=(self.rect.w - 155, self.rect.h - 10), background_color=(10, 30, 20, 128))
        import random
        for i in range(10):
            x = random.randrange(z.rect.w - b0.rect.w)
            y = random.randrange(z.rect.h - b0.rect.h)
            PosButton(z, pos=(x, y))


# For the PresentationScene import
ut_zone_class = UT_Focusable_Zone

if __name__ == "__main__":
    from baopig.prefabs.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
