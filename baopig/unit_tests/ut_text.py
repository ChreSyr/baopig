from baopig import *


class UT_Text_Zone(Zone):

    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        Layer(self, name="zones_layer", spacing=10)
        z1 = Zone(self, size=("100%", 80), background_color=(150, 150, 150), spacing=5, padding=5)
        z2 = Zone(self, size=("100%", 98), background_color=(150, 150, 150), spacing=5, padding=5)
        sv = ScrollView(self, size=("100%", 300), background_color=(150, 150, 150), padding=5)
        z3 = Zone(sv, spacing=10)
        z4 = Zone(self, size=("100%", 120), background_color=(150, 150, 150), spacing=5, padding=5)
        z5 = Zone(self, size=("100%", 120), background_color=(150, 150, 150), spacing=5, padding=5)
        self.default_layer.pack()

        # Z1
        hello = Text(parent=z1, text="Hello world\nIamaverylongword,canyoureadmecorrectly?"
                                     "\nWhat do you want to do ?", max_width=250, padding=5)
        z1.set_style_for(Text, font_file="algerian", font_italic=True)
        Text(parent=z1, text="Hello world\nIamaverylongword,canyoureadmecorrectly?"
                             "\nWhat do you want to do ?", max_width=hello.rect.width)
        z1.pack(axis="horizontal")

        # Z2
        z2.set_style_for(Text, font_file="monospace")
        z2.set_style_for(Text, font_height=60)
        z2.set_style_for(Text, font_color=(0, 150, 0))
        text = Text(z2, max_width=300, font_height=11, font_file="arialrounded",
                    text="- Bonjour à tous.\n"
                         "- Bonjour monsieur. Comment allez-vous ?\n"
                         "- Très bien, merci. Nous allons commencer. \"L'hypoténuse et l'hippocampe "
                         "se préparaient à pique-niquer, lorsque...\"\n"
                         "- Monsieur, j'avais oublié, j'ai un rendez-vous !\n"
                         "- Eh bien, filez, ça ira pour cette fois.\n"
                         "- Merci monsieur !\n"
                         "Et il partit. (vert fonce)")
        text.set_background_color((255, 255, 255, 128))
        text.font.config(color=(10, 50, 30))
        TextEdit(z2, text="Green", size=text.rect.size, font_file="passeroone")
        z2.pack(axis="horizontal")

        # Z3
        def load_sys_fonts():
            calls_index = 1
            row = 0
            col = 0
            fonts_zone.set_pos(top=-1)  # placed before the button
            fonts_zone.set_style_for(Text, font_height=18)
            fonts_zone.set_style_for(Text, font_color=(0, 0, 0))
            for file in pygame.font.get_fonts():
                # if file.endswith("gras") or file.endswith("italic") or file.endswith("italique") \
                #         or file.endswith("oblique"):
                #     continue
                Text(fonts_zone, text=file[:-4] if file.endswith(".ttf") else file, font_file=file,
                     row=row, col=col)
                col += 1
                if col == 4:
                    col = 0
                    row += 1
                if row > 100 * calls_index:
                    fonts_zone.pack(adapt=True)
                    z3.pack(adapt=True)
                    calls_index += 1
                    yield "STILL FONTS LEFT"
            fonts_zone.pack(adapt=True)
            z3.pack(adapt=True)
            yield "DONE"

        load_sys_fonts_generator = load_sys_fonts()

        def preview_fonts():
            try:
                print(next(load_sys_fonts_generator))
            except StopIteration:
                pass

        self.b = Button(z3, "Click here to see more fonts provided by your OS", command=preview_fonts,
                        width=sv.content_rect.width)
        fonts_zone = Zone(z3, height=0)
        GridLayer(fonts_zone, nbcols=4, col_width=int(sv.rect.width / 4), spacing=(5, 2))
        z3.pack(adapt=True)

        # Z4
        Text(z4, "max_width:150", max_width=150)
        Text(z4, "max_width:75", max_width=75)
        Text(z4, "padding:5", padding=5)
        Text(z4, "1\n2\n3", max_width=85, padding=10, spacing=10)
        z4.pack()

        # Z5
        z5.set_style_for(Text, font_height=15)
        widget = Text(z5, "Hello world", background_color="green4")
        widget.set_text("Hello world and everyone else")  # -> here, the font_height will be reduced
        Text(z5, "Hello world", background_color="green4")
        Text(z5, "Hello world", background_color="green4", max_width=100)
        Text(z5, "Hello world and everyone else", background_color="green4", max_width=100)
        z5.pack()


# For the PresentationScene import
ut_zone_class = UT_Text_Zone

if __name__ == "__main__":
    from baopig.prefabs.testerscene import TesterScene

    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()

"""
# Default code for Try it yourself
from baopig import *


class UT_Text_Zone(Zone):

    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        Text(parent=self, padding=5, max_width=self.rect.width,
             font_file="passeroone", font_height=50,
             text="Hello world\n"
                  "I am a very long text\n"
                  "but i'm sure que tu peux me lire sans probleme")


app = Application(size=(700, 700))
main_zone = UT_Text_Zone(Scene(app), size=("90%", "90%"), sticky="center")
app.launch()
"""
