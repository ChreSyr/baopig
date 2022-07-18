from baopig import *


class RainbowRect(Rectangle, Runable):
    def __init__(self, parent, **kwargs):
        self.paint_calls = 0
        Rectangle.__init__(self, parent, color=(255, 0, 0), **kwargs)
        Runable.__init__(self, parent)
        self.console = None

    def set_running(self, val):

        if val == self.is_running:
            return

        super().set_running(val)

        if self.is_running:
            self.console.set_text(self.console.text + "\nMethod called : set_running(True)")
        else:
            self.console.set_text(self.console.text + "\nMethod called : set_running(False)")
        self.console.parent.pack(adapt=True)

    def paint(self):
        self.color.set_hue(self.paint_calls)
        super().paint()

    def run(self):
        self.paint_calls = (self.paint_calls + .003) % 360
        self.send_paint_request()


class UT_Runable_Zone(Zone):
    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        Layer(self, name="zones_layer", children_margins=10)
        z1 = Zone(self, background_color=(150, 150, 150), padding=10, children_margins=10)
        self.default_layer.pack()

        rainbow = RainbowRect(z1)
        buttons_zone = Zone(z1, children_margins=10)
        buttons_zone.set_style_for(Button, width=200)
        Button(buttons_zone, text="start running", command=PrefilledFunction(rainbow.set_running, True))
        Button(buttons_zone, text="stop running", command=PrefilledFunction(rainbow.set_running, False))
        buttons_zone.pack(axis="horizontal", adapt=True)
        rainbow.resize(*buttons_zone.rect.size)
        rainbow.console = Text(z1, text="Console:", max_width=rainbow.rect.w)
        z1.pack(adapt=True)

    def load_sections(self):
        self.parent.add_section(
            title="Paintable.set_running()",
            tests=[
                "After set_running(True), the Runable is running",
                "After set_running(False), the Runable is stopped",
            ]
        )


# For the PresentationScene import
ut_zone_class = UT_Runable_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene

    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
