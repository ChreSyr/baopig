
from baopig import *
from baopig.prefabs.colorchooserdialog import ColorChooserDialog


class UT_ColorChooserDialog_Zone(Zone):
    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        colorchooser = ColorChooserDialog(self.application)
        Button(self, "Wich color ?", sticky="midtop", pos=(0, 10), command=colorchooser.open)
        text = Text(self, "Color : None", sticky="midtop", pos=(0, 60))
        colorchooser.signal.ANSWERED.connect(lambda color: text.set_text("Color : " + str(color)), owner=None)


# For the PresentationScene import
ut_zone_class = UT_ColorChooserDialog_Zone

if __name__ == "__main__":
    from baopig.prefabs.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class).open()
    app.launch()
