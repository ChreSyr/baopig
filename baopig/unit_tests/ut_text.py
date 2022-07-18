from baopig import *


class UT_Text_Zone(Zone):

    def __init__(self, *args, **kwargs):
        Zone.__init__(self, *args, **kwargs)

        Layer(self, name="zones_layer", children_margins=10)
        z1 = Zone(self, size=("100%", 60), background_color=(150, 150, 150), children_margins=5, padding=5)
        z2 = Zone(self, size=("100%", 100), background_color=(150, 150, 150), children_margins=5, padding=5)
        z3 = Zone(self, size=("100%", 155), background_color=(150, 150, 150), padding=5)
        z4 = Zone(self, size=("100%", 120), background_color=(150, 150, 150), children_margins=5, padding=5)
        z5 = Zone(self, size=("100%", 120), background_color=(150, 150, 150), children_margins=5, padding=5)
        self.default_layer.pack()

        # Z1
        hello = Text(parent=z1, text="Hello world\nIamaverylongword,canyoureadmecorrectly?"
                                     "\nWhat do you want to do ?", max_width=250, padding=5)
        self.set_style_for(Text, font_file="Arial Narrow Bold Italic.ttf")
        Text(parent=z1, text="Hello world\nIamaverylongword,canyoureadmecorrectly?"
                             "\nWhat do you want to do ?", max_width=hello.rect.width)
        z1.pack(axis="horizontal")

        # Z2
        self.set_style_for(Text, font_file="monospace")
        self.set_style_for(Text, font_height=60)
        self.set_style_for(Text, font_color=(0, 150, 0))
        text = Text(z2, max_width=370, font_height=10, font_file="Arial Narrow Bold Italic.ttf",
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
        TextEdit(z2, text="Green", max_width=text.rect.width)
        z2.pack(axis="horizontal")

        # Z3
        self.set_style_for(Text, font_height=20)
        self.set_style_for(Text, font_color=(0, 0, 0))
        GridLayer(z3)
        for i, file in enumerate((
                "I am written in the default font",
                "monospace",
                # "Georgia.ttf",
                # "PlantagenetCherokee.ttf",
                # "Trebuchet MS Italic.ttf",
                # "Times New Roman.ttf",
                # "Arial.ttf",
                # "Osaka.ttf",
                # "Silom",
                # "Wingdings 2.ttf",
                # "Calibri.ttf",
                # "Candara.ttf",
                # "Consolas",
                # "Verdana",
                # "Keyboard.ttf",
                # "Gill Sans MT",
                # "Palatino Linotype.ttf",
                # "JetBrainsMono-Regular.ttf",
                # "JetBrainsMono-Medium.ttf",
                # "JetBrainsMono-Bold.ttf",
                # "JetBrainsMono-ExtraBold.ttf",
                "Nimportequoi.ttf",
        )):
            Text(z3, text=file[:-4] if file.endswith(".ttf") else file, font_file=file, row=i)
        z3.default_layer.pack()

        # Z4
        t = Text(z4, "max_width:150", max_width=150)
        Text(z4, "max_width:75", max_width=75, height=10)  # height is ignored
        Text(z4, "padding:5", padding=5)
        Text(z4, "1\n2\n3", max_width=85, padding=10, children_margins=10)
        z4.pack()

        # Z5
        self.set_style_for(Text, font_height=15)
        widget = Text(z5, "Hello world", background_color="green4")
        widget.set_text("Hello world and everyone else")  # -> here, the font_height will be reduced
        Text(z5, "Hello world", background_color="green4")
        Text(z5, "Hello world", background_color="green4", max_width=100)
        Text(z5, "Hello world and everyone else", background_color="green4", max_width=100)
        z5.pack()


# For the PresentationScene import
ut_zone_class = UT_Text_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene

    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
