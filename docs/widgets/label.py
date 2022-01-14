

import pygame
from baopig.pybao.issomething import *
from baopig.ressources import ressources
from baopig.font.font import _all, Font
from baopig.io import mouse
from baopig._lib import Runable, Widget, Zone, paint_lock
from .text import Text

fonts = _all[ressources.font.file]


class AbstractLabel(Zone):
    """
    A Label is a Container who contain a Text
    The interest of Label is to be able to ask for a given size, and then to adapt the text.
    """

    def __init__(
            self,
            parent,
            text,
            w, h,
            margin=None,  # TODO : better margin
            font=None,
            text_location=None,
            selectable=True,
            **kwargs
    ):
        """

        TODO : documentation a retravailler

        Si le parametre w est renseigne, la taille de la police s'adapte pour que
        le texte ne depasse pas. Sinon, la hitbox s'adapte a la longeur du texte

        Theoriquement parlant, h et font_size sont exactement les memes ; la hauteur
        du label est aussi la taille de la police en pixels. On va d'abord regarder
        si font_size est renseigne, puis h, et on mettra la valeur DEFAULT_FONT_SIZE par defaut.

        margin est l'espace minimal entre les bords de la hitbox et le texte

        Parce que le text_component est ajoute apres la creation du Label, on ne peut deviner
        la taille que prendra ce Label. On reinitialise donc la hitbox et le background dans
        self.set_text_component()
        """

        # DEFAULT VALUES

        # margin, h and font_size
        if font is not None: font = font.copy()
        font_size = font.height if font is not None else None
        font_size_is_unset = font_size is None
        h_is_unset = h is None
        if font_size is not None and h is not None:
            assert font_size <= h, "The text cannot exceed the label height"

        # margin
        if margin is None:
            if font_size is not None and h is not None:
                margin = int((h - font_size) / 2)
            else:
                margin = 0
        assert margin >= 0, "The value of margin must be positive : {} ".format(margin)


        if font_size is None and h is None: font_size = ressources.font.height
        if h is None: h = font_size + margin * 2
        assert h > 0, "The value of h must be positive : {} ".format(h)
        if font_size is None: font_size = h - margin * 2
        assert font_size <= h - margin * 2, "The text cannot exceed the space defined by the margin"
        assert font_size > 0, "The value of font_size must be positive : {} ".format(font_size)

        # w
        if w is None: w = fonts.get_font(font_size).size(text)[0] + margin * 2
        else:
            if font_size_is_unset or True:
                while font_size > 1 and fonts.get_font(font_size).size(text)[0] > w - margin * 2:
                    font_size -= 1
                assert font_size > 0, "The value of font_size is too small : {} " \
                                      "(this is the result of a small width parameter)".format(font_size)
                if h_is_unset and text:
                    while fonts.get_font(font_size).size(text)[0] < w - margin * 2:
                        font_size += 1
                    font_size -= 1
                    h = font_size + margin * 2
            else:
                assert font_size <= w - margin * 2, "The text cannot exceed the space defined by the margin"
        assert w > 0, "The value of w must be positive : {} ".format(w)

        if font is None: font = Font()
        font._height = font_size
        font._color = self.theme.get_value("theme-color-font")  # TODO : remove this temporary fix with better font system

        if text_location is None: text_location = "center"
        assert isinstance(selectable, bool)

        # INHERITANCE
        Zone.__init__(
            self,
            parent=parent,
            size=(w, h),
            **kwargs
        )

        text_component = Text(
            parent=self,
            text=text,
            pos=getattr(self.auto, text_location),
            pos_location=text_location,
            font=font,
            selectable=selectable,
            name=self.name + " -> text"
        )

        # TODO : self.set_padding(margin)

        self._text_component_ref = text_component.get_weakref()
        # self.margin = margin

    text = property(lambda self: self.text_component.text)
    text_component = property(lambda self: self._text_component_ref())
    font_size = property(lambda self: self.text_component.font.height)
    font_color = property(lambda self: self.text_component.font.color)



class Label(AbstractLabel):
    """
    A Label is a Label who cannot evolve during the application life
    It contains a LineText

    """

    def __init__(
            self,
            parent,
            text,
            font=None,
            size=(None, None),
            w=None,
            h=None,
            margin=None,
            text_location=None,
            selectable=True,
            **kwargs
    ):
        """
        Si le parametre w n'est pas renseigne, la hitbox s'adapte a la longeur du texte
        Si le parametre w est renseigne, la taille de la police s'adapte pour que
        le texte ne depasse pas. Si le texte ne prends pas toute la largeur, il est
        positionne au milieu du label

        Theoriquement parlant, h et font_size sont exactement les memes ; la hauteur
        du label est aussi la taille de la police en pixels. On va d'abord regarder
        si font_size est renseigne, puis h, et on mettra la valeur DEFAULT_FONT_SIZE par defaut.

        margin est l'espace minimal entre les bords de la hitbox et le texte
        margin_x est l'espace reel entre les bords droite/gauche de la hitbox et ceux du texte
        margin_y est l'espace reel entre les bords haut/bas de la hitbox et ceux du texte

             ___________________________________________
            |  _ _ _______________________________ _ _  |     | margin = margin_y
            | |   |    _                          |   | |
            |     |   |_   _   _         _        |     |
            | |   |   |   |_| |     |_| |_| |_|   |   | |
            |     |                  _|           |     |
            | | _ |_______________________________| _ | |
            |___________________________________________|     | margin = margin_y

            <---->                                     -
            margin_x                              margin
        """

        assert is_iterable(size, 2)
        if size[0] is not None: w = size[0]
        if size[1] is not None: h = size[1]

        # HERITANCE
        AbstractLabel.__init__(
            self,
            parent,
            text,
            font=font,
            w=w,
            h=h,
            margin=margin,
            text_location=text_location,
            selectable=selectable,
            **kwargs
        )


# TODO : Faire des tests avec des margin, des modification_mode...
class DynamicLabel(AbstractLabel, Runable):
    """
    A DynamicLabel is basically a Label who can change its LineText

    At creation, you must fill one (and only one) of the following parameters :
        - text : The text will not change by itself
        - get_text : At each run() loop, the text will be set to get_text()
        - observed_object : At each run() loop, the text will be set to str(observed_object)

    The aspects of the label who might evolve :
        - the text
        - the font size
        - the font color
        - the background color
        - the margin (TODO : margin modification not implemented yet)

    If the h or w parameter is filled, then they are respectively not able to change at all
    OR
    There is a new modification_mode in addition with these from DynamicText:
        - FIXED_HITBOX : Can change the text. The font size is limited by the hitbox's width
    The default modification_mode is ADAPTABLE

    The surface might wait for the first _render() call to correspond to hitbox size
    This is the only moment where surface.get_size() and hitbox.size can differ

    """
    # TODO : modification_mode rework
    # TODO : pos argument is the position of origin_location

    def __init__(self,
                 parent,
                 pos=None,
                 text=None,
                 get_text=None,
                 observed_object=None,
                 size=(None, None),
                 w=None,
                 h=None,
                 margin=None,
                 font_size=None,
                 font_color=None,
                 background_color=None,
                 selectable=True,
                 modification_mode=None,
                 text_location=None,
                 origin_location=None,
                 name=None,
    ):

        assert len([arg for arg in (text, get_text, observed_object) if arg is not None]) <= 1, \
            "You must fill at most one of these parameters : 'text', 'get_text' or 'observed_object'"

        # text
        if text is None:
            if get_text is None:
                if observed_object is None:
                    text = "Unset"
                else:
                    text = str(observed_object)
                    get_text = observed_object.__str__
            else:
                try:
                    text = str(get_text())
                except Exception as e:
                    text = "Unset"

        # size
        assert is_iterable(size, 2)
        if size[0] is not None: w = size[0]
        if size[1] is not None: h = size[1]

        # modification_mode
        # if modification_mode is None: modification_mode = ADAPTABLE  # TODO : what was that ?

        AbstractLabel.__init__(
            self,
            parent=parent,
            text=text,
            pos=pos,
            w=w,
            h=h,
            margin=margin,
            font_size=font_size,
            font_color=font_color,
            background_color=background_color,
            text_location=text_location,
            origin_location=origin_location,
            name=name,
        )
        Runable.__init__(self)

        self._get_new_text = get_text
        self.modification_mode = modification_mode
        self.has_fixed_width = w is not None or modification_mode == ADAPTABLE
        self.has_fixed_height = h is not None
        # TODO : solve default_font_size bug
        self.default_font_size = self.text_component.font.height if font_size is None else font_size

        if self._get_new_text is None:
            self.stop_running()
        if self.modification_mode == FIXED_HITBOX:
            self.lock_size()
        if self.modification_mode == IMMOVABLE:
            self.lock_size()

    get_new_text = property(lambda self: self._get_new_text)

    def run(self):

        if self.get_new_text is None:
            print("USELESS CALL")
            return
        new_text = self.get_new_text()
        if new_text != self.text:
            self.set_text(new_text)

    def set_font_size(self, font_size):

        assert isinstance(font_size, int)

        if self.text_component.font_size == font_size:
            return None

        if self.modification_mode == IMMOVABLE:
            return None
        elif self.modification_mode == FIXED_FONT_SIZE:
            return None
        elif self.modification_mode == FIXED_TEXT:
            self.text_component.set_font_size(font_size)
        elif self.modification_mode == FIXED_HITBOX:
            while self.w < fonts.get_font(font_size).get_width(self.text):
                font_size -= 1
            self.text_component.set_font_size(font_size)
        elif self.modification_mode == ADAPTABLE:
            self.text_component.set_font_size(font_size)

        self.update_size()
        self.send_paint_request()

    def set_text(self, text):

        assert isinstance(text, str)

        if self.text == text:
            return None

        old_text = self.text

        if self.modification_mode == IMMOVABLE:
            return None
        elif self.modification_mode == FIXED_FONT_SIZE:
            self.text_component.set_text(text)
        elif self.modification_mode == FIXED_TEXT:
            return None
        elif self.modification_mode == FIXED_HITBOX:
            self.text_component.set_text(text)
            self.set_font_size(self.default_font_size)  # the font size need to adapt to the text
        elif self.modification_mode == ADAPTABLE:
            self.text_component.set_text(text)

        self.update_size()
        self.send_paint_request()

    def update_size(self):

        if self.text_component.w + self.margin * 2 != self.w:
            old_w = self.w
            self.resize_width(self.text_component.w + self.margin * 2)
            # self.text_component.x += self.w - old_w

        if self.text_component.h + self.margin * 2 != self.h:
            old_h = self.h
            self.resize_height(self.text_component.h + self.margin * 2)
            # self.text_component.y += self.h - old_h
