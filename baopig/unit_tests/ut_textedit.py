
from baopig import *


class UT_TextEdit_Zone(Zone):

    def __init__(self, *args, **kwargs):

        Zone.__init__(self, *args, **kwargs)

        self.zone1 = Zone(self, pos=(10, 10), size=(int(self.rect.w / 2) - 15, self.rect.h - 20),
                          background_color=(100, 100, 100, 50))
        self.zone2 = Zone(self, pos=(self.zone1.rect.right + 10, 10),
                          size=(int(self.rect.w / 2) - 15, self.rect.h - 20), background_color=(100, 100, 100, 50))

        self.zone1.mirrored = TextEdit(self.zone1, text="0123456789012345", max_width=40, pos=(10, 10))
        self.zone1.d = DynamicText(self.zone1, self.zone1.mirrored.get_text, pos=self.zone1.mirrored.rect.topright)

        text = TextEdit(self.zone2, max_width=self.zone2.rect.w - 20, pos=(10, 10))

        self.b = Button(self.zone2, text="RUN", sticky="topright", ref=text,
                        command=lambda: exec(text.text), catching_errors=True)


# For the PresentationScene import
ut_zone_class = UT_TextEdit_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
