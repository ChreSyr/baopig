from baopig import *


class RainbowRect(Rectangle):
    def __init__(self, parent, **kwargs):
        self.paint_calls = 0
        Rectangle.__init__(self, parent, color=(255, 0, 0), **kwargs)

    def paint(self):
        self.paint_calls = (self.paint_calls + 3) % 360
        self.color.set_hue(self.paint_calls)
        super().paint()


class UT_Paintable_Zone(Zone):
    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        Layer(self, name="zones_layer", children_margins=10)
        z1 = Zone(self, background_color=(150, 150, 150), padding=10, children_margins=10)
        self.default_layer.pack()

        rainbow = RainbowRect(z1)
        buttons_zone = Zone(z1, children_margins=10)
        Button(buttons_zone, text="dirty = 0", command=PrefilledFunction(rainbow.set_dirty, 0))
        Button(buttons_zone, text="dirty = 1", command=PrefilledFunction(rainbow.set_dirty, 1))
        Button(buttons_zone, text="dirty = 2", command=PrefilledFunction(rainbow.set_dirty, 2))
        Button(buttons_zone, text="paint request", command=rainbow.send_paint_request)
        buttons_zone.pack(axis="horizontal", adapt=True)
        rainbow.resize(*buttons_zone.size)
        z1.pack(adapt=True)

    def load_sections(self):
        self.parent.add_section(
            title="Paintable.set_dirty()",
            tests=[
                "if dirty is 0, paint() is not requested",
                "if dirty is 1, paint() is called at next frame rendering, then dirty will be set to 0 again",
                "if dirty is 2, paint() is called at each frame rendering",
            ]
        )
        self.parent.add_section(
            title="Paintable.send_paint_request()",
            tests=[
                "if dirty was 0, paint() is called at next frame rendering, then dirty will be set to 0 again",
            ]
        )


# For the PresentationScene import
ut_zone_class = UT_Paintable_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene

    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
