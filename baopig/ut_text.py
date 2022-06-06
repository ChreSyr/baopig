

from baopig import *
import pygame


# TODO : solve : selection error, there seems to be a problem with abs_hitbox or selection_rect
class UT_Text_Scene(Scene):

    def __init__(self, app):

        Scene.__init__(self, app)

        hello = Text(
            parent=self,
            pos=(10, 10),
            text="Hello world"
                 "\nIamaverylongword,canyoureadmecorrectly?"
                 "\nWhat do you want to do ?",
            width=250,
            # mode=Text.FILLED_MODE,  # TODO
        )
        ressources.font.config(file="Arial Narrow Bold Italic.ttf")
        hello2 = Text(
            parent=self,
            pos=(hello.right + 10, 10),
            text="Hello world"
                 "\nIamaverylongword,canyoureadmecorrectly?"
                 "\nWhat do you want to do ?",
            width=hello.width,
            # mode=Text.FILLED_MODE,
        )

        # TODO : hide selection_rect on double clic
        ressources.font.config(file="monospace")
        ressources.font.config(height=60)
        ressources.font.config(color=(0, 100, 0))
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
            font=Font(height=10, file="Arial Narrow Bold Italic.ttf")
        )
        text.font.config(height=25)
        text.set_background_color((255, 255, 255, 128))
        edit = TextEdit(self, pos=text.bottomleft, font=text.font, width=text.max_width, text="Green")
        text.font.config(color=(10, 50, 30))

        ressources.font.config(height=20)
        ressources.font.config(color=(0, 0, 0))
        z = Zone(self, pos=edit.bottomleft, size=("90%", "100%"))
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
            Text(z, text=file[:-4] if file.endswith(".ttf") else file, font=Font(file=file), row=i)
        #z.default_layer.pack()


class UT_TextEdit_Scene(Scene):

    def __init__(self, app):

        Scene.__init__(self, app, size=(1000, 700))

        self.zone1 = Zone(self, pos=(10, 10), size=(self.w / 2 - 15, self.h - 20), background_color=(100, 100, 100, 50))
        # print(self.zone1)
        self.zone2 = Zone(self, pos=(self.zone1.right + 10, 10), size=(self.w / 2 - 15, self.h - 20), background_color=(100, 100, 100, 50))

        self.zone1.mirrored = TextEdit(self.zone1, text="0123456789012345", width=40, pos=(10, 10))
        self.zone1.d = DynamicText(self.zone1, self.zone1.mirrored.get_text, pos=self.zone1.mirrored.topright)

        text = TextEdit(self.zone2, pos=(10, 10), width=self.zone2.w - 20)

        self.b = Button(self.zone2, text="RUN", pos=text.topright, command=lambda: exec(text.text))
        self.b.origin.config(location="topright")
        text.signal.RESIZE.connect(lambda: self.b.origin.config(pos=text.topright), owner=self.b)
        text.signal.MOTION.connect(lambda: self.b.origin.config(pos=text.topright), owner=self.b)


        scrap = \
            "f = application.focused_scene\n" \
            "c = f.children\n" \
            "b = Button(application.focused_scene, 'HELLO WORLD', command=lambda: print('Hello world'))\n" \
            "Dragable.set_dragable(b)\n" \
            "b2 = b.copy()\n" \
            "Dragable.set_dragable(b2)\n" \
            ""[:-1]
        scrap = \
            "fr = application.focused_scene\n" \
            "et = fr.zone2.default_layer[0]\n" \
            "font = et.font\n" \
            "for i in range(2, 30):\n" \
            "   font.config(height=i)\n" \
            ""[:-1]
        clipboard.put(scrap)


if __name__ == "__main__":
    app = Application(size=(600, 900))
    UT_Text_Scene(app)
    UT_TextEdit_Scene(app)
    app.launch()