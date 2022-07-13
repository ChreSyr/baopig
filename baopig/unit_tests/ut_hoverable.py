from baopig import *


class HoverableRectangle(Rectangle, HoverableByMouse):
    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        color="blue"
    )

    def __init__(self, parent, **kwargs):
        Rectangle.__init__(self, parent, **kwargs)

        self.is_main = True  # needed in HoverableByMouse.__init__()
        HoverableByMouse.__init__(self, parent)

    def handle_hover(self):
        self.set_color("yellow" if self.is_main else "yellow4")

    def handle_unhover(self):
        self.set_color("blue" if self.is_main else "blue4")

    def set_main(self, val):
        self.is_main = val
        if self.is_hovered:
            self.handle_hover()
        else:
            self.handle_unhover()


class TestingZone(Zone, Focusable):

    def __init__(self, parent, **kwargs):
        Zone.__init__(self, parent, **kwargs)
        Focusable.__init__(self, parent)
        self._controlled_ref = lambda: None
        self.highlighter = Highlighter(self, target=self, visible=False, border_width=4)

    controlled = property(lambda self: self._controlled_ref())

    def handle_defocus(self):
        self.highlighter.hide()

    def handle_focus(self):
        self.highlighter.show()

    def handle_keydown(self, key):

        if key == pygame.K_a:
            if self.controlled is not None:
                self.controlled.set_main(False)
            self._controlled_ref = HoverableRectangle(self, sticky="center").get_weakref()

        elif self.controlled is None:
            return
        vel = 5
        if self.controlled.is_awake:
            if key == pygame.K_LEFT:
                self.controlled.move(dx=-vel)
            elif key == pygame.K_RIGHT:
                self.controlled.move(dx=vel)
            elif key == pygame.K_UP:
                self.controlled.move(dy=-vel)
            elif key == pygame.K_DOWN:
                self.controlled.move(dy=vel)

        if key == pygame.K_s:
            self.controlled.show()
        elif key == pygame.K_h:
            self.controlled.hide()

        elif key == pygame.K_w:
            self.controlled.wake()
        elif key == pygame.K_l:
            self.controlled.sleep()

        elif key == pygame.K_k:
            self.controlled.kill()
            last_child = self.default_layer[-1]
            if last_child != self.highlighter:
                self._controlled_ref = last_child.get_weakref()
                self.controlled.set_main(True)

        elif key == pygame.K_r:
            if self.controlled.w == 30:
                self.controlled.resize(40, 40)
            elif self.controlled.w == 40:
                self.controlled.resize(20, 20)
            else:
                self.controlled.resize(30, 30)

        elif key == pygame.K_n:
            self.controlled.set_touchable_by_mouse(False)  # TODO : tests


class UT_Hoverable_Zone(Zone):
    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        Layer(self, name="zones_layer", children_margins=10)
        z1 = Zone(self, size=(90, 50), background_color=(150, 150, 150), padding=10, children_margins=10)
        z2 = Zone(self, size=("100%", 250))
        self.default_layer.pack()

        # Z1
        hr = HoverableRectangle(z1)
        light = Rectangle(z1, color="black")
        hr.signal.HOVER.connect(lambda: light.set_color("red3"), owner=light)
        hr.signal.UNHOVER.connect(lambda: light.set_color("black"), owner=light)
        z1.default_layer.pack(axis="horizontal")

        # Z2
        TestingZone(z2, size=("50%", "100%"), background_color=(150, 150, 150))
        text_zone = Zone(z2, size=("50%", "100%"))
        z2.default_layer.pack(axis="horizontal")
        Text(text_zone, width=text_zone.w,
             text="Focus the zone at left in order to use it with your keyboard.\n"
                  "Use the arrows to control the light blue rect\n"
                  "Press the following keys to execute actions over the light blue rect:\n"
                  " - a : Create a new widget\n"
                  " - s : Show the widget\n"
                  " - h : Hide the widget\n"
                  " - w : Wake up the widget\n"
                  " - l : Asleep the widget\n"
                  " - k : Kill the widget\n"
                  " - n : Set the widget non-touchable\n"
             )

    def load_sections(self):
        self.parent.add_section(
            title="mouse manages mouse.hovered_widget",
            tests=[
                "When the mouse moves, the hovered_widget is updated",
            ]
        )
        self.parent.add_section(
            title="HoverableByMouse can manage mouse.hovered_widget",
            tests=[
                "When a hovered HoverableByMouse disappears (hide, sleep, kill), it drops the hover",
                "When a hovered HoverableByMouse moves or get resized, if needed, it drops the hover",
                "When a HoverableByMouse appears (creation, show, wake), if needed, it gains the hover",
                "When a HoverableByMouse moves or get resized, if needed, it gains the hover",
            ]
        )
        self.parent.add_section(
            title="signal.HOVER & signal.UNHOVER",
            tests=[
                "When a HoverableByMouse is just hovered, the signal HOVER is emitted",
                "When a hovered HoverableByMouse is unhovered, the signal UNHOVER is emitted",
            ]
        )


# For the PresentationScene import
ut_zone_class = UT_Hoverable_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene

    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
