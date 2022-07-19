import random

from baopig import *


class UT_LayerPack_Zone(Zone):

    def __init__(self, *args, **kwargs):

        Zone.__init__(self, *args, **kwargs)

        classiclayer_tester = Zone(self, size=("100%", "50%"), name="classiclayer_tester")
        safe_layer = Layer(classiclayer_tester, Button, name="safe_layer")
        self.package = Zone(classiclayer_tester, padding=10, children_margins=5, pos=(0, 35), size=(300, 300),
                            background_color=(90, 90, 80))
        Layer(self.package)

        def add():
            zone = Zone(self.package, name="zone", background_color="green4", padding=3, children_margins=3,
                        pos=(random.randint(0, 200), random.randint(0, 200)))
            Rectangle(parent=zone, color=(255, 255, 0), size=(zone.rect.w, 10), pos=(0, 0), name="Cobaye")
            Text(zone, f"layer's length : {len(self.package.default_layer)}")
            Button(zone, "REMOVE", command=zone.kill)
            zone.default_layer.pack()
            zone.adapt(zone.default_layer)

        Button(classiclayer_tester, "ADD", command=add)
        b = Button(classiclayer_tester, "PACK", command=self.package.pack)
        b.set_window((b.rect.left, b.rect.top, b.rect.w, 20),
                     follow_movements=True)  # TODO : remove, here for some tests
        Indicator(b, "NOTE : By default, pack() sorts widgets by position", loc="bottom", max_width=200)
        Button(classiclayer_tester, "CLEAR", command=self.package.default_layer.clear)
        safe_layer.pack(axis="horizontal")
        Text(classiclayer_tester, pos=(330, 10), text="Testing Layer.pack()", font_height=30)

        s = Slider(classiclayer_tester, pos=(330, 80), step=1, minval=0, maxval=100, title="padding.left",
                   defaultval=self.package.padding.left, printed_title=True, length=150, wideness=15)

        def new_padding(val):
            self.package.padding._left = val

        s.signal.NEW_VAL.connect(new_padding, owner=None)

        s = Slider(classiclayer_tester, pos=(330, 120), step=1, minval=0, maxval=100, title="children_margins.top",
                   defaultval=self.package.children_margins.top, printed_title=True, length=150, wideness=15)

        def new_childrenmargins_top(val):
            self.package.children_margins._top = val

        s.signal.NEW_VAL.connect(new_childrenmargins_top, owner=None)

        s = Slider(classiclayer_tester, pos=(330, 160), step=1, minval=0, maxval=100, title="children_margins.bottom",
                   defaultval=self.package.children_margins.bottom, printed_title=True, length=150, wideness=15)

        def new_childrenmargins_bottom(val):
            self.package.children_margins._bottom = val

        s.signal.NEW_VAL.connect(new_childrenmargins_bottom, owner=None)
        Text(classiclayer_tester, "NOTE : Only children_margins.top and children_margins.left are being used",
             max_width=self.rect.w - s.rect.right - 10, ref=s, refloc="midright", midleft=(10, 0))

        # GRID TESTING
        gridlayer_tester = Zone(self, size=("100%", "50%"))
        self.default_layer.pack()
        safe_layer2 = Layer(gridlayer_tester, Button, name="safe_layer")
        self.package2 = Zone(gridlayer_tester, padding=10, children_margins=5, pos=(0, 35), size=(300, 300),
                             background_color=(90, 90, 80))
        GridLayer(self.package2, nbrows=10, nbcols=10)

        def add():

            for i in range(10):

                if len(self.package2.children) == 81:
                    return

                searching = True
                x, y = 0, 0
                while searching:
                    x = random.randint(0, 8)
                    y = random.randint(0, 8)
                    if self.package2.default_layer.get_data(x, y) is None:
                        searching = False

                z = Zone(parent=self.package2, row=x, col=y, background_color="yellow4", size=(30, 30))
                Text(z, f"{x}, {y}", size=(30, 30))

        Button(gridlayer_tester, "ADD", command=add)
        Button(gridlayer_tester, "PACK", command=self.package2.pack)
        Button(gridlayer_tester, "CLEAR", command=self.package2.default_layer.clear)
        safe_layer2.pack(axis="horizontal")
        Text(gridlayer_tester, pos=(310, 10), text="Testing GridLayer.pack()", font_height=30)

        sliders_layer = Layer(gridlayer_tester, children_margins=25)
        s = Slider(gridlayer_tester, layer=sliders_layer, step=1, minval=0, maxval=100, title="padding.left",
                   defaultval=self.package2.padding.left, printed_title=True, length=150, wideness=15)
        def new_paddingleft(val):
            self.package2.padding._left = val
        s.signal.NEW_VAL.connect(new_paddingleft, owner=None)

        s = Slider(gridlayer_tester, layer=sliders_layer, step=1, minval=0, maxval=100, title="padding.top",
                   defaultval=self.package2.padding.top, printed_title=True, length=150, wideness=15)
        def new_paddingtop(val):
            self.package2.padding._top = val
        s.signal.NEW_VAL.connect(new_paddingtop, owner=None)

        s = Slider(gridlayer_tester, layer=sliders_layer, step=1, minval=0, maxval=100, title="children_margins.left",
                   defaultval=self.package2.children_margins.left, printed_title=True, length=150, wideness=15)
        def new_childrenmargins_left(val):
            self.package2.children_margins._left = val
        s.signal.NEW_VAL.connect(new_childrenmargins_left, owner=None)

        s = Slider(gridlayer_tester, layer=sliders_layer, step=1, minval=0, maxval=100, title="children_margins.top",
                   defaultval=self.package2.children_margins.top, printed_title=True, length=150, wideness=15)
        def new_childrenmargins_top(val):
            self.package2.children_margins._top = val
        s.signal.NEW_VAL.connect(new_childrenmargins_top, owner=None)

        sliders_layer.pack(start_pos=(330, 80))


# For the PresentationScene import
ut_zone_class = UT_LayerPack_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
