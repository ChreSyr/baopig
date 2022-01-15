

import pygame
from string import printable as string_printable
from baopig.pybao.issomething import *
from baopig.pybao.objectutilities import TypedDeque, PrefilledFunction
from baopig.ressources import *
from baopig.io import LOGGER, mouse
from baopig._lib import Closable, Focusable, Container, Selector, Rectangle
from .text import Text
from .label import DynamicLabel


class InputBox(DynamicLabel, Selector):
    """
    Une InputBox est un Container.
    Elle contient un DynamicLabel dont le texte est saisi au clavier par l'utilisateur
    Les entrees peuventent etre filtrees grace au parametre char_filter : seuls les
    caracteres contenus dans char_filter sont acceptes comme entrees
    Afin d'ecouter les entrees du clavier, la InputBox a besoin d'avoir le focus
    """

    class HistoricElement:
        # TODO : make lighter ? via a single string concatening both values ? via a tuple inheritance ?
        def __init__(self, text, cursor_index):

            assert isinstance(text, str)
            assert isinstance(cursor_index, int)

            self.text = text
            self.cursor_index = cursor_index

    def __init__(self,
                 parent,
                 size=None,
                 pos=None,
                 command=None,
                 exec_command_on_defocus=False,
                 presentation_text=None,
                 font_size=None,
                 font_color=None,
                 background_color=None,
                 default_text=None,
                 entry_type=None,
                 char_filter=None,
                 maxlen=None,
                 name=None):

        if size is None:
            h = ressources.font.height
            size = (h * 5, h + int(h / 6) * 2)
        if command is None: command = lambda: None
        if presentation_text is None: presentation_text = "Enter your text here"
        if font_color is None: font_color = TEXTBOXES_FONT_COLOR
        if background_color is None: background_color = TEXTBOXES_BG_COLOR
        if default_text is None: default_text = "Unset"  # If we don't precise something, it will be "Unset"
        if entry_type is None: entry_type = str

        # TODO : Faire un background uni et ajouter deux Rectangles pour le contour (un pour la ligne noire, l'autre pour marquer le margin)
        background = pygame.Surface(size, pygame.SRCALPHA)
        background.fill(background_color)
        pygame.draw.rect(background, TEXTBOXES_OUTLINE_COLOR, (0, 0) + size, 3)  # Contour

        assert isinstance(default_text, str)
        assert entry_type in (str, float, int), \
                    "Entries of InputBox can only be of type str, float or int"
        if char_filter is not None:
            # char_filter peut etre un string ou une liste de caracteres
            assert hasattr(char_filter, "__iter__"), "char_filter must be an iterable"
            for elt in char_filter:
                assert isinstance(elt, str), "char_filter must only contains characters"
                assert len(elt) == 1, "char_filter must only contains characters"

        # Inheritance
        DynamicLabel.__init__(
            self,
            parent=parent,
            pos=pos,
            text=default_text,
            size=size,
            margin=int(size[1] / 6),
            font_size=font_size,
            font_color=font_color,
            background_color=background_color,
            # TODO : un mode qui permet d'avoir une hitbox fixe et un font_size fixe tout en permettant les changements sur text
            modification_mode=FIXED_HITBOX,
            text_location="midleft",
            name=name
        )
        Selector.__init__(self)
        # INFO : InputBox is has stopped running because of static text

        def handle_click():
            # self.selection.start(self.text_component.find_mouse_index())
            # if self.cursor.is_sleeping:
            #     self.cursor.wake()
            # self.cursor.set_index(self.selection.index_end)
            print("CLICK")
        # self.handle_click.add(handle_click)
        # self.handle_drag.add(lambda: self.cursor.set_index(self.selection.index_end))

        def handle_focus():
            if self.cursor.is_sleeping:
                index = self.text_component.find_mouse_index() if mouse.button[1] else len(self.text)
                self.cursor.set_index(index)
            # else, the cursor have been woke up by a click
            print("FOCUS")
        def handle_defocus():
            self.cursor.asleep()
        def handle_enter():
            # TODO : use handle.add(...)
            assert self.is_focused

            if not self.text:
                if self.default_text:
                    self.set_text(self.default_text, cursor_index=len(self.default_text))

            mouse.defocus(self)  # -> generate a handle_defocus -> del cursor
                                 #                              -> command() (optionnal)

            if not exec_command_on_defocus:
                try:
                    command(self.entry_type(self.text))  # TODO : InputNumber and InputText
                except ValueError:
                    LOGGER.warning("Wrong value : {}, expected object of {} type".format(self.text, self.entry_type))
                except TypeError:  # missing 1 required positional argument: 'value' ?
                    command()
                except Exception as e:
                    raise e

        self.handle_focus.add(handle_focus)
        self.handle_defocus.add(handle_defocus)
        # self.handle_defocus.add(self.selection.close)
        self.handle_enter.add(handle_enter)
        # self.handle_enter.add(handle_enter)
        if exec_command_on_defocus:
            self.handle_defocus.add(command)

        # Historic
        max_item_stored = 5
        self.historic = TypedDeque(InputBox.HistoricElement, maxlen=max_item_stored)
        self.back_historic = TypedDeque(InputBox.HistoricElement, maxlen=max_item_stored)

        # Le contenu du label
        self._presentation_text_ref = Text(
            parent=self,
            text=presentation_text,
            pos=self.text_component.topleft,
            font_height=self.text_component.font.height,
            font_color=([255 - int((255 - font_color[i]) * .75)
                         for i in range(3)]),  # Le texte de presentation est plus clair
            name=self.name + " -> presentation_text",
        ).get_weakref()
        self.presentation_text.set_nontouchable()
        if default_text:
            self.presentation_text.hide()

        self.default_text = default_text
        self.char_filter = char_filter
        self.entry_type = entry_type
        self.maxlen = maxlen
        self.pos_label = 0  # Le decalage vers la gauche du label, lorsque le texte est trop long

        # Save the initial state
        self.save()

        margin_rect = Rectangle(
            parent=self,
            pos=(0, 0),
            size=self.size,
            border_width=self.margin,
            color=self.background.color,
            name=self.name + " -> margin"
        )
        margin_rect.set_nontouchable()
        outline_rect = Rectangle(
            parent=self,
            pos=(0, 0),
            size=self.size,
            border_width=2,
            color=TEXTBOXES_OUTLINE_COLOR,
            name=self.name + " -> outline"
        )
        outline_rect.set_nontouchable()

        """
        Tentatives de recuperer le presse papier

        pygame.scrap.init()
        if pygame.scrap.lost ():
            print("No content from me anymore. The clipboard is used by someone else.")
        pygame.scrap.put("own_data", "Bonjour")
        print(pygame.scrap.get("own_data"))
        types = pygame.scrap.get_types()
        #for type in types:
            #print(type, pygame.scrap.get(type))
        """

    have_selection = property(lambda self: self.selection.is_visible)
    presentation_text = property(lambda self: self._presentation_text_ref())

    def accept(self, new_char):
        """
        Test if a given character can be added to the text
        """

        if not new_char in string_printable: return False
        try:
            self.entry_type(new_char)
        except ValueError as e:
            if self.entry_type == float and new_char == '.':
                # Prevent apparition of two points in a float
                return new_char not in self.text
            else:
                return False
        return self.char_filter is None or new_char in self.char_filter

    def del_selected_text(self):
        """
        Supprime les caracteres seletionnes
        """

        if self.have_selection:
            # We use sorted because the self.index_end can be lower than self.index_start
            index_start, index_end = self.selection.sorted
            self.set_text(self.text[:index_start] + self.text[index_end:], cursor_index=index_start)
            self.selection.close()

    def handle_KEYDOWN(self, event):

        print("handle_KEYDOWN", event.key, self.is_focused)
        if self.is_focused:
            self.write(event)

    def redo(self):
        """
        Restaure la derniere modification
        """
        if len(self.back_historic):

            backup = self.back_historic.pop()  # last element of self.back_historic, the current state
            self.historic.append(backup)

            self.set_text(backup.text, cursor_index=backup.cursor_index, save=False)
        else:
            LOGGER.debug("Cannot redo last operation because the operations historic is empty")

    def save(self):

        self.historic.append(InputBox.HistoricElement(self.text, self.cursor.index))
        self.back_historic.clear()

    def set_text(self, text, cursor_index=None, save=True):

        if self.maxlen is not None and len(text) > self.maxlen:
            return

        super().set_text(text)
        if cursor_index is not None: self.cursor.set_index(cursor_index)
        if save: self.save()

        if not text and not self.presentation_text.is_visible:
            self.presentation_text.show()
        if text and self.presentation_text.is_visible:
            self.presentation_text.hide()

    def undo(self):
        """
        Annule la derniere modification
        """
        if len(self.historic) > 1:

            backup = self.historic.pop()  # last element of self.historic, which is the state before undo()
            self.back_historic.append(backup)

            last_state = self.historic[-1]
            self.set_text(last_state.text, cursor_index=last_state.cursor_index, save=False)
        else:
            LOGGER.debug("Cannot undo last operation because the operations historic is empty")

    def write(self, event):
        """
        N'accepte que les evenements du clavier
        Si la touche est speciale, effectue sa propre fonction
        Modifie le placement du curseur

        exemple d'event accepte:
            <Event(2-KeyDown {'unicode': '3', 'key': 34, 'mod': 1, 'scancode': 20, 'window': None})>
        """

        assert isinstance(event, pygame.event.EventType)
        assert hasattr(event, "key"), "write() need a keyboard entry"

        # Maj + ...
        if event.mod in (1, 2):
            if event.key == pygame.K_LEFT:
                # On avance la selection vers la gauche
                if not self.have_selection:
                    self.selection.start(self.cursor.index)
                self.cursor.set_index(self.cursor.index - 1)
                self.selection.index_end = self.cursor.index
            elif event.key == pygame.K_RIGHT:
                # On avance la selection vers la droite
                if not self.have_selection:
                    self.selection.start(self.cursor.index)
                self.cursor.set_index(self.cursor.index + 1)
                self.selection.index_end = self.cursor.index

        # Cmd + ...
        elif event.mod in (1024, 2048):
            if event.key == pygame.K_a:  # Select all
                self.selection.start(0)
                self.selection.index_end = len(self.text)
                self.cursor.set_index(self.selection.index_end)
            elif event.key == pygame.K_z:
                self.undo()
        # TODO : Cmd + Fleche works same as Fn + Fleche
        # TODO : Alt + Fleche go to word side

        # Maj + Cmd + ...
        elif event.mod in (1025, 1026, 2049, 2050):
            if event.key == pygame.K_z:
                self.redo()

        # Fleches
        elif event.key in (pygame.K_LEFT, pygame.K_HOME, pygame.K_RIGHT, pygame.K_END):
            if self.have_selection:
                if event.key in (pygame.K_LEFT, pygame.K_HOME):
                    self.cursor.set_index(self.selection.lowest)
                elif event.key in (pygame.K_RIGHT, pygame.K_END):
                    self.cursor.set_index(self.selection.highest)
                self.selection.close()
            elif event.key == pygame.K_LEFT:
                self.cursor.set_index(self.cursor.index - 1)
            elif event.key == pygame.K_HOME:  # Fn + K_LEFT
                self.cursor.set_index(0)
            elif event.key == pygame.K_RIGHT:
                self.cursor.set_index(self.cursor.index + 1)
            elif event.key == pygame.K_END:  # Fn + K_RIGHT
                self.cursor.set_index(len(self.text))

        # Suppression
        elif event.key == pygame.K_BACKSPACE:
            if self.have_selection:
                self.del_selected_text()
            elif self.cursor.index > 0:
                self.set_text(self.text[:self.cursor.index - 1] + self.text[self.cursor.index:],
                              cursor_index=self.cursor.index - 1)

        # Validation
        elif event.key in (pygame.K_RETURN, pygame.K_TAB):
            # because RETURN and TAB are in string.printable, we need to prevent writing them
            return

        # Lettres (minuscules et majuscules)
        if event.unicode and self.accept(event.unicode):
            if self.have_selection: self.del_selected_text()
            self.set_text(self.text[:self.cursor.index] + event.unicode + self.text[self.cursor.index:],
                          cursor_index=self.cursor.index + 1)
            # print(event)
