

from baopig import *


class UT_TextLabel_Zone(Zone):
    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        label = TextLabel(self, "Hello\nHow are you dear ?", background_color="yellow", pos=(10, 10),
                          width=100, height=200, align_mode="center")
        Button(self, "Click", pos=(120, 10), height=100)


ut_zones = [
    UT_TextLabel_Zone,
]


if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    for scene in ut_zones:
        TesterScene(app, scene)
    app.launch()

