

from baopig import *


class UT_Container_pack_Scene(Scene):

    def __init__(self):

        Scene.__init__(self)
        self.set_mode(pygame.RESIZABLE)
        Layer(self, "safe_layer")
        self.package = Layer(self, "package_layer")
        # self.add_layer("safe_layer")
        # self.package = self.default_layer

        t = Text(self, "'a' : Create a zone with a bunch of components\n"
                       "SPACE : Delete the oldest component\n"
                       "Maj + SPACE : Delete the oldest zone",
                 origin=Origin(pos=(0, 0), location="topright", reference_location="topright"),
                 layer="safe_layer")
        b = Button(self, "PACK", pos=t.bottomleft, command=self.package.sort, layer="safe_layer")
        # b.swap_layer("front_layer")

        def space(*args):
            if self.package:
                if keyboard.mod.maj:
                    self.package[0].kill()
                elif self.package[0].package:
                    self.package[0].package[0].kill()
                    # print(self.package[0].children)
                    if not self.package[0].package:
                        self.package[0].kill()
        self.handle_keydown[keyboard.SPACE].add(space)

        def free(*args):
            import gc
            gc.collect()
        self.handle_keydown[keyboard.f].add(free)

        def plus(*args):
            zone = Zone(self, name="zone")
            Rectangle(parent=zone, color=(255, 255, 0), size=(10, 10), pos=(0, 0), name="Cobaye")
            Text(zone, "1")
            Text(zone, "2")
            Text(zone, "3")
            Button(zone, "Hi")
            zone.default_layer.sort()
            self.package.pack(adapt=False)
            # print(zone.children)
        self.handle_keydown[keyboard.a].add(plus)


if __name__ == "__main__":
    UT_Container_pack_Scene()
    launch()
