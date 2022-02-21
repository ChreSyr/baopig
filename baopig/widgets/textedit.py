

from baopig.pybao.objectutilities import PrefilledFunction, Object, TypedDeque
from baopig._lib import *
from .text import Text, _LineSelection


# TODO : LineEntry (with select_all_on_focus and exec_on_defocus)
# TODO : solve arrows
# TODO : presentation text when nothing is in the text ?

class TextEdit(Text, Selector):

    STYLE = Text.STYLE.substyle()
    STYLE.modify(
        width = 100,
        background_color = "theme-color-font_opposite",
    )

    def __init__(self,
        parent,
        text=None,
        pos=None,
        font=None,
        font_color=None,
        font_height=None,
        width=None,
        **kwargs
    ):

        if text is None: text = ""
        if "max_width" in kwargs:
            raise PermissionError("Use width instead of max_width")

        self.inherit_style(parent, width=width)

        Text.__init__(self,
            parent=parent,
            text=text,
            pos=pos,
            font=font,
            color=font_color,
            font_height=font_height,
            max_width=self.style["width"],
            selectable=True,
            **kwargs
        )
        Selector.__init__(self)
        self.enable_selecting(True)

        self._cursor_ref = lambda: None

        self.set_background_color((255, 255, 255))
        self.cursors_layer = Layer(self, Cursor, name="cursors_layer", touchable=False)
        # self.layers.add_layer("cursors", CompsClass=Cursor, touchable=False)
        self.set_selectionrect_visibility(False)

    cursor = property(lambda self: self._cursor_ref())

    def accept(self, text):
        if text == '': return False
        return True

    def cut(self):

        self.copy()
        self.del_selected_data()

    def del_selected_data(self):

        if not self.is_selecting: return
        cursor_index = self.find_index(char_index=self.line_selections[0].index_start,
                                       line_index=self.line_selections[0].line.line_index)
        assert self.is_selecting
        selected_comps = tuple(self.selectables.selected)
        if selected_comps:
            if self.cursor is not None:
                self.cursor.save()
            for line in selected_comps:
                line._text = line.text[:line.selection.index_start] + line.text[line.selection.index_end:]
                line._end = '' if line.selection._is_selecting_line_end else line.end
            line.config()
        self.close_selection()
        self.cursor.config(text_index=cursor_index)

    def end_selection(self, abs_pos, visible=None):

        if self.selection_rect.end != abs_pos:
            super().end_selection(abs_pos, visible)
            # self.selection_rect.end is one pixel lower and on x axis than abs_pos, so we don't use it in this calculation
            pos = (self.selection_rect.end[0] - self.abs.left, self.selection_rect.end[1] - self.abs.top)
            line_index, char_index = self.find_indexes(pos=pos)
            if line_index != self.cursor.line_index or char_index != self.cursor.char_index:
                self.cursor.config(line_index=line_index, char_index=char_index, selecting="done")

    def handle_focus(self):
        assert self.cursor is None

        mouse_pos = mouse.get_pos_relative_to(self.parent)

        w = abs(self.rect.left - mouse_pos[0])
        h = abs(self.rect.top - mouse_pos[1])

        line_index = len(self.lines) - 1
        char_index = len(self.lines[-1].text)

        Cursor(self, line_index=line_index, char_index=char_index)

    def handle_keydown(self, key):

        self.cursor.handle_keydown(key)

    def handle_link(self):
        if not mouse.has_double_clicked:  # else, the cursor follow the selection
            self.cursor.config(text_index=self.find_mouse_index())

    def paste(self, data):

        self.cursor.write(data)

    def set_text(self, text):

        self._selection_start = None
        super().set_text(text)


class HaveHistory:

    def __init__(self):

        """
        An History element is created when :
            - A new text insert
            - A part of text pop
            - Just before a selected data is delete

        An History element store these data :
            - the entire text of parent
            - the cusror indexes (line and char)
            - the selection start and end, if the parent was selecting
        """
        max_item_stored = 50
        self.history = TypedDeque(Object, maxlen=max_item_stored)
        self.back_history = TypedDeque(Object, maxlen=max_item_stored)

    def redo(self):
        """
        Restaure la derniere modification
        """
        if self.back_history:

            backup = self.back_history.pop()  # last element of self.back_history, the current state
            self.history.append(backup)

            backup = self.history[-1]
            self.parent.set_text(backup.text)
            self.config(line_index=backup.cursor_line_index, char_index=backup.cursor_char_index, save=False)
            if backup.selection_start is not None:
                if self.parent.is_selecting:
                    self.parent.close_selection()
                self.parent.start_selection(backup.selection_start)
                self.parent.end_selection(backup.selection_end)

        # else:
        #     LOGGER.info("Cannot redo last operation because the operations history is empty")

    def save(self):

        # if self.parent.is_selecting:
        current = Object(
            text=self.parent.text,
            cursor_line_index=self.line_index,
            cursor_char_index=self.char_index,
            selection_start=self.parent.selection_rect.start if self.parent.selection_rect else None,
            selection_end=self.parent.selection_rect.end if self.parent.selection_rect else None
        )
        self.history.append(current)
        self.back_history.clear()

    def undo(self):
        """
        Annule la derniere modification
        """
        if len(self.history) > 1:  # need at least 2 elements in history

            backup = self.history.pop()  # last element of self.history, which is the state before undo()
            self.back_history.append(backup)

            previous = self.history[-1]
            self.parent.set_text(previous.text)
            self.config(line_index=previous.cursor_line_index, char_index=previous.cursor_char_index, save=False)
            if previous.selection_start is not None:
                if self.parent.is_selecting:
                    self.parent.close_selection()
                self.parent.start_selection(previous.selection_start)
                self.parent.end_selection(previous.selection_end)
        # else:
        #     LOGGER.info("Cannot undo last operation because the operations history is empty")


class Cursor(Rectangle, HaveHistory, RepetivelyAnimated):
    """
    By default, at creation, a cursor is set at mouse position
    """

    def __init__(self, parent, line_index, char_index):

        assert isinstance(parent, TextEdit)
        assert parent.cursor is None

        h = parent.font.height

        Rectangle.__init__(
            self,
            parent=parent,
            pos=(parent.lines[line_index].find_pixel(char_index), parent.lines[line_index].top),
            size=(int(h / 10), h),
            color=ressources.font.color,
            name=parent.name + " -> cursor"
        )
        HaveHistory.__init__(self)
        RepetivelyAnimated.__init__(self, interval=.5)

        self._char_index = None  # index of cursor position, see _Line._chars_pos for more explanations
        self.__line_index = None  # index of cursor line, see Text._lines_pos for more explanations
        self._line = None
        self._text_index = None  # index of cusor in Text.text

        self.parent._cursor_ref = self.get_weakref()
        self.connect("kill", self.parent.signal.DEFOCUS)
        self.swap_layer("cursors_layer")
        self.set_nontouchable()
        self.start_animation()

        self.config(line_index=line_index, char_index=char_index)

    char_index = property(lambda self: self._char_index)
    def _set_line_index(self, li):
        self.__line_index = li
        self._line = self._parent.lines[li]
    _line_index = property(lambda self: self.__line_index, _set_line_index)
    line_index = property(lambda self: self.__line_index)
    line = property(lambda self: self._line)
    text_index = property(lambda self: self._text_index)

    def config(self, text_index=None, line_index=None, char_index=None, selecting=False, save=True):
        """
        Place the cursor at line n° line_index and before the character n° char_index, count from 0
        If text_index is given instead of line_index and char_index, we use parent.find_indexes

        If char_index is at the end of a cutted line (a line too big for the text max_width), then
        the cursor can either be on the end of the line or at the start of the next line, it is
        algorithmically the same. So the object who config the cursor will decide where to place the
        cursor. It can give a float value for text_index (like 5.4) wich mean "Hey, if the cursor is
        at the end of a cutted line, let it move the start of the next one." In this exemple, the
        text_index value will be 5. This works also with char_index = 5.4
        """

        if text_index is not None:
            assert line_index is None
            assert char_index is None
            line_index, char_index = self.parent.find_indexes(text_index=text_index)
            assert text_index == self.parent.find_index(line_index, char_index)
        else:
            assert char_index is not None
            if line_index is None:
                text_index, line_index, char_index = self.parent.find_indexes(line_index=self.line_index, char_index=char_index)
            else:
                text_index = self.parent.find_index(line_index, char_index)

        assert text_index == self.parent.find_index(line_index, char_index)

        if selecting is True and self.parent.selection_rect.start is None:
            pos = self.parent.find_pos(self.text_index)
            abs_pos = self.parent.abs_left + pos[0], self.parent.abs_top + pos[1]
            self.parent.start_selection(abs_pos)

        def fit(v, min, max):
            if v < min: v = min
            elif v > max: v = max
            return v

        self._text_index = fit(text_index, 0, len(self.parent.text))
        self._line_index = fit(line_index, 0, len(self.parent.lines))
        self._char_index = fit(char_index, 0, len(self.line.text))

        # print("Set cursor at :", self.text_index, self.line_index, self.char_index, selecting, save)

        if self.char_index == len(self.line.text_with_end):
            LOGGER.warning("Tricky cursor position")

        if self.get_weakref()._comp is None:
            LOGGER.warning('This component should be dead :', self)

        old_pos = self.topleft
        self.y = self.line.y
        self.x = self.line.find_pixel(self.char_index)

        """if self.x > self.parent.w - self.w:
            dx = self.x - (self.parent.w - self.w)
            self.x -= dx
            self.line.x -= dx  # TODO : scroll text

        if self.x < 0:
            dx = - self.x
            self.x += dx
            self.line.x += dx"""  # TODO : scroll text

        self.start_animation()
        self.show()

        if selecting is "done":
            pass
        elif selecting is True:
            if self.parent.selection_rect.end is None or old_pos != self.pos:
                self.parent.end_selection((self.abs_left, self.abs_top))
        elif selecting is False:
            if self.parent.is_selecting:
                self.parent.close_selection()
        else:
            raise PermissionError

        if save and (not self.history or self.parent.text != self.history[-1].text):
            self.save()

    def handle_keydown(self, key):
        """
        N'accepte que les evenements du clavier
        Si la touche est speciale, effectue sa propre fonction
        Modifie le placement du curseur
        """

        # Cmd + ...
        if keyboard.mod.cmd:
            # Maj + Cmd + ...
            if keyboard.mod.maj:
                if key == keyboard.z:
                    self.redo()
                return
            elif keyboard.mod.ctrl or keyboard.mod.alt:
                return
            elif key == keyboard.d:
            # Duplicate
                selected_data = self.parent.get_selected_data()
                if selected_data == '':
                    selected_data = self.line.real_text
                    self.line.insert(0, selected_data)
                else:
                    self.parent.close_selection()
                    self.line.insert(self.char_index, selected_data)
                self.config(text_index=self.text_index + len(selected_data))
            elif key == keyboard.r:
            # Execute
                try:
                    exec(self.parent.text)
                except Exception as e:
                    LOGGER.warning("CommandError: "+str(e))
            elif key == keyboard.z:
                self.undo()
            elif key in (keyboard.LEFT, keyboard.HOME):
                self.config(self.parent.find_index(line_index=self.line_index, char_index=0), selecting=keyboard.mod.maj)
            elif key in (keyboard.RIGHT, keyboard.END):
                self.config(self.parent.find_index(line_index=self.line_index, char_index=len(self.line.text)), selecting=keyboard.mod.maj)
            elif key == keyboard.UP:
                if self.line_index > 0:
                    self.config(line_index=0,
                                char_index=self.parent.lines[0].find_index(self.rect.left),
                                selecting=keyboard.mod.maj)
            elif key == keyboard.DOWN:
                if self.line_index < len(self.parent.lines)-1:
                    self.config(line_index=len(self.parent.lines)-1,
                                char_index=self.parent.lines[len(self.parent.lines)-1].find_index(self.rect.left),
                                selecting=keyboard.mod.maj)
            return

        # Cursor movement
        if 272 < key < 282 and key != 277:

            if key in (keyboard.LEFT, keyboard.RIGHT):

                if keyboard.mod.alt:  # go to word side
                    if key == keyboard.LEFT:
                        if self.char_index == 0: return
                        self.config(text_index=self.text_index - 1, selecting=keyboard.mod.maj)
                        while self.char_index > 0 and \
                                (self.line.text[self.char_index-1] != ' ' or self.line.text[self.char_index] == ' '):
                            self.config(text_index=self.text_index - 1, selecting=keyboard.mod.maj)
                    elif key == keyboard.RIGHT:
                        if self.char_index == len(self.line.text): return
                        self.config(text_index=self.text_index + 1, selecting=keyboard.mod.maj)
                        while self.char_index < len(self.line.text) and \
                                (self.line.text[self.char_index-1] != ' ' or self.line.text[self.char_index] == ' '):
                            self.config(text_index=self.text_index + 1, selecting=keyboard.mod.maj)
                elif (not keyboard.mod.maj) and self.parent.is_selecting:
                    if key == keyboard.LEFT:
                        self.config(line_index=self.parent.line_selections[0].line_index,
                                    char_index=self.parent.line_selections[0].index_start)
                    elif key == keyboard.RIGHT:
                        self.config(line_index=self.parent.line_selections[-1].line_index,
                                    char_index=self.parent.line_selections[-1].index_end)
                elif key == keyboard.LEFT:
                    self.config(char_index=self.char_index-1,
                                selecting=keyboard.mod.maj)
                    # self.config(text_index=self.text_index - 1, selecting=keyboard.mod.maj)
                elif key == keyboard.RIGHT:
                    self.config(char_index=self.char_index+1,
                                selecting=keyboard.mod.maj)
                    # self.config(text_index=self.text_index + 1, selecting=keyboard.mod.maj)

            elif key in (keyboard.HOME, keyboard.END):
                if key == keyboard.HOME:  # Fn + K_LEFT
                    self.config(self.parent.find_index(line_index=self.line_index, char_index=0), selecting=keyboard.mod.maj)
                elif key == keyboard.END:  # Fn + K_RIGHT
                    self.config(self.parent.find_index(line_index=self.line_index, char_index=len(self.line.text)), selecting=keyboard.mod.maj)

            elif key in (keyboard.UP, keyboard.DOWN):
                if key == keyboard.UP:
                    if self.line_index > 0:
                        self.config(line_index=self.line_index-1,
                                    char_index=self.parent.lines[self.line_index-1].find_index(self.rect.left),
                                    selecting=keyboard.mod.maj)
                if key == keyboard.DOWN:
                    if self.line_index < len(self.parent.lines)-1:
                        self.config(line_index=self.line_index+1,
                                    char_index=self.parent.lines[self.line_index+1].find_index(self.rect.left),
                                    selecting=keyboard.mod.maj)

            elif key in (keyboard.PAGEUP, keyboard.PAGEDOWN):
                if key == keyboard.PAGEUP:
                    if self.line_index > 0:
                        self.config(line_index=0,
                                    char_index=self.parent.lines[0].find_index(self.rect.left),
                                    selecting=keyboard.mod.maj)
                if key == keyboard.PAGEDOWN:
                    if self.line_index < len(self.parent.lines)-1:
                        self.config(line_index=len(self.parent.lines)-1,
                                    char_index=self.parent.lines[len(self.parent.lines)-1].find_index(self.rect.left),
                                    selecting=keyboard.mod.maj)

        # Suppression
        elif key == keyboard.BACKSPACE:
            if self.parent.is_selecting:
                self.parent.del_selected_data()
            elif self.line_index > 0 or self.char_index > 0:
                if self.char_index > 0:
                    self.line.pop(self.char_index-1)
                else:
                    self.parent.lines[self.line_index - 1].pop(-1)
                old = self.text_index
                self.config(text_index=self.text_index - 1)
                assert self.text_index == old - 1

        elif key == keyboard.DELETE:
            if self.parent.is_selecting:
                self.parent.del_selected_data()
            if self.line.end == '\v' and self.char_index == len(self.line.text):
                if self.line_index < len(self.parent.lines) - 1:
                    self.parent.lines[self.line_index + 1].pop(0)
            else:
                self.line.pop(self.char_index)
            self.config(line_index=self.line_index,  # We don't use text_index because, if self.char_index is 0,
                        char_index=self.char_index)  # we want to stay at 0, text_index might send the cursor at the
                                                     # end of the previous line if it is a cutted line

        elif key == keyboard.ESCAPE:
            self.parent.defocus()

        elif keyboard.F1 <= key <= keyboard.F15:
            return

        # Write
        else:
            assert keyboard.last_event.key == key
            unicode = keyboard.last_event.unicode
            if key == keyboard.RETURN:
                unicode = '\n'
            elif key == keyboard.TAB:
                unicode = '    '
            self.write(unicode)

    def write(self, string):

            # Lettres (minuscules et majuscules)
            text = self.parent.text[:self.char_index] + string + self.parent.text[self.char_index:]
            if self.parent.accept(text):

                if self.parent.is_selecting:
                    self.parent.del_selected_data()

                self.line.insert(self.char_index, string)
                self.config(text_index=self.text_index + len(string))

