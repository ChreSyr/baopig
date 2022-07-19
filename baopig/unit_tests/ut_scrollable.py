

from baopig import *


class UT_Scrollable_Zone(Zone):
    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        self.set_style_for(Button, height=20)
        lay = Layer(self, padding=10, children_margins=10)

        TextEdit(self, text="Bonjour tout le monde.\n\n\n\n\n\n\n\n\n\n\nHello\n\n\n\nHello 2",
                 size=(300, 200), background_color="pink")
        Button(self)

        lay.pack()


# For the PresentationScene import
ut_zone_class = UT_Scrollable_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
