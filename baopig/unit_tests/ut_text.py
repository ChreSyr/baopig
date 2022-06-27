
from baopig import *


class UT_Text_Zone(Zone):

    def __init__(self, *args, **kwargs):

        Zone.__init__(self, *args, **kwargs)

        hello = Text(
            parent=self,
            pos=(10, 10),
            text="Hello world"
                 "\nIamaverylongword,canyoureadmecorrectly?"
                 "\nWhat do you want to do ?",
            width=250,
        )
        self.set_style_for(Text, font_file="Arial Narrow Bold Italic.ttf")
        hello2 = Text(
            parent=self,
            pos=(hello.right + 10, 10),
            text="Hello world"
                 "\nIamaverylongword,canyoureadmecorrectly?"
                 "\nWhat do you want to do ?",
            width=hello.width,
        )

        self.set_style_for(Text, font_file="monospace")
        self.set_style_for(Text, font_height=60)
        self.set_style_for(Text, font_color=(0, 100, 0))
        text = Text(
            self,
            pos=hello.bottomleft,
            text="- Bonjour à tous\n"
            "- Bonjour monsieur. Comment allez-vous ?\n"
            "- Très bien merci. Nous allons commencer.\n"
            "- Monsieur, j'avais oublié, j'ai un rendez-vous !\n"
            "- Eh bien filez, ça ira pour cette fois.\n"
            "- Merci monsieur !\n"
            "Et il partit. (vert fonce)",
            width=370,
            font_height=10,
            font_file="Arial Narrow Bold Italic.ttf"
        )
        text.set_background_color((255, 255, 255, 128))
        text.font.config(color=(10, 50, 30))
        edit = TextEdit(self, text="Green", width=text.width, pos=text.bottomleft)

        self.set_style_for(Text, font_height=20)
        self.set_style_for(Text, font_color=(0, 0, 0))
        z = Zone(self, pos=edit.bottomleft, size=("90%", "30%"))
        GridLayer(z)
        for i, file in enumerate((
            "I am written in the default font",
            "monospace",
            "Georgia.ttf",
            "PlantagenetCherokee.ttf",
            "Trebuchet MS Italic.ttf",
            "Times New Roman.ttf",
            "Arial.ttf",
            "Osaka.ttf",
            "Silom",
            "Wingdings 2.ttf",
            "Calibri.ttf",
            "Candara.ttf",
            "Consolas",
            "Verdana",
            "Keyboard.ttf",
            "Gill Sans MT",
            "Palatino Linotype.ttf",
            "JetBrainsMono-Regular.ttf",
            "JetBrainsMono-Medium.ttf",
            "JetBrainsMono-Bold.ttf",
            "JetBrainsMono-ExtraBold.ttf",
            "Nimportequoi.ttf",
        )):
            Text(z, text=file[:-4] if file.endswith(".ttf") else file, font_file=file, row=i)
        #z.default_layer.pack()


# For the PresentationScene import
ut_zone_class = UT_Text_Zone

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    TesterScene(app, ut_zone_class)
    app.launch()
