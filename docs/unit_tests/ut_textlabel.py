

from baopig import *


class UT_TextLabel(Zone):
    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        label = TextLabel(self, "Hello\nHow are you dear ?", background_color="yellow", pos=(10, 10),
                          width=100, height=200, align_mode="center")
        Button(self, "Click", pos=(120, 10), height=100)


ut_scenes = [
    UT_TextLabel,
]


if __name__ == "__main__":
    from baopig.unit_tests.TesterScene import TesterScene
    app = Application()
    for scene in ut_scenes:
        TesterScene(app, scene)
    app.launch()

