

import time
import pygame
from baopig.pybao.objectutilities import Object, History
from baopig.communicative import Communicative
from baopig.documentation import Container, Focusable, HoverableByMouse, LinkableByMouse, ScrollableByMouse
from .logging import LOGGER


class _Mouse(Communicative):

    _signals = "MOUSEMOTION", "MOUSEBUTTONDOWN", "MOUSEBUTTONUP", "MOUSEWHEEL"

    def __init__(self):

        Communicative.__init__(self)

        # 4 signals :
        #     - MOUSEMOTION
        #     - MOUSEBUTTONDOWN
        #     - MOUSEBUTTONUP
        #     - MOUSEWHEEL
        for signal in self._signals:
            self.create_signal(signal)

        self._pos = (-1, -1)  # No collision at application launch
        self._rel = (0, 0)  # Le dernier deplacement de la souris

        # L'etat des bouttons de la souris (il y en a 5)
        # self.button[3] -> is the button 3 pressed ?
        # There is no button 0, so self.button[0] = None
        # For pygame, the 4 and 5 buttons are wheel up and down,
        # so these buttons are implemented as mouse.SCROLL

        self._pressed_buttons = {}

        # [None, 0, 0, 0]  # WARNING : A mouse can have additionnals buttons

        # Using an empty clic avoid testing if the mouse has clicks in memory or not
        empty_clic = Object(
            time=-1,  # heure du clic - en secondes
            button=None,  # numero du bouton
            pos=None)  # position du clic
        historic_size = 3  # Pour le triple-clic
        self.clic_history = History(maxlen=historic_size, seq=[empty_clic] * historic_size)

        """
        When the mouse is hovering a Text inside a Button inside a Zone inside a Scene,
        then the Text is hovered
        """
        self._hovered_widget = None

        """
        When the mouse click on a Text inside a Button inside a Zone inside a Scene,
        then the Text is linked
        """
        self._linked_widget = None

        """
        Permet de savoir si l'utilisateur vient de faire un double-click

        Pour faire un double-clic, il faut :
            - qu'il y ait eu 2 clics en moins de 5 dixiemes de secondes
            - que les 2 clics aient ete fait par le bouton gauche
            - que la souris n'ait pas bougee entre les clics

        has_double_clicked garde la valeur True jusqu'au clic suivant
        """
        self.has_double_clicked = False

        """
        Permet de savoir si l'utilisateur vient de faire un triple-clic

        Pour faire un triple-clic, il faut :
            - qu'il y ait eu 3 clics en moins de 10 dixiemes de secondes
            - que les 3 clics aient ete fait par le bouton gauche
            - que la souris n'ait pas bougee entre les clics

        has_triple_clicked garde la valeur True jusqu'au clic suivant
        """
        self.has_triple_clicked = False

        self._application = None
        self._display = None
        self._is_hovering_display = True

    def __repr__(self):
        return "<Mouse(" + str(self.__dict__) + ")>"

    def __str__(self):
        return f"<Mouse(pos={self.pos}, pressed_buttons={self._pressed_buttons})>"

    pos = property(lambda self: self._pos)
    x = property(lambda self: self._pos[0])
    y = property(lambda self: self._pos[1])

    is_hovering_display = property(lambda self: self._is_hovering_display)
    linked_widget = property(lambda self: self._linked_widget)
    hovered_widget = property(lambda self: self._hovered_widget)

    def _link(self, widget):

        assert self.is_hovering_display
        assert self.linked_widget is None

        if widget is not None:
            assert not widget.is_linked

            self._linked_widget = widget
            widget.is_linked = True

            widget.signal.HIDE.connect(self._unlink, owner=None)
            widget.signal.SLEEP.connect(self._unlink, owner=None)
            widget.signal.KILL.connect(self._unlink, owner=None)

            self.linked_widget.handle_link()

    def _get_touched_widget(self):
        """ Return the youngest touchable widget that is touched """

        def get_touched_widget(cont):

            for layer in reversed(tuple(cont.layers_manager.touchable_layers)):
                assert layer.touchable
                for child in reversed(layer):
                    if child.is_touchable_by_mouse and child.collidemouse():
                        if isinstance(child, Container):
                            touched = get_touched_widget(child)
                            if touched is not None:
                                return touched
                        return child
            if cont.is_touchable_by_mouse:
                return cont

        return get_touched_widget(self._application.focused_scene)

    def _hover_display(self):

        if self.is_hovering_display:
            return
        self._is_hovering_display = True
        self.update_hovered_widget()

    def _unhover_display(self):

        if not self.is_hovering_display:
            return
        self._hover(None)
        self._is_hovering_display = False

    def _hover(self, widget):

        if widget is self._hovered_widget:
            return

        # UNHOVER
        old_hovered = self._hovered_widget
        if self._hovered_widget is not None:
            assert old_hovered.is_hovered
            old_hovered._is_hovered = False

            old_hovered.signal.HIDE.disconnect(self.update_hovered_widget)
            old_hovered.signal.SLEEP.disconnect(self.update_hovered_widget)
            old_hovered.signal.KILL.disconnect(self.update_hovered_widget)

        self._hovered_widget = widget

        # HOVER
        if widget is not None:
            assert widget.is_visible, repr(widget)

            assert not widget.is_hovered
            widget._is_hovered = True

            widget.signal.HIDE.connect(self.update_hovered_widget, owner=None)
            widget.signal.SLEEP.connect(self.update_hovered_widget, owner=None)
            widget.signal.KILL.connect(self.update_hovered_widget, owner=None)

        # SIGNALS
        if old_hovered is not None:
            old_hovered.signal.UNHOVER.emit()

        if widget is not None:
            widget.signal.HOVER.emit()

    def _unlink(self):
        """
        This method unlinks a LinkableByMouse widget from the mouse

        It can exceptionnaly be called when a clicked widget disappears
        Then the widget calls itself this function, trougth LinkableByMouse.unlink()
        """

        try:
            assert self.linked_widget.is_linked or self.linked_widget.is_dead
        except AssertionError as e:
            raise e

        widget = self.linked_widget
        self._linked_widget = None

        if widget.is_alive:
            widget.is_linked = False

            widget.signal.HIDE.disconnect(self._unlink)
            widget.signal.SLEEP.disconnect(self._unlink)
            widget.signal.KILL.disconnect(self._unlink)

            widget.handle_unlink()
        # While the mouse left button was press, we didn't update hovered_widget
        self.update_hovered_widget()

    def get_pos_relative_to(self, widget):

        return widget.abs_rect.referencing(self.pos)

    def is_pressed(self, button_id):
        """Return True if the button with identifier 'button_id' (an integer) is pressed"""

        try:
            return bool(self._pressed_buttons[button_id])
        except KeyError:
            # Here, the button has never been pressed
            return 0

    def receive(self, event):

        # Unknown & skipable events
        if event.type not in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
            LOGGER.warning(f"Unknown event : {event}")
            return
        if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):

            if event.button not in (1, 2, 3, 4, 5):
                if event.button not in (6, 7, 8, 9, 10):  # TODO : what are these events ?
                    LOGGER.warning(f"Unknown button id : {event.button} (event : {event})")
                return

            # if self._pressed_buttons[event.button] is False:
            # if self.pressed_button is not None and self.pressed_button != event.button:
            #     # Another button is already pressed, we skip
            #     LOGGER.info("Another button is already pressed, we skip")
            #     return

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button in (4, 5):
                    # It's a wheel end of scrolling, wich is useless
                    return

                # if not self.is_pressed(event.button):
                #     # This button's DOWN event have been skiped, so we skip it's UP event
                #     return
        elif event.type == pygame.MOUSEMOTION:

            if event.rel == (0, 0):
                # Don't care
                return

        # Real work

        if event.type == pygame.MOUSEBUTTONDOWN:

            # ACTUALIZING MOUSE STATE

            if event.button in (4, 5):

                def first_scrollable_in_family_tree(widget):
                    if widget.parent == widget:
                        return None
                    if isinstance(widget, ScrollableByMouse) and widget.is_touchable_by_mouse:
                        return widget
                    return first_scrollable_in_family_tree(widget.parent)

                pointed = self._get_touched_widget()
                scrolled = first_scrollable_in_family_tree(pointed)
                if scrolled:
                    scrolled.handle_mouse_scroll(event)

            else:  # Ignore wheel
                self.clic_history.append(Object(time=time.time(), button=event.button, pos=event.pos))
                self._pressed_buttons[event.button] = True

                self.has_double_clicked = \
                    self.clic_history[-2].time > self.clic_history[-1].time - .5 and \
                    self.clic_history[-2].button == self.clic_history[-1].button == 1 and \
                    self.clic_history[-2].pos == self.clic_history[-1].pos

                self.has_triple_clicked = \
                    self.has_double_clicked and \
                    self.clic_history[-3].time > self.clic_history[-1].time - 1 and \
                    self.clic_history[-3].button == self.clic_history[-1].button == 1 and \
                    self.clic_history[-3].pos == self.clic_history[-1].pos

                # UPDATING CLICKS, FOCUSES, HOVERS...

                if event.button in (1, 2, 3):

                    def first_linkable_in_family_tree(widget):
                        # The recursivity always ends because a Scene is a LinkableByMouse
                        if isinstance(widget, LinkableByMouse) and widget.is_touchable_by_mouse:
                            return widget
                        return first_linkable_in_family_tree(widget.parent)

                    def first_focusable_in_family_tree(widget):
                        # The recursivity always ends because a Scene is a Focusable
                        if isinstance(widget, Focusable) and widget.is_touchable_by_mouse:
                            return widget
                        return first_focusable_in_family_tree(widget.parent)

                    pointed = self._get_touched_widget()
                    linked = first_linkable_in_family_tree(pointed)

                    linked.handle_mousebuttondown(event)

                    if event.button == 1:
                        focused = first_focusable_in_family_tree(linked)
                        # Le focus passe avant le link
                        self._application.focused_scene.focus(focused)
                        self._link(linked)

        elif event.type == pygame.MOUSEBUTTONUP:

            assert self.is_pressed(event.button)

            # ACTUALIZING MOUSE STATE
            self._pressed_buttons[event.button] = False

            # Linkable stuff
            if self.linked_widget:
                self._unlink()

        elif event.type == pygame.MOUSEMOTION:

            # ACTUALIZING MOUSE STATE
            self._pos = event.pos

            # Linkable and Hoverable stuff
            if self.is_pressed(button_id=1) and self.linked_widget:
                self.linked_widget.handle_link_motion(event.rel)
            else:
                self.update_hovered_widget()

        # EVENT TRANSMISSION
        for signal_id in self._signals:
            if event.type == getattr(pygame, signal_id):
                getattr(self.signal, signal_id).emit(event)
                break

    def update_hovered_widget(self):

        if self.linked_widget is not None:
            return

        def first_hoverable_in_family_tree(widget):
            if widget.scene is widget:
                if isinstance(widget, HoverableByMouse):
                    return widget
                return None
            if isinstance(widget, HoverableByMouse):
                return widget
            else:
                return first_hoverable_in_family_tree(widget.parent)

        pointed = self._get_touched_widget()
        if pointed is None:
            self._hover(None)
        else:
            self._hover(first_hoverable_in_family_tree(pointed))


mouse = _Mouse()
del _Mouse
