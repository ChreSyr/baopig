
import pygame
from math import inf as math_inf
from baopig.pybao.issomething import *
from baopig.pybao.objectutilities import Object, TypedList
from baopig.ressources import *
from baopig.font.font import Font
from baopig.io import mouse
from baopig._lib import *


def set_indicator(self, text=None, get_text=None, indicator=None):
    """Create a text above the widget when hovered"""

    if self._indicator is not None:
        raise PermissionError("Can only have one indicator")
    if indicator is not None:
        self._indicator = indicator
    elif (text is not None) == (get_text is not None):
        raise PermissionError("You must only define one of text and get_text")
    elif text is None:
        self._indicator = DynamicText(
            self.parent, get_text,
            color=(255, 255, 255), font_height=15,
            pos=(0, -5), pos_location="bottom", pos_ref=self, pos_ref_location="top",
            background_color=(0, 0, 0, 192), padding=(8, 4), touchable=False,
        )
    else:
        self._indicator = Text(
            self.parent, text,
            color=(255, 255, 255), font_height=15,
            pos=(0, -5), pos_location="bottom", pos_ref=self, pos_ref_location="top",
            background_color=(0, 0, 0, 192), padding=(8, 4), touchable=False,
        )
    self._indicator.origin.config(from_hitbox=True)
    if self.layer.accept(self._indicator):
        self._indicator.swap_layer(self.layer)
        self._indicator.move_in_front_of(self)
    self._indicator.connect("wake", self.signal.HOVER)
    self._indicator.connect("asleep", self.signal.UNHOVER)
    if not self.is_hovered:
        self._indicator.asleep()
Hoverable.set_indicator = set_indicator


class _Line(ResizableWidget):
    """
    A Line is a component who only have text on its surface
    It have a transparent background
    It have an end string who is the separator between this line and the next one

    The aspects who might evolve :
        - the text
        - the font size
        - the font color
        - the end character

    When the hitbox size change, there is only one point who is used to locate the LineText : it is
    the origin. Exemple : if the origin is TOPLEFT, and the hitbox width grows, it will expend on the
    right side, because the origin is on the left. Ther is 9 possible positions for the origin :
        - topleft       - midtop        - topright
        - midleft       - center        - midright
        - bottomleft    - midbottom     - bottomright
    The default origin position is TOPLEFT


    Here is an example of font size :

        font_size = 63
        ____   _
        ____  |_   _   _         _             | 13 px  |
        ____  |   |_| |     |_| |_| |_|        | 37 px  | 63 px
        ____                 _|                | 13 px  |

    A Line is an element of a Paragraph, wich ends with a '\n'.

    """

    def __init__(self, parent, text, line_index):

        assert isinstance(parent, Text)

        self._line_index = line_index
        ResizableWidget.__init__(self,
            parent=parent,
            surface=pygame.Surface((parent.w, parent.font.height), pygame.SRCALPHA),
            layer=parent.lines,
            name="{}({})".format(self.__class__.__name__[1:], text),
        )

        self.__text = ""
        self.__end = ''
        self._text_with_end = None
        self._real_text = None
        # char_pos[i] est la distance entre left et la fin du i-eme caractere
        # Exemple : soit self.text = "Hello world"
        #           char_pos[6] = margin + distance entre le debut de "H" et la fin de "w"
        self._chars_pos = []

        self.config(text=text, end='\n', called_by_constructor=True)

    def __repr__(self):
        return "{}(index={}, text={})".format(self.__class__.__name__, self.line_index, self.text)

    def __str__(self):
        return self.text

    def _set_end(self, end):
        self.__end = end
        self._text_with_end = self.text + end
        self._real_text = self.text + ('' if end == '\v' else end)
    _end = property(lambda self: self.__end, _set_end)
    end = property(lambda self: self.__end)
    font = property(lambda self: self._parent._font)
    line_index = property(lambda self: self._line_index)
    real_text = property(lambda self: self._real_text)
    def _set_text(self, text):
        self.__text = text
        self._text_with_end = text + self.end
        self._real_text = text + ('' if self.end == '\v' else self.end)
    _text = property(lambda self: self.__text, _set_text)
    text = property(lambda self: self.__text)
    text_with_end = property(lambda self: self._text_with_end)

    def find_index(self, x, only_left=False, end_of_word=False):
        """
        Renvoie l'index correspondant a la separation de deux lettres la plus proche de x

        Example :
            x = 23              (23eme pixel a droite de self.left)
            find_index(x) -> 3  (position entre la 3eme et la 4eme lettre)

        Si only_left est demande, renvoie un index qui correspond a une separation a droite
        de x
        Si end_of_word est a True, l'index renvoye correspondra a une fin de mot
        Un mot est precede et suivi d'espaces ou d'un tiret
        Example:
            'Comment allez-vous ?' est forme des mots 'Comment', 'allez-', 'vous' et '?'
        """

        def ecart(x1, x2):
            return abs(x1 - x2)

        dist_from_closest_char = math_inf
        index_of_closest_char = None

        for index, char_pos in enumerate(self._chars_pos):

            if only_left and char_pos > x:
                break
            if ecart(x, char_pos) > dist_from_closest_char:
                break

            if end_of_word:
                if index != 0 and index != len(self.text):
                    def is_end_of_word(i):
                        if self.text[i] == ' ':
                            return True
                        if self.text[i-1] == '-':
                            return True
                        return False
                    if not is_end_of_word(index):
                        continue

            dist_from_closest_char = ecart(x, char_pos)
            index_of_closest_char = index

        return index_of_closest_char

    def find_mouse_index(self):
        """
        Return the closest index from mouse.x
        """

        return self.find_index(mouse.get_pos_relative_to(self)[0])

    def find_pixel(self, index):
        """
        Renvoi la distance entre hitbox.left et la fin du index-eme caractere
        """
        return self._chars_pos[index]

    def get_first_line_of_paragraph(self):
        if self.line_index == 0:
            return self
        i = self.line_index
        while self.parent.lines[i-1].end != '\n':
            i -= 1
        return self.parent.lines[i]

    def get_last_line_of_paragraph(self):
        i = self.line_index
        while self.parent.lines[i].end != '\n':
            i += 1
        return self.parent.lines[i]

    def get_paragraph(self):
        line = self.get_first_line_of_paragraph()
        while line.end != '\n':
            yield line
            line = self.parent.lines[line.line_index+1]
        yield line

    def get_paragraph_text(self):
        return ''.join(line.real_text for line in self.get_paragraph())[:-1]  # discard '\n'

    def get_paragraph_text_with_end(self):
        return ''.join(line.text_with_end for line in self.get_paragraph())

    def insert(self, char_index, string):
        """
        Insert a string inside a line (not after the end delimitation)
        """

        if string:
            self.config(text=self.text[:char_index] + string + self.text[char_index:])

    def pop(self, index):
        """
        Remove one character from line.real_text
        """

        if index < 0:
            index = len(self.real_text) + index
        if self.end != '\v' and index == len(self.real_text)-1:
            if self.line_index == len(self.parent.lines)-1:
                return  # pop of end of text
            self.config(end='\v')
        else:
            self.config(text=self.text[:index] + self.text[index+1:])

    def config(self, text=None, end=None, called_by_constructor=False):

        # if not called_by_constructor:

        with paint_lock:

            if end is not None:
                assert end in ('\n', ' ', '\v')
                if self.parent.max_width is None:
                    assert end == '\n'
                self._end = end
            if text is not None:
                if '\t' in text:
                    text = str.replace(text, '\t', '    ')  # We can also replace it at rendering
                if '\v' in text:
                    text = str.replace(text, '\v', '')
                assert isinstance(text, str)
                self._text = text

            if self.end != '\n' and self.line_index == len(self.parent.lines)-1:
                raise PermissionError

            if called_by_constructor is False and len(tuple(self.get_paragraph())) > 0:

                self._text = self.get_paragraph_text()

                for line in tuple(self.get_paragraph()):
                    if line != self:
                        line.kill()
                self.parent._pack()

                self._end = '\n'

            if '\n' in self.text:
                self.__class__(
                    parent=self.parent,
                    text=self.text[self.text.index('\n')+1:],
                    line_index=self.line_index + .5
                )
                self._text = self.text[:self.text.index('\n')]

            self.update_char_pos()
            if self.parent.max_width is not None and self.font.get_width(self.text) > self.parent.max_width:

                max_width = self.parent.max_width
                assert self.find_pixel(1) <= max_width, "The max_width is too little : " + str(max_width)

                if True:
                    index_end = index_newline_start = self.find_index(
                        max_width, only_left=True, end_of_word=True)
                    if index_end == 0:
                        sep = '\v'
                        index_newline_start = index_end = self.find_index(
                            max_width, only_left=True, end_of_word=False)
                    else:
                        end = self.text[index_end]
                        sep = ' ' if end == ' ' else '\v'  # else, the word is of type 'smth-'
                        if end == ' ': index_newline_start += 1
                    LineClass = _SelectableLine if isinstance(self, Selectable) else _Line
                    self.__class__(
                        parent=self.parent,
                        text=self.text[index_newline_start:],
                        line_index=self.line_index + .5,  # the line will correct itself
                    )
                    self._end = sep
                    self._text = self.text[0:index_end]
                    self.update_char_pos()

            font_render = self.font.render(self.text)
            surf_w = font_render.get_width()
            # if self.parent.max_width is not None: surf_w = max(self.parent.w, surf_w)
            surface = pygame.Surface((surf_w, self.font.height), pygame.SRCALPHA)
            surface.blit(font_render, (0, 0))
            """if self.parent.max_width is None:
                surface.blit(font_render, (0, 0))
            elif self.parent.align_mode == "left":
                surface.blit(font_render, (0, 0))
            elif self.parent.align_mode == "center":
                surface.blit(font_render, (int((surf_w - font_render.get_width()) / 2), 0))
            elif self.parent.align_mode == "right":
                surface.blit(font_render, (surf_w - font_render.get_width(), 0))
            else:
                raise ValueError"""
            self.set_surface(surface)
            self.parent._pack()

    def update_char_pos(self):
        """
        Actualise les valeurs de char_pos

        Appele lors de la creation de LineSelection et lorsque le texte change

        char_pos[i] est la distance entre hitbox.left et la fin du i-eme caractere
        Exemple :
                    Soit self.text = "Hello world"
                    char_pos[6] = margin + distance entre le debut de "H" et la fin de "w"
        """
        self._chars_pos = [0]
        text = ''
        for char in self.text:
            text += char
            self._chars_pos.append(self.font.get_width(text))


class _SelectableLine(_Line, Selectable):
    """
    You are selecting a SelectableLine when :
        - A condition described in Selectable is verified
        - A cursor moves while Maj key is pressed
    """
    
    def __init__(self, *args, **kwargs):

        _Line.__init__(self, *args, **kwargs)
        Selectable.__init__(self)

        def connect():
            self.connect("handle_selector_link", self.selector.signal.LINK)
        self.parent.send_request(connect)

        self._selection_ref = lambda: None

    selection = property(lambda self: self._selection_ref())

    def select(self):

        selection = self.selector.selection_rect
        assert self.abs_hitbox.colliderect(selection.abs_hitbox)
        if self.selection is None and not selection.w and not selection.h:
            return

        if self.selection is None:
            _LineSelection(self)

        selecting_line_end = False
        if self.abs.top <= selection.start[1] < self.abs.bottom:
            start = self.find_index(selection.start[0] - self.abs.left)
        elif selection.start[1] < self.abs.top: start = 0
        else:
            start = len(self.text)
            if self is not self.parent.lines[-1]: selecting_line_end = True
        if self.abs.top <= selection.end[1] < self.abs.bottom:
            end = self.find_index(selection.end[0] - self.abs.left)
        elif selection.end[1] < self.abs.top: end = 0
        else:
            end = len(self.text)
            if self is not self.parent.lines[-1]: selecting_line_end = True

        start, end = sorted((start, end))
        self.selection.config(start, end, selecting_line_end)

    def get_selected_data(self):
        if self.selection is None:
            return ''
        return self.selection.get_data()

    def handle_selector_link(self):

        if mouse.has_triple_clicked:
            if self.parent.collidemouse() and self.hitbox.top <= mouse.get_pos_relative_to(self.parent)[1] < self.hitbox.bottom:
                with paint_lock:
                    self.selector.close_selection()
                    self.selector.start_selection((self.abs.left, self.abs.top))
                    self.selector.end_selection((self.abs.right, self.abs.top), visible=False)  # not + 1 so we don't see the selection rect
                # print("selection :", self.selection.index_start, self.selection.index_end)
        elif mouse.has_double_clicked:
            if self.parent.collidemouse() and self.hitbox.top <= mouse.get_pos_relative_to(self.parent)[1] < self.hitbox.bottom:
                self.select_word(self.find_mouse_index())
                # print("selection :", self.selection.index_start, self.selection.index_end)

    def select_word(self, index):
        """
        Selectionne le mot le plus proche de index
        """

        separators = " ,„.…:;/\'\"`´”’" \
                     "=≈≠+-±–*%‰÷∞√∫" \
                     "()[]{}<>≤≥«»" \
                     "?¿!¡@©®ª#§&°" \
                     "‹◊†¬•¶|^¨~" \
                     ""

        index_start = index_end = index
        while index_start > 0 and self.text[index_start - 1] not in separators:
            index_start -= 1
        while index_end < len(self.text) and self.text[index_end] not in separators:
            index_end += 1

        # Si index n'est pas sur un mot, on selectionne tout le label
        if index_start == index_end == index:
            index_start = 0
            index_end = len(self.text)

        with paint_lock:
            if self.selector.is_selecting:
                self.selector.close_selection()
            if index_start == 0:
                self.selector.start_selection((self.abs.left, self.abs.top))
            else:
                self.selector.start_selection((self.abs.left + self.find_pixel(index_start), self.abs.top))
            if index_end == len(self.text):
                self.selector.end_selection((self.abs.right, self.abs.top), visible=False)
            else:
                self.selector.end_selection((self.abs.left + self.find_pixel(index_end), self.abs.top), visible=False)

    def unselect(self):
        if self.selection is not None:
            self.selection.kill()


class _LineSelection(Rectangle):
    """
    A LineSelection is a Rectangle with a light blue color : (167, 213, 255, 127)
    Each Line can have a LineSelection

    When you click on a SelectableLine, and then move the mouse while its pressed,
    you are selecting the SelectableLine
    The size and the position of the LineSelection object change according to your mouse

    When you double-click on a SelectableLine, it select a word
    When you triple-click on a SelectableLine, it select the whole line text
    """

    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        color = "theme-color-selection",
        border_width = 0
    )

    def __init__(self, line):

        assert isinstance(line, _SelectableLine)

        self._line_index = line.line_index
        Rectangle.__init__(self,
            parent=line.parent,
            pos=line.topleft,
            size=(0, line.h),
            name=line.name+" -> selection"
        )

        # self.is_selecting = False  # True if the user is pressing the mouse button for a selection
        self._index_start = self._index_end = 0
        self._is_selecting_line_end = False
        self._line_ref = line.get_weakref()

        # Initializations
        # self.move_behind(self.line)
        self.line._selection_ref = self.get_weakref()
        self.depend_on(self.line)
        self.swap_layer("line_selections")

    index_end = property(lambda self: self._index_end)
    index_start = property(lambda self: self._index_start)
    line = property(lambda self: self._line_ref())
    line_index = property(lambda self: self._line_index)
    text = property(lambda self: self.line._text)

    def config(self, index_start, index_end, selecting_line_end):

        index_start, index_end = sorted((index_start, index_end))
        self.set_start(index_start)
        self.set_end(index_end, selecting_line_end)
        # TODO : remove set_start and set_end

    def get_data(self):
        end = self.line.end if self._is_selecting_line_end else ''
        if end == '\v': end = ''
        return self.line.text[self.index_start:self.index_end] + end

    def set_end(self, index, selecting_line_end):

        self._index_end = index
        self._is_selecting_line_end = selecting_line_end
        if selecting_line_end:
            assert self.line is not self.parent.lines[-1]

        if self._is_selecting_line_end:
            self.resize_width(self.line.width -
                              self.line.find_pixel(self.index_start))
        else:
            self.resize_width(abs(self.line.find_pixel(self.index_end) -
                                  self.line.find_pixel(self.index_start)))
        self.left = self.line.x + self.line.find_pixel(self.index_start)

    def set_start(self, index):

        if index == self.index_start:
            return

        self._index_start = self._index_end = index
        self.resize_width(0)
        self.left = self.line.find_pixel(self._index_start)

        if self.is_sleeping:
            self.wake()
        self.show()


# TODO : Line (text with only one line)
class Text(Zone):

    STYLE = Zone.STYLE.substyle()
    STYLE.modify(
        width=0,
        height=0,
    )
    STYLE.create(
        font_file = None,
        font_height = 15,
        color = "theme-color-font",
        bold = False,
        italic = False,
        underline = False,
        align_mode = "left",
        max_width=None,
    )
    STYLE.set_type("font_height", int)
    STYLE.set_type("color", Color)
    STYLE.set_type("bold", bool)
    STYLE.set_type("italic", bool)
    STYLE.set_type("underline", bool)
    STYLE.set_type("align_mode", str)
    STYLE.set_type("padding", MarginType)
    STYLE.set_constraint("font_height", lambda val: val > 0, "a text must have a positive font height")
    STYLE.set_constraint("font_file", lambda val: (val is None) or isinstance(val, str), "must be None or a string")
    STYLE.set_constraint("align_mode", lambda val: val in ("left", "center", "right"), "must be 'left', 'center' or 'right'")

    # TODO : align modes
    # LEFT_MODE = 50
    # CENTER_MODE = 51
    # RIGHT_MODE = 52

    def __init__(self,
        parent,
        text=None,
        font=None,  # TODO : remove it
        font_file=None,
        font_height=None,
        color=None,
        bold=False,
        italic=False,
        underline=False,
        max_width=None,
        padding=None,
        selectable=True,
        **options
    ):

        # if mode is None: mode = Text.LEFT_MODE

        if max_width is not None:
            options["max_width"] = max_width
            assert isinstance(max_width, int)
            assert max_width > 0
        assert isinstance(selectable, bool)

        Zone.__init__(self, parent, **options)

        if font is None:
            self.inherit_style(
                parent,
                font_file=font_file,
                font_height=font_height,
                color=color,
                bold=bold,
                italic=italic,
                underline=underline,
                padding=padding,
            )
            font = Font(
                file=self.style["font_file"],
                height=self.style["font_height"],
                color=self.style["color"],
                bold=self.style["bold"],
                italic=self.style["italic"],
                underline=self.style["underline"],
                text_owner=self,
            )
        else:
            assert isinstance(font, Font), str(font)
            font = font.copy(text_owner=self)

        self._font = font
        self._max_width = self.style["max_width"]
        self._min_width = self.font.get_width("m")
        self._is_selectable = selectable
        self._lines_pos = []
        self._align_mode = self.style["align_mode"]
        self._padding = self.style["padding"]
        self.has_locked.text = False

        if self.max_width is not None:
            self.resize_width(self.max_width)
            self.lock_width(True)

        self.line_selections = Layer(self, _LineSelection, name="line_selections", touchable=False, sort_by_pos=True)
        # self.lines = GridLayer(self, "lines", _Line)
        self.lines = Layer(self, _Line, name="lines", default_sortkey=lambda line: line.line_index)
        # self.layers.add_layer("line_selections", CompsClass=_LineSelection, touchable=False)
        # self.layers.add_layer("lines", CompsClass=_Line, default_sortkey=lambda line: line.line_index)
        # self.line_selections.move_behind("lines")
        self.set_text(text)

    align_mode = property(lambda self: self._align_mode)
    font = property(lambda self: self._font)
    is_selectable = property(lambda self: self._is_selectable)
    max_width = property(lambda self: self._max_width)
    padding = property(lambda self: self._padding)

    def _pack(self):

        if self.align_mode == "center":  # only usefull for the widget creation
            if self.max_width is None:
                centerx = int(max(l.w for l in self.lines) / 2)
            else:
                centerx = int(self.max_width / 2)

        self.lines.sort()
        h = self.padding.top
        for i, line in enumerate(self.lines):
            line.topleft = (self.padding.left, h)
            line._line_index = i
            h = line.bottom

            if self.align_mode == "left":
                line.left = self.padding.left
            elif self.align_mode == "center":
                line.centerx = centerx
            elif self.align_mode == "right":
                line.right = self.width - self.padding.right

        self.adapt(self.lines, padding=self.padding, horizontally=self.max_width is None)

        self._lines_pos = []
        for line in self.lines:
            self._lines_pos.append(line.top)

    def _find_index(self, pos):
        """
        Renvoie l'index correspondant a l'espace entre deux caracteres le plus proche

        Exemple :
            pos = (40, 23)                             (40eme pixel a partir de self.left, 23eme pixel sous self.top)
            find_index(pos) -> self.find_index(2, 13)  (pos est sur le 14eme caractere de la 3eme ligne)
        """

        if pos[1] < 0:
            return self.lines[0].find_index(pos[0])
        elif pos[1] >= self.h:
            return self.find_index(len(self.lines) - 1, self.lines[-1].find_index(pos[0]))
        else:
            for line_index, line in enumerate(self.lines):
                if pos[1] < line.bottom:
                    return self.find_index(line_index, line.find_index(pos[0]))
        assert self.lines[-1].bottom == self.h, str(self.lines[-1].bottom) + ' ' + str(self.h)
        raise Exception

    def find_index(self, line_index, char_index=None):
        """
        This method return the total index from a line index and a character index

        Example:
            text = "Hello\n"
                   "world"
            text.find_index(1, 2) -> index between 'o' and 'r'
                                  -> 8

        WARNING : this method result don't always match with text.index('r'), when
                  the text is cut inside a word or after a '-', we need two different
                  indexes for the end of the line and the start of the next line
        """
        if char_index is None:
            return self._find_index(pos=line_index)

        text_index = 0
        for i, line in enumerate(self.lines):
            if i == line_index:
                break
            text_index += len(line.real_text)
        return text_index + char_index

    def _find_indexes(self, pos):
        """
        Renvoie l'index correspondant a l'espace entre deux caracteres le plus proche

        Exemple :
            pos = (40, 23)                             (40eme pixel a partir de self.left, 23eme pixel sous self.top)
            find_index(pos) -> self.find_index(2, 13)  (pos est sur le 14eme caractere de la 3eme ligne)
        """

        if pos[1] < 0:
            return 0, 0
        elif pos[1] >= self.h:
            return len(self.lines) - 1, len(self.lines[-1].text)
        else:
            for line_index, line in enumerate(self.lines):
                if line.bottom > pos[1]:
                    return line_index, line.find_index(pos[0])

        raise Exception

    def _find_indexes_corrected(self, line_index, char_index):

        text_index = 0
        for i, line in enumerate(self.lines):
            if i == line_index:
                break
            text_index += len(line.real_text)
        text_index += char_index
        if text_index < 0: return 0, 0, 0
        if text_index > len(self.text):
            return len(self.text), len(self.lines)-1, len(self.lines[-1].text)

        if not 0 <= char_index <= len(self.lines[line_index].text):
            char_index = text_index
            for line_index, line in enumerate(self.lines):
                if char_index <= len(line.text):
                    assert 0 <= char_index <= len(line.text), char_index
                    break
                char_index -= len(line.real_text)

        assert text_index == self.find_index(line_index, char_index), "{}, {}, {}".format(text_index, line_index, char_index)

        return text_index, line_index, char_index

    def find_indexes(self, text_index=None, line_index=None, char_index=None, pos=None):
        """
        Renvoie l'inverse de self.find_index(line_index, char_index)

        Example:
            text = "Hello\n"
                   "world"
            text.find_indexes(8) -> (1, 2)
        """

        if line_index is not None:
            assert text_index is None
            assert char_index is not None
            assert pos is None
            return self._find_indexes_corrected(line_index=line_index, char_index=char_index)

        if pos is not None:
            assert text_index is None
            assert line_index is None
            assert char_index is None
            return self._find_indexes(pos=pos)

        if text_index < 0: return 0, 0
        char_index = text_index
        for line_index, line in enumerate(self.lines):
            if char_index <= len(line.text):
                assert 0 <= char_index <= len(line.text), char_index
                return line_index, char_index
            char_index -= len(line.real_text)

        # The given text_index is too high
        return line_index, len(line.text)

    def find_mouse_index(self):
        """
        Return the closest index from mouse.x
        """
        return self.find_index(mouse.get_pos_relative_to(self))

    def find_mouse_indexes(self):
        """
        Return the closest indexes from mouse.x
        """
        return self.find_indexes(pos=mouse.get_pos_relative_to(self))

    def _find_pos(self, text_index):

        line_index, char_index = self.find_indexes(text_index=text_index)
        return self.find_pos(line_index=line_index, char_index=char_index)

    def find_pos(self, text_index=None, line_index=None, char_index=None):
        """
        Effectue l'inverse de find_indexes
        La position renvoyee est relative a self.topleft
        """
        if text_index is not None: return self._find_pos(text_index=text_index)
        return self.lines[line_index].find_pixel(char_index), self._lines_pos[line_index]

    def get_selected_data(self):
        if self.is_selectable:
            return ''.join(line.get_selected_data() for line in self.lines)

    def get_text(self):
        return ''.join(line.real_text for line in self.lines)[:-1]  # Discard last \n
    text = property(get_text)

    def lock_text(self, locked=True):

        self.has_locked.text = locked

    def set_max_width(self, max_width):

        assert isinstance(max_width, int)
        assert max_width > 0
        if self._min_width > max_width:
            raise PermissionError(f"The max_width is too little : {max_width}")
        self._max_width = max_width
        self.lock_width(False)
        self.resize_width(self.max_width)
        self.lock_width(True)
        self.set_text(self.get_text())

    def set_text(self, text):

        if self.has_locked.text: return
        with paint_lock:

            first_line = self.lines[0] if self.lines else None
            for child in tuple(self.lines):
                assert child in self.children
                assert self == child.parent
                if child != first_line:
                    child.kill()
            try:
                assert len(self.lines) in (0, 1), self.lines
            except Exception as e:
                raise e

            if first_line is not None:
                first_line.config(text=text, end='\n')
            else:
                LineClass = _SelectableLine if self.is_selectable else _Line
                LineClass(
                    parent=self,
                    text=text,
                    line_index=0,
                )
            self._pack()
            self._name = self.lines[0].text


class DynamicText(Text, Runable):

    def __init__(
        self,
        parent,
        get_text,
        **kwargs
    ):

        assert callable(get_text), get_text

        Text.__init__(
            self,
            parent=parent,
            text=str(get_text()),
            **kwargs
        )
        Runable.__init__(self)

        self.get_new_text = get_text

        self.start_running()

    def run(self):

        new_text = str(self.get_new_text())
        if new_text != self.text:
            self.set_text(new_text)


class TextLabel(Text):
    """
    A TextLabel is a Label who only contains text. The interest of TextLabel is to restrict
    the Text sizes.

    If a width is given, then the Text won't be longer, just like Text.max_width
    If a height is given, same thing, the Text won't be higher.

    When a text is longer than the required width, there is 3 solutions :
        - The text inserts an end of line (solution opered by Text.max_width, not possible in TextLabel)
        - The text font height is reduced
        - The text stay longer, a scroll could allow to read it
    When a text is higher than the required height, there is 2 solutions :
        - The text font height is reduced
        - The text stay higher, a scroll could allow to read it


    """

    def __init__(self, parent, *args, width=None, height=None, scrollable=False, **options):

        assert "max_width" not in options, "Use 'width' instead"
        Text.__init__(self, parent, *args, **options)

        self.set_size(width, height)

    def set_size(self, width=None, height=None):

        if (width is not None) or height is not None:
            if not self.padding.is_null:
                if self.align_mode != "center":
                    print(self.padding)
                    raise PermissionError("Cannot define padding and size on a TextLabel")
            if width is not None:
                plus = (width - self.width) / 2
                self.padding.left += plus
                self.padding.right += plus
            if height is not None:
                plus = (height - self.height) / 2
                self.padding.top += plus
                self.padding.bottom += plus
            self._pack()



