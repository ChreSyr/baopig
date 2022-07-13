

from baopig import *


class UT_Scrollable_Zone(Zone):
    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)
        self.set_style_for(Button, height=20)

        scroller = ScrollableZone(
            self, (200, 140), pos=(10, 50), background_color="gray", size=(400, 1000))
        import string
        i = 0
        for h in range(10, 1000, 60):
            b = Button(scroller, pos=(10, h), text=string.ascii_letters[i], padding=0)
            i += 1
            Indicator(b, "Empty")
            def cut():
                scrollslider = scroller.scrollsliders[0]
                scrollslider.resize_width(scrollslider.rect.w - 20)
            if h == 10:
                b.command = cut
            else:
                b.command = lambda: scroller.set_window(scroller.window[:2] + (300, 140))


# For the PresentationScene import
ut_zone_class = UT_Scrollable_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
