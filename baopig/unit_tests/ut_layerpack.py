import random

from baopig import *


class UT_LayerPack_Zone(Zone, Focusable):

    def __init__(self, *args, **kwargs):

        Zone.__init__(self, *args, **kwargs)
        Focusable.__init__(self)

        self.handle_defocus()  # Set a new background color
        self.package = Layer(self, name="package_layer")
        def pack_package():
            self.package.pack(padding=10, children_margins=5)
        Layer(self, name="safe_layer")

        t = Text(self, "Click on the gray zone, then use your keyboard\n"
                       " ---\n"
                       "'a' : Create a zone with a bunch of components\n"
                       "SPACE : Delete the oldest component\n"
                       "Maj + SPACE : Delete the oldest zone",
                 pos=(0, 0), pos_location="topright", pos_ref_location="topright",
                 layer="safe_layer")
        b = Button(self, "PACK", pos=t.bottomleft, command=pack_package, layer="safe_layer")

    def handle_defocus(self):

        self.set_background_color((90, 90, 80))

    def handle_focus(self):

        self.set_background_color((160, 137, 80))

    def handle_keydown(self, key):

        if key == keyboard.SPACE:
            if self.package:
                if keyboard.mod.maj:
                    self.package[0].kill()
                elif True:
                    self.package[-1].kill()
        elif key == keyboard.f:
            import gc
            gc.collect()
            LOGGER.info("Garbage collected")
        elif key == keyboard.a:
            zone = Zone(self, name="zone", background_color="green4", padding=3, children_margins=3,
                        pos=(random.randint(0, 200), random.randint(0, 200)))
            Rectangle(parent=zone, color=(255, 255, 0), size=(zone.w, 10), pos=(0, 0), name="Cobaye")
            Text(zone, f"padding:{zone.padding}", max_width=200)
            Text(zone, f"children_margins:{zone.children_margins}", max_width=200)
            Text(zone, f"This zone's layer's length : {len(self.package)}")
            Text(zone, " ")
            Text(zone, " ")
            Button(zone, "REMOVE", command=zone.kill)
            zone.default_layer.pack()
            zone.adapt(zone.default_layer)


# For the PresentationScene import
ut_zone_class = UT_LayerPack_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
