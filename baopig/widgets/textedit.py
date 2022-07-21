from baopig.pybao.objectutilities import Object, deque
from baopig.io import keyboard, mouse, LOGGER
from baopig.lib import *
from .scrollview import ScrollView
from .text import Text


# TODO : LineEntry (with select_all_on_focus and exec_on_defocus)
# TODO : presentation text when nothing is in the text ?


class SelectionRect_For_TextEdit(SelectionRect):

    def clip(self, rect):
        pass


class TextEdit(ScrollView, Selector):
    STYLE = ScrollView.STYLE.substyle()
    STYLE.modify(
        background_color="theme-color-font_opposite",
        height=45,
        padding=2,
        width=100,
    )

    def __init__(self, parent, text="", **kwargs):

        text_kwargs = {}
        for key in (
                "font_file",
                "font_height",
                "font_color",
                "font_bold",
                "font_italic",
                "font_underline",
                "max_width",
        ):
            if key in kwargs:
                text_kwargs[key] = kwargs.pop(key)

        Selector.__init__(self, parent, can_select=True, selectionrect_class=SelectionRect_For_TextEdit, **kwargs)
        ScrollView.__init__(self, parent)

        self._text_widget_ref = Text(self, text=text, selectable=True, **text_kwargs).get_weakref()
        # self.text_widget.signal.MOTION.disconnect(self.text_widget.handle_unselect)

        self.set_selectionrect_visibility(False)

        self._cursor_ref = Cursor(self).get_weakref()
        self.cursor.sleep()

        self.set_style_for(SelectionRect, ref=self.text_widget)

    cursor = property(lambda self: self._cursor_ref())
    text = property(lambda self: self._text_widget_ref().get_text())
    text_widget = property(lambda self: self._text_widget_ref())

    def accept(self, text):
        return text != ''

    def del_selection_data(self):

        if not self.text_widget.is_selected:
            return
        cursor_index = self.text_widget.find_index(
            char_index=self.text_widget.line_selections[0].index_start,
            line_index=self.text_widget.line_selections[0].line.line_index
        )
        assert self.is_selecting
        selected_lines = tuple(line for line in self.text_widget.lines if line.is_selected)
        if selected_lines:
            if self.cursor is not None:
                self.cursor.save()
            for line in selected_lines:
                line._text = line.text[:line.selection.index_start] + line.text[line.selection.index_end:]
                line._end = '' if line.selection._is_selecting_line_end else line.end
            line.config(line.text)
        self.close_selection()
        self.cursor.config(text_index=cursor_index)

    def end_selection(self, *args, **kwargs):

        super().end_selection(*args, **kwargs)

        pos = (self.selection_rect.abs_end[0] - self.text_widget.abs_rect.left,
               self.selection_rect.abs_end[1] - self.text_widget.abs_rect.top)
        line_index, char_index = self.text_widget._find_indexes(pos=pos)
        if line_index != self.cursor.line_index or char_index != self.cursor.char_index:
            self.cursor.config(line_index=line_index, char_index=char_index, selecting="done")

    def handle_defocus(self):

        super().handle_defocus()
        self.cursor.sleep()

    def handle_focus(self):

        super().handle_focus()

        text_index = self.text_widget._find_index(  # stupid looking bug fix
            pos=(self.x_scroller.val + self.rect.width, self.y_scroller.val + self.rect.height)
        )

        self.cursor.wake()
        self.cursor.config(text_index=text_index)

    def handle_keydown(self, key):

        if keyboard.mod.ctrl:
            if key in (pygame.K_a, pygame.K_c, pygame.K_v, pygame.K_x):
                return super().handle_keydown(key)
        self.cursor.handle_keydown(key)

    def handle_link(self):

        super().handle_link()

        if not mouse.has_double_clicked and not mouse.has_triple_clicked:  # else, the cursor follow the selection
            self.cursor.wake()
            self.cursor.config(text_index=self.text_widget._find_mouse_index())

    def paste(self, data):

        self.cursor.write(data)

    def select_all(self):

        if self.selectables:
            if self.is_selecting:
                self.close_selection()
            self.start_selection(self.main_widget.abs_rect.topleft)
            self.end_selection(self.main_widget.abs_rect.bottomright)

    def set_text(self, text):

        self.text_widget.set_text(text)


class Cursor(Rectangle, RepetivelyAnimated):
    """
    By default, at creation, a cursor is set at mouse position
    """
    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        color="theme-color-font"
    )

    def __init__(self, parent):

        assert isinstance(parent, TextEdit)

        h = parent.text_widget.font.height

        Rectangle.__init__(
            self,
            parent=parent,
            ref=parent.text_widget,
            size=(int(h / 10), h),
            name=parent.name + " -> cursor",
            layer=Layer(parent, Cursor, name="cursor_layer", level=LayersManager.FOREGROUND, maxlen=1),
            touchable=False
        )
        RepetivelyAnimated.__init__(self, parent, interval=.5)

        self._char_index = 0  # index of cursor position, see _Line._chars_pos for more explanations
        self.__line_index = 0  # index of cursor line, see Text._lines_pos for more explanations
        self._line = None
        self._text_index = 0  # index of cusor in Text.text

        # History
        """
        A History element is created when :
            - A new text insert
            - A part of text pop
            - Just before a selected data is delete

        A History element store these data :
            - the entire text of parent
            - the cusror indexes (line and char)
            - the selection start and end, if the parent was selecting
        """
        max_item_stored = 50
        self.history = deque(maxlen=max_item_stored)
        self.back_history = deque(maxlen=max_item_stored)

    char_index = property(lambda self: self._char_index)

    def _set_line_index(self, li):
        self.__line_index = li
        self._line = self.text_widget.lines[li]

    _line_index = property(lambda self: self.__line_index, _set_line_index)
    left_from_text = property(lambda self: self.rect.left - self.text_widget.rect.left)
    line_index = property(lambda self: self.__line_index)
    line = property(lambda self: self._line)
    text_widget = property(lambda self: self._parent.text_widget)
    text_index = property(lambda self: self._text_index)

    def clip(self):
        """ Scroll the Text until the cursor is inside the TextEdit"""

        x_scroller = self.parent.x_scroller
        if self.rect.right > self.parent.rect.width:
            dx = self.rect.right - self.parent.rect.width
            new_val = min(x_scroller.val + dx + 30, x_scroller.maxval)
            x_scroller.set_val(new_val)
        elif self.rect.left < 0:
            dx = self.rect.left
            new_val = max(x_scroller.val + dx - 30, x_scroller.minval)
            x_scroller.set_val(new_val)

        y_scroller = self.parent.y_scroller
        if self.rect.bottom > self.parent.rect.height:
            dy = self.rect.bottom - self.parent.rect.height
            new_val = min(y_scroller.val + dy, y_scroller.maxval)
            y_scroller.set_val(new_val)
        elif self.rect.top < 0:
            dy = self.rect.top
            new_val = max(y_scroller.val + dy, y_scroller.minval)
            y_scroller.set_val(new_val)

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
            line_index, char_index = self.text_widget.find_indexes(text_index=text_index)
        else:
            assert char_index is not None
            assert line_index is not None
            text_index = self.text_widget.find_index(line_index, char_index)

        # assert text_index == self.text_widget.find_index(line_index, char_index)

        if selecting:
            if self.parent.selection_rect is None:
                abs_pos = self.abs_rect.center
                self.parent.start_selection(abs_pos)

        def fit(v, mini, maxi):
            if v < mini:
                v = mini
            elif v > maxi:
                v = maxi
            return v

        self._text_index = fit(text_index, 0, len(self.text_widget.text))
        self._line_index = fit(line_index, 0, len(self.text_widget.lines) - 1)
        self._char_index = fit(char_index, 0, len(self.line.text))

        if self.char_index == len(self.line.text_with_end):
            LOGGER.warning("Tricky cursor position")

        if self.get_weakref()._ref is None:
            LOGGER.warning('This widget should be dead :', self)

        old_pos = self.rect.pos
        self.set_pos(top=self.line.rect.top + self.text_widget.rect.top)
        self.set_pos(left=self.line.find_pixel(self.char_index) + self.text_widget.rect.left)

        self.clip()

        self.start_animation()
        self.show()  # always shown when the animation starts

        if selecting == "done":
            pass
        elif selecting is True:
            if self.parent.selection_rect.abs_end is None or old_pos != self.rect.pos:
                self.parent.end_selection(self.abs_rect.topleft)
        elif selecting is False:
            if self.parent.is_selecting:
                self.parent.close_selection()
        else:
            raise PermissionError

        if save and (not self.history or self.text_widget.text != self.history[-1].text):
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
                    selected_data = self.line.text_with_end
                    self.line.insert(0, selected_data)
                else:
                    self.parent.close_selection()
                    self.line.insert(self.char_index, selected_data)
                self.config(text_index=self.text_index + len(selected_data))
            elif False and key == pygame.K_r:  # TODO
                # Execute
                try:
                    exec(self.text_widget.text)
                except Exception as e:
                    LOGGER.warning("CommandError: " + str(e))
            elif key == pygame.K_z:
                self.undo()
            elif key in (pygame.K_LEFT, pygame.K_HOME):
                self.config(self.text_widget.find_index(line_index=self.line_index, char_index=0),
                            selecting=keyboard.mod.maj)
            elif key in (pygame.K_RIGHT, pygame.K_END):
                self.config(self.text_widget.find_index(line_index=self.line_index, char_index=len(self.line.text)),
                            selecting=keyboard.mod.maj)
            elif key == pygame.K_UP:
                if self.line_index > 0:
                    self.config(line_index=0,
                                char_index=self.text_widget.lines[0].find_index(self.left_from_text),
                                selecting=keyboard.mod.maj)
            elif key == pygame.K_DOWN:
                if self.line_index < len(self.text_widget.lines) - 1:
                    self.config(
                        line_index=len(self.text_widget.lines) - 1,
                        char_index=self.text_widget.lines[len(self.text_widget.lines) - 1].find_index(
                            self.left_from_text),
                        selecting=keyboard.mod.maj
                    )

        # Cursor movement
        elif 1073741898 <= key <= 1073741906 and key != 1073741900:

            if key in (pygame.K_LEFT, pygame.K_RIGHT):

                if keyboard.mod.alt:  # go to word side
                    if key == pygame.K_LEFT:
                        if self.char_index == 0:
                            return
                        self.config(text_index=self.text_index - 1, selecting=keyboard.mod.maj)
                        while self.char_index > 0 and \
                                (self.line.text[self.char_index - 1] != ' ' or self.line.text[self.char_index] == ' '):
                            self.config(text_index=self.text_index - 1, selecting=keyboard.mod.maj)
                    elif key == pygame.K_RIGHT:
                        if self.char_index == len(self.line.text):
                            return
                        self.config(text_index=self.text_index + 1, selecting=keyboard.mod.maj)
                        while self.char_index < len(self.line.text) and \
                                (self.line.text[self.char_index - 1] != ' ' or self.line.text[self.char_index] == ' '):
                            self.config(text_index=self.text_index + 1, selecting=keyboard.mod.maj)
                elif (not keyboard.mod.maj) and len(self.text_widget.line_selections):
                    if key == pygame.K_LEFT:
                        self.config(line_index=self.text_widget.line_selections[0].line_index,
                                    char_index=self.text_widget.line_selections[0].index_start)
                    elif key == pygame.K_RIGHT:
                        self.config(line_index=self.text_widget.line_selections[-1].line_index,
                                    char_index=self.text_widget.line_selections[-1].index_end)
                elif key == pygame.K_LEFT:
                    # self.config(char_index=self.char_index-1, selecting=keyboard.mod.maj)
                    self.config(text_index=self.text_index - 1, selecting=keyboard.mod.maj)
                elif key == pygame.K_RIGHT:
                    # self.config(char_index=self.char_index+1, selecting=keyboard.mod.maj)
                    self.config(text_index=self.text_index + 1, selecting=keyboard.mod.maj)

            elif key in (pygame.K_HOME, pygame.K_END):
                if key == pygame.K_HOME:  # Fn + K_LEFT
                    self.config(text_index=self.text_widget.find_index(line_index=self.line_index, char_index=0),
                                selecting=keyboard.mod.maj)
                elif key == pygame.K_END:  # Fn + K_RIGHT
                    self.config(self.text_widget.find_index(line_index=self.line_index, char_index=len(self.line.text)),
                                selecting=keyboard.mod.maj)

            elif key in (pygame.K_UP, pygame.K_DOWN):
                if key == pygame.K_UP:
                    if self.line_index > 0:
                        self.config(line_index=self.line_index - 1,
                                    char_index=self.text_widget.lines[self.line_index - 1].find_index(
                                        self.left_from_text),
                                    selecting=keyboard.mod.maj)
                if key == pygame.K_DOWN:
                    if self.line_index < len(self.text_widget.lines) - 1:
                        self.config(line_index=self.line_index + 1,
                                    char_index=self.text_widget.lines[self.line_index + 1].find_index(
                                        self.left_from_text),
                                    selecting=keyboard.mod.maj)

            elif key in (pygame.K_PAGEUP, pygame.K_PAGEDOWN):
                if key == pygame.K_PAGEUP:
                    if self.line_index > 0:
                        self.config(line_index=0,
                                    char_index=self.text_widget.lines[0].find_index(self.left_from_text),
                                    selecting=keyboard.mod.maj)
                if key == pygame.K_PAGEDOWN:
                    if self.line_index < len(self.text_widget.lines) - 1:
                        self.config(
                            line_index=len(self.text_widget.lines) - 1,
                            char_index=self.text_widget.lines[len(self.text_widget.lines) - 1].find_index(
                                self.left_from_text),
                            selecting=keyboard.mod.maj)

        # Suppression
        elif key == pygame.K_BACKSPACE:
            if self.text_widget.is_selected:
                self.parent.del_selection_data()
            elif self.line_index > 0 or self.char_index > 0:
                if self.char_index > 0:
                    self.line.pop(self.char_index-1)
                else:
                    self.text_widget.lines[self.line_index - 1].pop(-1)
                old = self.text_index
                self.config(text_index=self.text_index - 1)
                assert self.text_index == old - 1

        elif key == pygame.K_DELETE:
            if self.parent.is_selected:
                self.text_widget.del_selection_data()
            if self.line.end == '' and self.char_index == len(self.line.text):
                if self.line_index < len(self.text_widget.lines) - 1:
                    self.text_widget.lines[self.line_index + 1].pop(0)
            else:
                self.line.pop(self.char_index)

            # We don't use text_index because, if self.char_index is 0,
            # we want to stay at 0, text_index might send the cursor at the
            # end of the previous line if it is a cutted line
            self.config(line_index=self.line_index,
                        char_index=self.char_index)

        elif key == pygame.K_ESCAPE:
            self.parent.defocus()

        # Write
        else:
            unicode = keyboard.last_event.unicode
            if key == pygame.K_RETURN:
                unicode = '\n'
            elif key == pygame.K_TAB:
                unicode = '    '
            if unicode:  # skip every maj, majlock, met, cmd, ctrl...
                self.write(unicode)

    def write(self, string):

        if self.text_widget.is_selected:
            self.parent.del_selection_data()

        # Letters (lowercase and uppercase)
        text = self.text_widget.text[:self.char_index] + string + self.text_widget.text[self.char_index:]
        if self.parent.accept(text):
            self.line.insert(self.char_index, string)
            self.config(text_index=self.text_index + len(string))
            # TODO : solve : when a TextEdit is resized, the cursor does not follow its text

    # History
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
            text=self.text_widget.text,
            cursor_line_index=self.line_index,
            cursor_char_index=self.char_index,
            selection_start=self.parent.selection_rect.abs_start if self.parent.selection_rect else None,
            selection_end=self.parent.selection_rect.abs_end if self.parent.selection_rect else None
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
