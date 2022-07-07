
from baopig import *


class UT_TextEdit_Zone(Zone):

    def __init__(self, *args, **kwargs):

        Zone.__init__(self, *args, **kwargs)

        self.zone1 = Zone(self, pos=(10, 10), size=(self.w / 2 - 15, self.h - 20), background_color=(100, 100, 100, 50))
        self.zone2 = Zone(self, pos=(self.zone1.right + 10, 10), size=(self.w / 2 - 15, self.h - 20),
                          background_color=(100, 100, 100, 50))

        self.zone1.mirrored = TextEdit(self.zone1, text="0123456789012345", width=40, pos=(10, 10))
        self.zone1.d = DynamicText(self.zone1, self.zone1.mirrored.get_text, pos=self.zone1.mirrored.topright)

        text = TextEdit(self.zone2, width=self.zone2.w - 20, pos=(10, 10))

        self.b = Button(self.zone2, text="RUN", topright=text.topright, command=lambda: exec(text.text),
                        catching_errors=True)
        text.signal.RESIZE.connect(lambda: self.b.origin.config(pos=text.topright), owner=self.b)
        text.signal.MOTION.connect(lambda: self.b.origin.config(pos=text.topright), owner=self.b)


# For the PresentationScene import
ut_zone_class = UT_TextEdit_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
