

from baopig import *


class UT_ColorChooserDialog_Zone(Zone):
    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        colorchooser = ColorChooserDialog(self.application)
        text = Text(self, "Color : None", pos=(10, 40))
        colorchooser.signal.ANSWERED.connect(lambda color: text.set_text("Color : " + str(color)), owner=None)
        b = Button(self, "Wich color ?", sticky="top", command=colorchooser.open)


ut_zones = [
    UT_ColorChooserDialog_Zone,
]

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    for scene in ut_zones:
        TesterScene(app, scene)
    app.launch()
