from baopig import *


class ThemePresentator(Zone, Selector):
    STYLE = Zone.STYLE.substyle()
    STYLE.modify(
        background_color="theme-color-scene_background",
    )

    def __init__(self, parent, theme):
        Zone.__init__(self, parent, theme=theme, size=("100%", 200))
        Selector.__init__(self, parent)
        Layer(self, padding=10, children_margins=10)

        def click():
            ColorChooserDialog(self.application, one_shot=True, theme=self.theme.subtheme()).open()

        Button(self, text="Dialog", command=click)
        Text(self, text="lambda")
        TextEdit(self, text="lambda text in a TextEdit, can you see the ScrollSlider ?", height=40, width=350)
        Slider(self, minval=0, maxval=10, step=1)
        CheckBox(self, "lambda")

        self.pack()


class UT_Theme_Zone(Zone):

    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        sv = ScrollView(self, size=("100%", "100%"))
        z = Zone(sv, width="100%", padding=(0, 10), children_margins=(0, 10))

        ThemePresentator(z, theme="default")
        ThemePresentator(z, theme="dark")
        ThemePresentator(z, theme="pinky")
        ThemePresentator(z, theme="green")

        z.pack(adapt=True)


# For the PresentationScene import
ut_zone_class = UT_Theme_Zone

if __name__ == "__main__":
    from baopig.prefabs.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
