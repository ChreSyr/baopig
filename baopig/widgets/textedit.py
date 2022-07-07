

from baopig.pybao.objectutilities import Object, deque
from baopig.io import keyboard, mouse, LOGGER
from baopig.lib import *
from .text import Text


# TODO : LineEntry (with select_all_on_focus and exec_on_defocus)
# TODO : solve arrows
# TODO : presentation text when nothing is in the text ?


class TextEdit(Text, Selector):

    STYLE = Text.STYLE.substyle()
    STYLE.modify(
        width=100,
        background_color="theme-color-font_opposite",
    )

    def __init__(self, parent, text="", **kwargs):

        Text.__init__(self, parent=parent, text=text, selectable=True, **kwargs)
        Selector.__init__(self, parent)

        self.set_selectionrect_visibility(False)
        self.selector.selectables.remove(self)  # remove this Text from the Selector parent
        self._selector_ref = self.get_weakref()  # make this Text its own Selector
        self.selector.selectables.add(self)

        self._cursor_ref = lambda: None
        self.cursors_layer = Layer(self, Cursor, name="cursors_layer", touchable=False)

    cursor = property(lambda self: self._cursor_ref())

    def accept(self, text):
        if text == '': return False
        return True

    def del_selection_data(self):

        if not self.is_selected: return
        cursor_index = self.find_index(char_index=self.line_selections[0].index_start,
                                       line_index=self.line_selections[0].line.line_index)
        assert self.is_selecting
        selected_lines = tuple(line for line in self.lines if line.is_selected)
        if selected_lines:
            if self.cursor is not None:
                self.cursor.save()
            for line in selected_lines:
                line._text = line.text[:line.selection.index_start] + line.text[line.selection.index_end:]
                line._end = '' if line.selection._is_selecting_line_end else line.end
            line.config()
        self.close_selection()
        self.cursor.config(text_index=cursor_index)

    def end_selection(self, *args, **kwargs):

        super().end_selection(*args, **kwargs)

        pos = (self.selection_rect.end[0] - self.abs.left, self.selection_rect.end[1] - self.abs.top)
        line_index, char_index = self._find_indexes(pos=pos)
        if line_index != self.cursor.line_index or char_index != self.cursor.char_index:
            self.cursor.config(line_index=line_index, char_index=char_index, selecting="done")

    def handle_defocus(self):

        self.cursor.sleep()

    def handle_focus(self):

        line_index = len(self.lines) - 1
        char_index = len(self.lines[-1].text)

        if self.cursor is None:
            Cursor(self, line_index=line_index, char_index=char_index)
        else:
            self.cursor.wake()
            self.cursor.config(line_index=line_index, char_index=char_index)

    def handle_keydown(self, key):

        if keyboard.mod.ctrl:
            if key in (pygame.K_a, pygame.K_c, pygame.K_v, pygame.K_x):
                return super().handle_keydown(key)
        self.cursor.handle_keydown(key)

    def handle_link(self):

        super().handle_link()

        if not mouse.has_double_clicked and not mouse.has_triple_clicked:  # else, the cursor follow the selection
            self.cursor.config(text_index=self._find_mouse_index())

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
        self.history = deque(maxlen=max_item_stored)
        self.back_history = deque(maxlen=max_item_stored)

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
    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        color="theme-color-font"
    )

    def __init__(self, parent, line_index, char_index):

        assert isinstance(parent, TextEdit)
        assert parent.cursor is None

        h = parent.font.height

        Rectangle.__init__(
            self,
            parent=parent,
            pos=(parent.lines[line_index].find_pixel(char_index), parent.lines[line_index].top),
            size=(int(h / 10), h),
            # color=ressources.font.color,
            name=parent.name + " -> cursor"
        )
        HaveHistory.__init__(self)
        RepetivelyAnimated.__init__(self, parent, interval=.5)

        self._char_index = None  # index of cursor position, see _Line._chars_pos for more explanations
        self.__line_index = None  # index of cursor line, see Text._lines_pos for more explanations
        self._line = None
        self._text_index = None  # index of cusor in Text.text

        self.parent._cursor_ref = self.get_weakref()
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

        If char_index is at the end of a cutted line (a line too big for the text width), then
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
        else:
            assert char_index is not None
            assert line_index is not None
            text_index = self.parent.find_index(line_index, char_index)

        assert text_index == self.parent.find_index(line_index, char_index)

        if selecting is True and self.parent.selection_rect.start is None:
            pos = self.parent.find_pos(self.text_index)
            abs_pos = self.parent.abs_left + pos[0], self.parent.abs_top + pos[1]
            self.parent.start_selection(abs_pos)

        def fit(v, mini, maxi):
            if v < mini:
                v = mini
            elif v > maxi:
                v = maxi
            return v

        self._text_index = fit(text_index, 0, len(self.parent.text))
        self._line_index = fit(line_index, 0, len(self.parent.lines))
        self._char_index = fit(char_index, 0, len(self.line.text))

        if self.char_index == len(self.line.text_with_end):
            LOGGER.warning("Tricky cursor position")

        if self.get_weakref()._ref is None:
            LOGGER.warning('This widget should be dead :', self)

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

        if selecting == "done":
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
        if keyboard.mod.ctrl:
            # Maj + Cmd + ...
            if keyboard.mod.maj:
                if key == pygame.K_z:
                    self.redo()
                return
            elif keyboard.mod.cmd or keyboard.mod.alt:
                return
            elif key == pygame.K_d:
            # Duplicate
                selected_data = self.parent.get_selection_data()
                if selected_data == '':
                    selected_data = self.line.real_text
                    self.line.insert(0, selected_data)
                else:
                    self.parent.close_selection()
                    self.line.insert(self.char_index, selected_data)
                self.config(text_index=self.text_index + len(selected_data))
            elif key == pygame.K_r:
            # Execute
                try:
                    exec(self.parent.text)
                except Exception as e:
                    LOGGER.warning("CommandError: "+str(e))
            elif key == pygame.K_z:
                self.undo()
            elif key in (pygame.K_LEFT, pygame.K_HOME):
                self.config(self.parent.find_index(line_index=self.line_index, char_index=0), selecting=keyboard.mod.maj)
            elif key in (pygame.K_RIGHT, pygame.K_END):
                self.config(self.parent.find_index(line_index=self.line_index, char_index=len(self.line.text)), selecting=keyboard.mod.maj)
            elif key == pygame.K_UP:
                if self.line_index > 0:
                    self.config(line_index=0,
                                char_index=self.parent.lines[0].find_index(self.rect.left),
                                selecting=keyboard.mod.maj)
            elif key == pygame.K_DOWN:
                if self.line_index < len(self.parent.lines)-1:
                    self.config(line_index=len(self.parent.lines)-1,
                                char_index=self.parent.lines[len(self.parent.lines)-1].find_index(self.rect.left),
                                selecting=keyboard.mod.maj)
            return

        # Cursor movement
        if 272 < key < 282 and key != 277:  # TODO : update (doesn't work with pygame v2)

            if key in (pygame.K_LEFT, pygame.K_RIGHT):

                if keyboard.mod.alt:  # go to word side
                    if key == pygame.K_LEFT:
                        if self.char_index == 0: return
                        self.config(text_index=self.text_index - 1, selecting=keyboard.mod.maj)
                        while self.char_index > 0 and \
                                (self.line.text[self.char_index-1] != ' ' or self.line.text[self.char_index] == ' '):
                            self.config(text_index=self.text_index - 1, selecting=keyboard.mod.maj)
                    elif key == pygame.K_RIGHT:
                        if self.char_index == len(self.line.text): return
                        self.config(text_index=self.text_index + 1, selecting=keyboard.mod.maj)
                        while self.char_index < len(self.line.text) and \
                                (self.line.text[self.char_index-1] != ' ' or self.line.text[self.char_index] == ' '):
                            self.config(text_index=self.text_index + 1, selecting=keyboard.mod.maj)
                elif (not keyboard.mod.maj) and self.parent.is_selecting:
                    if key == pygame.K_LEFT:
                        self.config(line_index=self.parent.line_selections[0].line_index,
                                    char_index=self.parent.line_selections[0].index_start)
                    elif key == pygame.K_RIGHT:
                        self.config(line_index=self.parent.line_selections[-1].line_index,
                                    char_index=self.parent.line_selections[-1].index_end)
                elif key == pygame.K_LEFT:
                    self.config(char_index=self.char_index-1,
                                selecting=keyboard.mod.maj)
                    # self.config(text_index=self.text_index - 1, selecting=keyboard.mod.maj)
                elif key == pygame.K_RIGHT:
                    self.config(char_index=self.char_index+1,
                                selecting=keyboard.mod.maj)
                    # self.config(text_index=self.text_index + 1, selecting=keyboard.mod.maj)

            elif key in (pygame.K_HOME, pygame.K_END):
                if key == pygame.K_HOME:  # Fn + K_LEFT
                    self.config(self.parent.find_index(line_index=self.line_index, char_index=0), selecting=keyboard.mod.maj)
                elif key == pygame.K_END:  # Fn + K_RIGHT
                    self.config(self.parent.find_index(line_index=self.line_index, char_index=len(self.line.text)), selecting=keyboard.mod.maj)

            elif key in (pygame.K_UP, pygame.K_DOWN):
                if key == pygame.K_UP:
                    if self.line_index > 0:
                        self.config(line_index=self.line_index-1,
                                    char_index=self.parent.lines[self.line_index-1].find_index(self.rect.left),
                                    selecting=keyboard.mod.maj)
                if key == pygame.K_DOWN:
                    if self.line_index < len(self.parent.lines)-1:
                        self.config(line_index=self.line_index+1,
                                    char_index=self.parent.lines[self.line_index+1].find_index(self.rect.left),
                                    selecting=keyboard.mod.maj)

            elif key in (pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                if key == pygame.K_PAGEUP:
                    if self.line_index > 0:
                        self.config(line_index=0,
                                    char_index=self.parent.lines[0].find_index(self.rect.left),
                                    selecting=keyboard.mod.maj)
                if key == pygame.K_PAGEDOWN:
                    if self.line_index < len(self.parent.lines)-1:
                        self.config(line_index=len(self.parent.lines)-1,
                                    char_index=self.parent.lines[len(self.parent.lines)-1].find_index(self.rect.left),
                                    selecting=keyboard.mod.maj)

        # Suppression
        elif key == pygame.K_BACKSPACE:
            if self.parent.is_selected:
                self.parent.del_selection_data()
            elif self.line_index > 0 or self.char_index > 0:
                if self.char_index > 0:
                    self.line.pop(self.char_index-1)
                else:
                    self.parent.lines[self.line_index - 1].pop(-1)
                old = self.text_index
                self.config(text_index=self.text_index - 1)
                assert self.text_index == old - 1

        elif key == pygame.K_DELETE:
            if self.parent.is_selected:
                self.parent.del_selection_data()
            if self.line.end == '\v' and self.char_index == len(self.line.text):
                if self.line_index < len(self.parent.lines) - 1:
                    self.parent.lines[self.line_index + 1].pop(0)
            else:
                self.line.pop(self.char_index)
            self.config(line_index=self.line_index,  # We don't use text_index because, if self.char_index is 0,
                        char_index=self.char_index)  # we want to stay at 0, text_index might send the cursor at the
                                                     # end of the previous line if it is a cutted line

        elif key == pygame.K_ESCAPE:
            self.parent.defocus()

        elif pygame.K_F1 <= key <= pygame.K_F15:
            return

        # Write
        else:
            assert keyboard.last_event.key == key
            unicode = keyboard.last_event.unicode
            if key == pygame.K_RETURN:
                unicode = '\n'
            elif key == pygame.K_TAB:
                unicode = '    '
            self.write(unicode)

    def write(self, string):

        # Letters (lowercase and uppercase)
        text = self.parent.text[:self.char_index] + string + self.parent.text[self.char_index:]
        if self.parent.accept(text):

            if self.parent.is_selected:
                self.parent.del_selection_data()

            self.line.insert(self.char_index, string)
            self.config(text_index=self.text_index + len(string))
            # TODO : solve : when a TextEdit is resized, the cursor does not follow its text
