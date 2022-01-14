

from baopig import *


class UT_Scrollable(Zone):
    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)
        self.set_style_for(Button, height=20)

        scroller = ScrollableZone(
            self, (200, 140), pos=(10, 50), background_color="gray", size=(400, 1000))
        # scroller.set_indicator("Scroller")
        import string
        i = 0
        for h in range(10, 1000, 60):
            b = Button(scroller, pos=(10, h), text=string.ascii_letters[i], padding = 0)
            i += 1
            b.set_indicator("Empty")
            def cut():
                scroller.scrollsliders[0].width -= 20
            if h == 10:
                b.command = cut
            else:
                b.command = lambda: scroller.set_window(scroller.window[:2] + (300, 140))


ut_scenes = [
    UT_Scrollable,
]


if __name__ == "__main__":
    from baopig.unit_tests.TesterScene import TesterScene
    app = Application()
    for scene in ut_scenes:
        TesterScene(app, scene)
    app.launch()

