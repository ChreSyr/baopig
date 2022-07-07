from baopig import *


class RainbowRect(Rectangle, Runable):
    def __init__(self, parent, **kwargs):
        self.paint_calls = 0
        Rectangle.__init__(self, parent, color=(255, 0, 0), **kwargs)
        Runable.__init__(self, parent)
        self.console = None

    def handle_startrunning(self):
        self.console.set_text(self.console.text + "\nMethod called : handle_startrunning")
        self.console.parent.pack(adapt=True)

    def handle_stoprunning(self):
        self.console.set_text(self.console.text + "\nMethod called : handle_stoprunning")
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
        Button(buttons_zone, text="start running", command=rainbow.start_running)
        Button(buttons_zone, text="stop running", command=rainbow.stop_running)
        buttons_zone.pack(axis="horizontal", adapt=True)
        rainbow.resize(*buttons_zone.size)
        rainbow.console = Text(z1, text="Console:", width=rainbow.w)
        z1.pack(adapt=True)

    def load_sections(self):
        self.parent.add_section(
            title="Paintable.start_running() & Paintable.stop_running()",
            tests=[
                "After start_running(), the Runable is running",
                "After stop_running(), the Runable is stopped",
            ]
        )
        self.parent.add_section(
            title="Handlers",
            tests=[
                "When a Runable starts to run, the method handle_startrunning() is called",
                "When a Runable is stopped, the method handle_stoprunning() is called",
            ]
        )


# For the PresentationScene import
ut_zone_class = UT_Runable_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene

    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
