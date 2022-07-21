
from baopig import *


class UT_Button_Zone(Zone):
    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        layer = Layer(self, spacing=10)
        z1 = Zone(self, size=("100%", 60), background_color=(150, 150, 150), spacing=5, padding=5)
        z2 = Zone(self, size=("100%", 100), background_color=(150, 150, 150), spacing=5, padding=5)
        z3 = Zone(self, size=("100%", 500), background_color=(150, 150, 150))
        layer.pack()

        # Z1
        class MyButton(Button):
            def handle_validate(self):
                super().handle_validate()
                t.set_text(f"You clicked on : {self.text}")

        MyButton(z1, "Hello world")
        MyButton(z1, "Dlrow olleh")
        b = Button(z1, "Other way")
        Button(z1, "Console print", command=PrefilledFunction(print, "Hello world from 'Console print' Button"))
        t = Text(z1)
        b.command = PrefilledFunction(t.set_text, f"You clicked on : {b.text}")
        z1.pack(axis="horizontal")

        # Z2
        GridLayer(z2)
        z2.set_style_for(Button, padding=0)
        Button(z2, "l1", row=0, col=0)
        Button(z2, "l1\nl2\nl3", row=0, col=1)
        Button(z2, "-----------l1-----------", row=0, col=2)
        Text(z2, text=f"padding:{z2.get_style_for(Button)['padding']}", row=0, col=3)
        z2.set_style_for(Button, padding=13)
        Button(z2, "l1", row=1, col=0)
        Button(z2, "l1\nl2", row=1, col=1)
        Button(z2, "-----------l1-----------", row=1, col=2)
        Text(z2, text=f"padding:{z2.get_style_for(Button)['padding']}", row=1, col=3)
        z2.pack()

        # Z3
        class PosButton(Button):
            def __init__(self, parent, pos):
                Button.__init__(self, parent, pos=pos, text="({}, {})".format(*pos))

        import random
        width = Button.STYLE["width"]
        height = Button.STYLE["height"]
        for i in range(10):
            x = random.randrange(z3.rect.w - width)
            y = random.randrange(z3.rect.h - height)
            PosButton(z3, pos=(x, y))


# For the PresentationScene import
ut_zone_class = UT_Button_Zone

if __name__ == "__main__":
    from baopig.prefabs.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
