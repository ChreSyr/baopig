
import glob
import pygame
from baopig.io import LOGGER
# TODO : change the height system ? go back to default from pygame ?


class Font:

    def __init__(self, owner=None, file=None, height=None, color=None, bold=None, italic=None, underline=None):

        self._file = None
        self._filepath = None
        self._height = None
        self._ascent = None
        self._font = None
        self._color = None
        self._owner_wkref = (lambda: None) if owner is None else owner.get_weakref()

        if owner is not None:
            if file is None:
                file = owner.style["font_file"]
            if height is None:
                height = owner.style["font_height"]
            if color is None:
                color = owner.style["font_color"]
            if bold is None:
                bold = owner.style["font_bold"]
            if italic is None:
                italic = owner.style["font_italic"]
            if underline is None:
                underline = owner.style["font_underline"]

        assert file is None or isinstance(file, str)

        self.config(file=file, height=height, color=color, bold=bold, italic=italic, underline=underline,
                    update_owner=False)

    def __str__(self):

        return f"Font(height:{self.height}, ascent:{self._ascent}, file={self.file})"

    __repr__ = __str__

    color = property(lambda self: self._color)
    file = property(lambda self: self._file)
    filepath = property(lambda self: self._filepath)
    height = property(lambda self: self._height)
    owner = property(lambda self: self._owner_wkref())

    def config(self, file=None, height=None, color=None, bold=None, italic=None, underline=None, update_owner=True):

        if file is not None:
            self._file = file

            if file in sys_fonts:
                pass
            elif file == "monospace":
                file = "JetBrainsMono-Medium.ttf"
            elif not file.endswith(".ttf"):
                if file.count("."):
                    LOGGER.warning("Can only look for tff fonts, not " + file)
                    self._file = file = None
                else:
                    file += ".ttf"

            if file in sys_fonts:
                self._filepath = file
            else:
                if file not in filepaths:
                    # print("get_filepath(", file, end=") -> ", sep="")
                    filepath = get_filepath(file)
                    if filepath is None:
                        LOGGER.warning(f"Font not found : {file} (the default font will be used instead)")
                    filepaths[file] = filepath
                    # print(filepaths[file])
                self._filepath = filepaths[file]

        if height is not None:
            assert height > 1, "A font height must be higher than 1"
            self._height = height
        if file is not None or height is not None:
            """if self.height in _all[file]._fonts:
                ascent = _all[file].get_font(self.height)._ascent
            else:
                ascent = self.height
                all_from_file = _all[self.file]

                little_brother = self.height - 1
                if not all_from_file._fonts:
                    little_brother = 0
                while little_brother > 0 and little_brother not in all_from_file._fonts:
                    little_brother -= 1
                if little_brother > 0:
                    ascent = all_from_file.get_font(little_brother)._ascent

                elif all_from_file._fonts and little_brother == 0:
                    big_brother = self.height + 1
                    while big_brother not in all_from_file._fonts:
                        big_brother += 1
                    ascent = all_from_file.get_font(big_brother)._ascent
                    while height < all_from_file.get_font(ascent=ascent).size("")[1]:
                    while height < pygame.font.Font(self.font, ascent).size("")[1]:
                        ascent -= 1
                        if ascent <= 0:
                            raise PermissionError("Too small value for font height : " + str(self.height))

                while self.height < pygame.font.Font(self.file, ascent).size("")[1]:
                    ascent -= 1
                while self.height > pygame.font.Font(self.file, ascent).size("")[1]:
                    ascent += 1
                if ascent <= 0:
                    raise PermissionError("Too small value for font height : " + str(self.height))
                
            self._ascent = ascent
            self._font = pygame.font.Font(self.file, self._ascent)"""

            self._font = _all[self.filepath].get_font(height=self.height)
            self._ascent = self._font.get_ascent()

        if color is not None:
            try:
                color = pygame.Color(color)  # TODO little rework of Color
            except ValueError:
                color = pygame.Color(*color)
            self._color = color
        if bold is not None:
            self._font.set_bold(bold)
        if italic is not None:
            self._font.set_italic(italic)
        if underline is not None:
            self._font.set_underline(underline)

        if update_owner and self.owner is not None:
            self.owner.set_text(self.owner.text)

    def get_width(self, text):

        return self._font.size(text)[0]

    def render(self, text, background_color=None):

        assert background_color is None or len(background_color) == 3, \
            "Don't like rendering a text with a transparent background color"

        rendering = self._font.render(text, 1, self._color, background_color)
        if rendering.get_height() != self._height:
            assert rendering.get_height() > self._height
            rendering = rendering.subsurface((0, 0, rendering.get_width(), self._height)).copy()
        return rendering


class _Fonts:
    """
    Pour plus de clarte, il a ete decide que Font(30) cree une ploice de taille 30
    En effet, pygame.font.Font(30) cree une police de hauteur 21
    Afin de trouver efficacement quelle valeur faut-il donner à pygame.font.Font
    pour obtenir une police de taille 30, on enregistre les polices auparavent crees
    dans _fonts

    Exemple :

    """

    def __init__(self, filepath):

        if filepath == "default":
            filepath = None
        pygame.font.init()
        self._fonts = {}
        self._fonts_by_ascent = {}
        self._filepath = filepath
        if filepath in sys_fonts:
            self._font_class = pygame.font.SysFont
        else:
            self._font_class = pygame.font.Font

    def get_font(self, height=None, ascent=None):
        """
        Methode qui renvoie une police de hauteur 'height' en pixels ou une police cree
        avec la hauteur bizarre de pygame, appelee ici 'ascent'
        """
        if ascent is None:
            assert isinstance(height, int), "height must be an integer (it's a font size)"
            assert height > 0, "A text must have a positive height"

            try:
                # Si le dictionnaire des polices contient deja la taille de police demandee
                return self._fonts[height]
            except KeyError:
                pass

            # Sinon on l'ajoute au dictionnaire
            ascent = height

            while height < self.get_font(ascent=ascent).get_height():
                ascent -= 1
            while height > self.get_font(ascent=ascent).get_height():
                ascent += 1
            if ascent <= 0:
                raise PermissionError("Too small value for font height : " + str(height))

            try:
                # Si le dictionnaire des polices contient deja la taille de police demandee
                return self._fonts[height]
            except KeyError:
                pass

            if self.get_font(ascent=ascent).get_height() < height:
                # print(self._fonts, self.get_font(ascent=ascent).get_height(), height)
                raise AssertionError
            slightly_higher_font = self.get_font(ascent=ascent)
            for i in range(self.get_font(ascent=ascent).get_height() - height):
                self._fonts[height + i + 1] = slightly_higher_font
            self._fonts_by_ascent[ascent] = slightly_higher_font
            return slightly_higher_font

        else:
            assert height is None

            try:
                # Si le dictionnaire des polices contient deja la taille de police demandee
                return self._fonts_by_ascent[ascent]
            except KeyError:
                pass

            new_font = self._font_class(self._filepath, ascent)
            self._fonts[new_font.get_height()] = new_font
            self._fonts_by_ascent[ascent] = new_font
            return new_font


class _All(dict):
    def __getitem__(self, filepath):
        if filepath not in self:
            self[filepath] = _Fonts(filepath)
        return super().__getitem__(filepath)


_all = _All()


def get_filepath(file):
    import os
    exec_dir = os.getcwd()
    for path in glob.iglob(exec_dir + "/*.ttf"):
        if path.endswith(file):
            return path
    for path in glob.iglob(exec_dir + "/*/*.ttf"):
        if path.endswith(file):
            return path
    for path in glob.iglob(exec_dir + "/*/*.ttf"):
        if path.endswith(file):
            return path
    for path in glob.iglob(exec_dir + "/*/*/*.ttf"):
        if path.endswith(file):
            return path
    for path in glob.iglob(__file__[:-7] + "lib/*.ttf"):
        if path.endswith(file):
            return path
    for path in glob.iglob(__file__[:-7] + "lib/*/*.ttf"):
        if path.endswith(file):
            return path
    for path in glob.iglob(__file__[:-7] + "lib/*/*/*.ttf"):
        if path.endswith(file):
            return path
    for path in glob.iglob("/System/Library/Fonts/*.ttf"):
        if path.endswith(file):
            return path
    for path in glob.iglob("/System/Library/Fonts/*.ttf"):
        if path.endswith(file):
            return path
    for path in glob.iglob("/Library/Fonts/Microsoft/*.ttf"):
        if path.endswith(file):
            return path
    for path in glob.iglob("/Library/Fonts Disabled/*.ttf"):
        if path.endswith(file):
            return path
    for path in glob.iglob("/Library/Fonts/*.ttf"):
        if path.endswith(file):
            return path


filepaths = {}
sys_fonts = pygame.font.get_fonts()

# The 2 last font files, on my ACER with Windows 11, are bugged
sys_fonts.remove('leelawadeegras')
sys_fonts.remove('microsoftuighurgras')

if __name__ == "__main__":
    import os

    exec_dir = os.getcwd()
    for path in glob.iglob(__file__[:-7] + "lib/*.ttf"):
        print(path)
    for path in glob.iglob(__file__[:-7] + "lib/*/*.ttf"):
        print(path)
    for path in glob.iglob(__file__[:-7] + "lib/*/*/*.ttf"):
        print(path)
    for path in glob.iglob("/System/Library/Fonts/*.ttf"):
        print(path)
    for path in glob.iglob("/System/Library/Fonts/*.ttf"):
        print(path)
    for path in glob.iglob("/Library/Fonts/Microsoft/*.ttf"):
        print(path)
    for path in glob.iglob("/Library/Fonts Disabled/*.ttf"):
        print(path)
    for path in glob.iglob("/Library/Fonts/*.ttf"):
        print(path)

    h = 50
    font = Font(file='monospace', height=h)
    print(font.height, h, font._font.get_height())
    assert font.height == h == font._font.get_height()
    print(font)
