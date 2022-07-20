
from baopig import *


class UT_TextEdit_Zone(Zone):

    def __init__(self, *args, **kwargs):

        Zone.__init__(self, *args, **kwargs)

        z1 = Zone(self, pos=(10, 10), size=(int(self.rect.w / 2) - 15, 150),
                  background_color=(100, 100, 100, 50))
        z2 = Zone(self, pos=(z1.rect.right + 10, 10), size=(int(self.rect.w / 2) - 15, 150),
                  background_color=(100, 100, 100, 50))
        z3 = Zone(self, pos=(10, z1.rect.bottom + 10), size=(int(self.rect.w / 3) - 20, 120),
                  background_color=(100, 100, 100, 50), padding=5, children_margins=2)
        z4 = Zone(self, pos=(z3.rect.right + 10, z1.rect.bottom + 10), size=(int(self.rect.w / 3) - 20, 120),
                  background_color=(100, 100, 100, 50), padding=5, children_margins=2)

        z1.mirrored = TextEdit(z1, text="0123456789012345", max_width=40, pos=(10, 10), size=(100, 120))
        z1.d = DynamicText(z1, z1.mirrored.text_widget.get_text, pos=z1.mirrored.rect.topright)

        text = TextEdit(z2, max_width=z2.rect.w - 20, pos=(10, 10), size=(z2.rect.w - 20, 120))

        Button(z2, text="RUN", sticky="topright", ref=text, command=lambda: exec(text.text), catching_errors=True)

        # Z3
        LineEdit(z3)
        LineEdit(z3, width=190, padding=5, font_height=30)
        z3.pack()

        # Z4
        Entry(z4, entry_type=int)
        Entry(z4, entry_type=float)
        Entry(z4, entry_type=str)
        NumEntry(z4, min=0, max=10, accept_floats=True, default=5)
        z4.pack()

# For the PresentationScene import
ut_zone_class = UT_TextEdit_Zone

if __name__ == "__main__":
    from baopig.prefabs.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
