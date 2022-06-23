
from baopig import *


class UT_TextEdit_Zone(Zone):

    def __init__(self, *args, **kwargs):

        Zone.__init__(self, *args, **kwargs)

        self.zone1 = Zone(self, pos=(10, 10), size=(self.w / 2 - 15, self.h - 20), background_color=(100, 100, 100, 50))
        # print(self.zone1)
        self.zone2 = Zone(self, pos=(self.zone1.right + 10, 10), size=(self.w / 2 - 15, self.h - 20), background_color=(100, 100, 100, 50))

        self.zone1.mirrored = TextEdit(self.zone1, text="0123456789012345", width=40, pos=(10, 10))
        self.zone1.d = DynamicText(self.zone1, self.zone1.mirrored.get_text, pos=self.zone1.mirrored.topright)

        text = TextEdit(self.zone2, width=self.zone2.w - 20, pos=(10, 10))

        self.b = Button(self.zone2, text="RUN", pos=text.topright, command=lambda: exec(text.text), catching_errors=True)
        self.b.origin.config(location="topright")
        text.signal.RESIZE.connect(lambda: self.b.origin.config(pos=text.topright), owner=self.b)
        text.signal.MOTION.connect(lambda: self.b.origin.config(pos=text.topright), owner=self.b)


        scrap = \
            "f = application.focused_scene\n" \
            "c = f.children\n" \
            "b = Button(application.focused_scene, 'HELLO WORLD', command=lambda: print('Hello world'))\n" \
            "Dragable.set_dragable(b)\n" \
            "b2 = b.copy()\n" \
            "Dragable.set_dragable(b2)\n" \
            ""[:-1]
        scrap = \
            "fr = application.focused_scene\n" \
            "et = fr.zone2.default_layer[0]\n" \
            "font = et.font\n" \
            "for i in range(2, 30):\n" \
            "   font.config(height=i)\n" \
            ""[:-1]
        clipboard.put(scrap)


# For the PresentationScene import
ut_zone_class = UT_TextEdit_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()