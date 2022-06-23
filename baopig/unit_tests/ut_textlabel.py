
from baopig import *


class UT_TextLabel_Zone(Zone):
    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        Button(self, "Click", pos=(150, 10), height=100)
        TextLabel(self, "Hello\nHow are you dear ?", background_color="yellow", pos=(10, 10),
                  width=100, height=200, align_mode="center")
        self.set_style_for(Text, max_width=100)
        TextLabel(self, "Hello\nHow are you dear ?", background_color="yellow", pos=(10, 220),
                  width=100, height=200, align_mode="center")


# For the PresentationScene import
ut_zone_class = UT_TextLabel_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
