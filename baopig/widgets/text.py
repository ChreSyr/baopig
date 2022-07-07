
from math import inf as math_inf
from baopig.io import mouse
from baopig.font.font import Font
from baopig.lib import *


class _Line(Widget):
    """
    A Line is a widget who only have text on its surface
    It has a transparent background
    It has an end string who is the separator between this line and the next one

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
        Widget.__init__(self, parent=parent, surface=pygame.Surface((parent.w, parent.font.height), pygame.SRCALPHA),
                        layer=parent.lines, name=f"{self.__class__.__name__[1:]}({text})")

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
        return f"{self.__class__.__name__}(index={self.line_index}, text={self.text})"

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
                        if self.text[i - 1] == '-':
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
        while self.parent.lines[i - 1].end != '\n':
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
            line = self.parent.lines[line.line_index + 1]
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
        if self.end != '\v' and index == len(self.real_text) - 1:
            if self.line_index == len(self.parent.lines) - 1:
                return  # pop of end of text
            self.config(end='\v')
        else:
            self.config(text=self.text[:index] + self.text[index + 1:])

    def config(self, text=None, end=None, called_by_constructor=False):

        # if not called_by_constructor:

        with paint_lock:

            if end is not None:
                assert end in ('\n', ' ', '\v')
                if self.parent.width_is_adaptable:
                    assert end == '\n'
                self._end = end
            if text is not None:
                if '\t' in text:
                    text = str.replace(text, '\t', '    ')  # We can also replace it at rendering
                if '\v' in text:
                    text = str.replace(text, '\v', '')
                assert isinstance(text, str)
                self._text = text

            if self.end != '\n' and self.line_index == len(self.parent.lines) - 1:
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
                    text=self.text[self.text.index('\n') + 1:],
                    line_index=self.line_index + .00001
                )
                self._text = self.text[:self.text.index('\n')]

            self.update_char_pos()
            if not self.parent.width_is_adaptable and self.font.get_width(self.text) > self.parent.content_rect.width:

                max_width = self.parent.content_rect.width
                assert self.find_pixel(1) <= max_width, "The availible width is too little : " + str(max_width)

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
                        if end == ' ':
                            index_newline_start += 1
                    self.__class__(
                        parent=self.parent,
                        text=self.text[index_newline_start:],
                        line_index=self.line_index + .00001,  # the line will correct itself
                    )
                    self._end = sep
                    self._text = self.text[0:index_end]
                    self.update_char_pos()

            font_render = self.font.render(self.text)
            surf_w = font_render.get_width()
            surface = pygame.Surface((surf_w, self.font.height), pygame.SRCALPHA)
            surface.blit(font_render, (0, 0))
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


class _SelectableLine(_Line):
    """
    You are selecting a SelectableLine when :
        - A condition described in SelectableWidget is verified
        - A cursor moves while Maj key is pressed
    """

    # TODO : improve Text creation, with less recursion
    # NOTE : this is a temporary way to minimize the recursion
    _selection_ref = lambda self: None  # needed during construction
    _is_selected = False

    def __init__TBR(self, *args, **kwargs):

        self._selection_ref = lambda: None  # needed during construction

        _Line.__init__(self, *args, **kwargs)

        self._is_selected = False

    is_selected = property(lambda self: self._is_selected)
    selection = property(lambda self: self._selection_ref())
    selector = property(lambda self: self._parent.selector)

    def check_select(self, selection_rect):
        """
        Method called by the selector each time the selection_rect rect changes
        The selection_rect has 3 attributes:
            - start
            - end
            - rect (the surface between start and end)
        These attributes are absolutely referenced, wich means they are relative
        to the application. Start and end attributes reffer to the start and end
        of the selection_rect, who will often be caused by a mouse link motion
        """

        assert self.is_alive
        collide_rect = (self.parent.abs.left, self.abs.top, self.parent.abs.w, self.abs.h)

        if selection_rect.abs_rect.colliderect(collide_rect):
            self._is_selected = True
            self.handle_select()
        else:
            if not self.is_selected:
                return
            self._is_selected = False
            self.handle_unselect()

    def get_selected_data(self):
        if self.selection is None:
            return ''
        return self.selection.get_data()

    def handle_select(self):

        selection = self.selector.selection_rect
        if self.selection is None and not selection.w and not selection.h:
            return

        if self.selection is None:
            _LineSelection(self)

        selecting_line_end = False
        if self.abs.top <= selection.start[1] < self.abs.bottom:
            start = self.find_index(selection.start[0] - self.abs.left)
        elif selection.start[1] < self.abs.top:
            start = 0
        else:
            start = len(self.text)
            if self is not self.parent.lines[-1]:
                selecting_line_end = True

        if self.abs.top <= selection.end[1] < self.abs.bottom:
            end = self.find_index(selection.end[0] - self.abs.left)
        elif selection.end[1] < self.abs.top:
            end = 0
        else:
            end = len(self.text)
            if self is not self.parent.lines[-1]:
                selecting_line_end = True

        start, end = sorted((start, end))
        self.selection.config(start, end, selecting_line_end)

    def handle_unselect(self):
        if self.selection is not None:
            self.selection.kill()

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


class _LineSelection(Rectangle):
    """
    A LineSelection is a Rectangle with a light blue color : (167, 213, 255, 127)
    Each Line can have a LineSelection

    When you click on a SelectableLine, and then move the mouse while its pressed,
    you are selecting the SelectableLine
    The size and the position of the LineSelection object change according to your mouse

    When you double-click on a SelectableLine, it selects a word
    When you triple-click on a SelectableLine, it selects the whole line text
    """

    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        color="theme-color-selection",
        border_width=0
    )

    def __init__(self, line):

        assert isinstance(line, _SelectableLine)

        self._line_index = line.line_index
        Rectangle.__init__(self,
                           parent=line.parent,
                           pos=line.topleft,
                           size=(0, line.h),
                           name=line.name + " -> selection"
                           )

        # self.is_selecting = False  # True if the user is pressing the mouse button for a selection
        self._index_start = self._index_end = 0
        self._is_selecting_line_end = False
        self._line_ref = line.get_weakref()

        # Initializations
        # self.move_behind(self.line)
        self.line._selection_ref = self.get_weakref()
        self.line.signal.KILL.connect(self.kill, owner=self)
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

    def get_data(self):
        end = self.line.end if self._is_selecting_line_end else ''
        if end == '\v':
            end = ''
        return self.line.text[self.index_start:self.index_end] + end

    def set_end(self, index, selecting_line_end):

        self._index_end = index
        self._is_selecting_line_end = selecting_line_end
        if selecting_line_end:
            assert self.line is not self.parent.lines[-1]

        if self._is_selecting_line_end:
            self.resize_width(self.line.parent.width -  # parent because it goes all the way long, further than line.w
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

        if self.is_asleep:
            self.wake()
        self.show()


class Text(Zone, SelectableWidget):
    STYLE = Zone.STYLE.substyle()
    STYLE.modify(
        width=0,
        height=0,
    )
    STYLE.create(
        align_mode="left",
        font_file=None,
        font_height=15,
        font_color="theme-color-font",
        font_bold=False,
        font_italic=False,
        font_underline=False,
        selectable=True,

        # WARNING : the two following style attributes are very consuming when set to False
        height_is_adaptable=None,  # by default, True if height is > 0, False otherwise
        width_is_adaptable=None,
    )
    STYLE.set_type("align_mode", str)
    STYLE.set_type("font_height", int)
    STYLE.set_type("font_color", Color)
    STYLE.set_type("font_bold", bool)
    STYLE.set_type("font_italic", bool)
    STYLE.set_type("font_underline", bool)
    STYLE.set_type("selectable", bool)
    STYLE.set_constraint("align_mode", lambda val: val in ("left", "center", "right"),
                         "must be 'left', 'center' or 'right'")
    STYLE.set_constraint("font_height", lambda val: val > 0, "a text must have a positive font height")
    STYLE.set_constraint("font_file", lambda val: (val is None) or isinstance(val, str), "must be None or a string")

    def __init__(self, parent, text=None, **kwargs):

        Zone.__init__(self, parent, **kwargs)
        SelectableWidget.__init__(self, parent)

        self._height_is_adaptable = self.style["height_is_adaptable"]
        if self._height_is_adaptable is None:
            self._height_is_adaptable = self.h == 0
            self.style.modify(height_is_adaptable=self._height_is_adaptable)
        elif self._height_is_adaptable is False and self.h == 0:
            raise PermissionError("When 'height_is_adaptable' is set to False, 'height' must also be set")
        self._width_is_adaptable = self.style["width_is_adaptable"]
        if self._width_is_adaptable is None:
            self._width_is_adaptable = self.w == 0
            self.style.modify(width_is_adaptable=self._width_is_adaptable)
        elif self._width_is_adaptable is False and self.w == 0:
            raise PermissionError("When 'width_is_adaptable' is set to False, 'width' must also be set")

        self._font = Font(self)
        self._min_width = self.font.get_width("m")
        self._is_selectable = self.style["selectable"]
        self._lines_pos = []
        self._align_mode = self.style["align_mode"]
        self._padding = self.style["padding"]
        self._has_locked.text = False

        self.line_selections = Layer(self, _LineSelection, name="line_selections", touchable=False, sort_by_pos=True)
        self.lines = Layer(self, _Line, name="lines", default_sortkey=lambda line: line.line_index)
        self.set_text(text)

    align_mode = property(lambda self: self._align_mode)
    font = property(lambda self: self._font)
    height_is_adaptable = property(lambda self: self._height_is_adaptable)
    is_selectable = property(lambda self: self._is_selectable)
    padding = property(lambda self: self._padding)
    width_is_adaptable = property(lambda self: self._width_is_adaptable)

    def set_adaptable_size(self, width, height):
        """
        Example:
            widget = Text(parent, "Hello world", font_file=None)
            print(widget.size)  # -> prints (82, 15)
            widget.set_adaptable_size(width=False, height=False)
            widget.set_text("Hello world and everyone else")  # -> here, the font_height will be reduced
        """

        self._height_is_adaptable = height
        self._width_is_adaptable = width

    def _pack(self):

        centerx = None  # warning shut down
        if self.align_mode == "center":  # only usefull for the widget creation
            if self._width_is_adaptable:
                centerx = max(line.w for line in self.lines) / 2 + self.content_rect.left
            else:
                centerx = self.content_rect.centerx

        self.lines.sort()
        # TODO : test with windowed text aligned to the center, content_rect might not be a good solution
        h = self.content_rect.top
        for i, line in enumerate(self.lines):
            line._line_index = i
            line.top = h
            h = line.bottom
            if self.align_mode == "left":
                line.left = self.content_rect.left
            elif self.align_mode == "center":
                line.centerx = centerx
            elif self.align_mode == "right":
                line.right = self.content_rect.right

        # Adaptable resize
        if self._height_is_adaptable and self._width_is_adaptable:
            right = max(line.right for line in self.lines)
            bottom = max(line.bottom for line in self.lines)
            assert bottom == self.lines[-1].bottom
            self.resize(w=right + self.padding.right, h=bottom + self.padding.bottom)
        elif self._height_is_adaptable:
            bottom = max(line.bottom for line in self.lines)
            assert bottom == self.lines[-1].bottom
            if bottom + self.padding.bottom != self.h:  # TODO : without this line, the printing bug, find why
                self.resize_height(bottom + self.padding.bottom)
        elif self._width_is_adaptable:
            right = max(line.right for line in self.lines)
            self.resize_width(right + self.padding.right)

        # New positions in _lines_pos
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

    def find_index(self, line_index, char_index):
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

    def find_indexes(self, text_index):
        """
        Renvoie l'inverse de self.find_index(line_index, char_index)

        Example:
            text = "Hello\n"
                   "world"
            text.find_indexes(8) -> (1, 2) (index is between 'wo' & 'rld')
        """

        if text_index < 0:
            return 0, 0

        for line_index, line in enumerate(self.lines):
            if text_index <= len(line.text):
                return line_index, text_index
            text_index -= len(line.real_text)

        # The given text_index is too high
        return len(self.lines), len(self.lines[-1].text)

    def _find_mouse_index(self):
        """
        Return the closest index from mouse.x
        """
        return self._find_index(pos=mouse.get_pos_relative_to(self))

    def get_text(self):
        return ''.join(line.real_text for line in self.lines)[:-1]  # Discard last \n

    text = property(get_text)

    def pack(self, *args, **kwargs):

        raise PermissionError("Should not use this method on a Text")

    def resize(self, w, h):
        # NOTE : resizing a Text with adaptable size will set the size fixed, non-adaptable

        old_size = self.content_rect.size
        super().resize(w, h)

        if self._width_is_adaptable:
            lines_width = max(line.w for line in self.lines)
            if self.content_rect.w != lines_width:
                self._width_is_adaptable = False
                self.set_text(self.get_text())
        else:
            lines_width = old_size[0]
            if self.content_rect.w != lines_width:
                self.set_text(self.get_text())

        if self._height_is_adaptable:
            lines_height = self.lines[-1].bottom - self.content_rect.top
            if self.content_rect.h != lines_height:
                self._height_is_adaptable = False
                self.set_text(self.get_text())
        else:
            lines_height = old_size[1]
            if self.content_rect.h != lines_height:
                self.set_text(self.get_text())

    def set_text(self, text):

        if self.has_locked("text"):
            return

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
                line_class = _SelectableLine if self.is_selectable else _Line
                line_class(
                    parent=self,
                    text=text,
                    line_index=0,
                )

            self._pack()
            self._name = self.lines[0].text

            if not self.height_is_adaptable and self.lines[-1].bottom > self.content_rect.bottom:
                while self.lines[-1].bottom > self.content_rect.bottom:
                    if self.font.height == 2:
                        raise ValueError(
                            f"This text is too long for the text area : {text} (area={self.content_rect}), "
                            f"{self.align_mode}, {self.width}")
                    self.font.config(height=self.font.height - 1)  # changing the font automatically updates the text

    # Selectable methods
    def check_select(self, selection_rect):

        if not self.is_selectable:
            return

        for line in self.lines:
            line.check_select(selection_rect)
        self._is_selected = True in tuple((line.is_selected for line in self.lines))

    def get_selected_data(self):

        if self.is_selected:
            return ''.join(line.get_selected_data() for line in self.lines)

    def handle_selector_link(self):

        if not self.is_selectable:
            return

        if not self.collidemouse():
            return

        if mouse.has_triple_clicked:
            for line in self.lines:
                if line.abs.top <= mouse.y < line.abs.bottom:
                    with paint_lock:
                        self.selector.close_selection()
                        self.selector.start_selection((line.abs.left, line.abs.top))
                        self.selector.end_selection((line.abs.right, line.abs.top), visible=False)
                        return
        elif mouse.has_double_clicked:
            for line in self.lines:
                if line.abs.top <= mouse.y < line.abs.bottom:
                    line.select_word(line.find_mouse_index())

    def handle_unselect(self):

        if not self.is_selectable:
            return

        for line in self.lines:
            line.handle_unselect()


class DynamicText(Text, Runable):

    def __init__(self, parent, get_text, **kwargs):
        assert callable(get_text), get_text

        Text.__init__(self, parent=parent, text=str(get_text()), **kwargs)
        Runable.__init__(self, parent)

        self._get_new_text = get_text

        self.start_running()

    def run(self):
        new_text = str(self._get_new_text())
        if new_text != self.text:
            self.set_text(new_text)
