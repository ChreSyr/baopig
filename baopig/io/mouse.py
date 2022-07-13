

import time
import pygame
from baopig.pybao.objectutilities import Object, History
from baopig.communicative import Communicative
from baopig.documentation import Focusable, HoverableByMouse, LinkableByMouse
from .logging import LOGGER


class MouseEvent(Object):

    def __init__(self, signal, **kwargs):

        Object.__init__(self, signal=signal, type=getattr(mouse, signal), **kwargs)
        mouse.last_event = self

    def __str__(self):
        return f"<MouseEvent({self.type}-" \
               f"{list(mouse._signals.keys())[list(mouse._signals.values()).index(self.type)]} {self.__dict__})>"
    __repr__ = __str__


iterator = (i for i in range(60, 100))
class _Mouse(Communicative):

    LEFTBUTTON_DOWN = next(iterator)
    WHEELBUTTON_DOWN = next(iterator)
    RIGHTBUTTON_DOWN = next(iterator)

    LEFTBUTTON_UP = next(iterator)
    WHEELBUTTON_UP = next(iterator)
    RIGHTBUTTON_UP = next(iterator)

    SCROLL = next(iterator)

    MOTION = next(iterator)
    RELEASEDRAG = next(iterator)

    _signals = {

        "LEFTBUTTON_DOWN": LEFTBUTTON_DOWN,
        "WHEELBUTTON_DOWN": WHEELBUTTON_DOWN,
        "RIGHTBUTTON_DOWN": RIGHTBUTTON_DOWN,

        "LEFTBUTTON_UP": LEFTBUTTON_UP,
        "WHEELBUTTON_UP": WHEELBUTTON_UP,
        "RIGHTBUTTON_UP": RIGHTBUTTON_UP,

        "SCROLL": SCROLL,

        "MOTION": MOTION,
        "RELEASEDRAG": RELEASEDRAG,
    }

    def __init__(self):

        Communicative.__init__(self)

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
        self.last_event = None

    def __repr__(self):
        return "<Mouse(" + str(self.__dict__) + ")>"

    def __str__(self):
        return f"<Mouse(pos={self.pos}, pressed_buttons={self._pressed_buttons}, last_event={self.last_event})>"

    pos = property(lambda self: self._pos)
    x = property(lambda self: self._pos[0])
    y = property(lambda self: self._pos[1])

    application = property(lambda self: self._application)
    scene = property(lambda self: self._application._focused_scene)
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
            # self.linked_widget.signal.LINK.emit()
            self.linked_widget.handle_link()

    def _get_touched_widget(self):
        """ Return the youngest touchable widget that is touched """

        def get_touched_widget(cont):

            for layer in reversed(tuple(cont.layers_manager.touchable_layers)):
                assert layer.touchable
                for child in reversed(layer):
                    if child.is_touchable_by_mouse and child.collidemouse():
                        if hasattr(child, "children"):  # TODO : isinstance
                            touched = get_touched_widget(child)
                            if touched is not None:
                                return touched
                        return child
            if cont.is_touchable_by_mouse:
                return cont

        return get_touched_widget(self.scene)

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

        self._hovered_widget = widget

        # HOVER
        if widget is not None:
            assert widget.is_visible, repr(widget)
            assert not widget.is_hovered
            widget._is_hovered = True

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
            # widget.signal.UNLINK.emit()
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
            LOGGER.warning("Unknown event : {}".format(event))
            return
        if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):

            if event.button not in (1, 2, 3, 4, 5):
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

            if event.button not in (4, 5):  # Ignore wheel
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

            if event.button == 1:
                # UPDATING CLICKS, FOCUSES, HOVERS...

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
                focused = first_focusable_in_family_tree(linked)
                # Le focus passe avant le link
                self.scene._focus(focused)
                self._link(linked)

            # MOUSE EVENTS TRANSMISSION

            if event.button == 1:
                MouseEvent(
                    signal="LEFTBUTTON_DOWN",
                    pos=self.pos,
                )
            elif event.button == 2:
                MouseEvent(
                    signal="WHEELBUTTON_DOWN",
                    pos=self.pos,
                )
            elif event.button == 3:
                MouseEvent(
                    signal="RIGHTBUTTON_DOWN",
                    pos=self.pos,
                )
            elif event.button == 4:
                MouseEvent(
                    signal="SCROLL",
                    direction=1,
                )
                self.update_hovered_widget()
            elif event.button == 5:
                MouseEvent(
                    signal="SCROLL",
                    direction=-1,
                )
                self.update_hovered_widget()

        elif event.type == pygame.MOUSEBUTTONUP:

            assert self.is_pressed(event.button)

            # ACTUALIZING MOUSE STATE
            self._pressed_buttons[event.button] = False

            # MOUSE EVENTS TRANSMISSION
            if event.button == 1:  # release left button

                MouseEvent(
                    signal="LEFTBUTTON_UP",
                    pos=self.pos
                )

            elif event.button == 2:  # release wheel button

                MouseEvent(
                    signal="WHEELBUTTON_UP",
                    pos=self.pos,
                )

            elif event.button == 3:  # release right button

                MouseEvent(
                    signal="RIGHTBUTTON_UP",
                    pos=self.pos,
                )

            # UPDATING CLICKS, FOCUSES, HOVERS...

            if self.linked_widget:
                self._unlink()

        elif event.type == pygame.MOUSEMOTION:

            # ACTUALIZING MOUSE STATE
            self._pos = event.pos

            # MOUSE EVENTS TRANSMISSION
            MouseEvent(
                signal="MOTION",
                pos=self.pos,
                rel=event.rel,
            )

            # LINK_MOTION or HOVER signals
            if self.is_pressed(button_id=1):
                if self.linked_widget:
                    # self.linked_widget.signal.LINK_MOTION.emit(self.last_event)
                    self.linked_widget.handle_link_motion(self.last_event)
            else:
                self.update_hovered_widget()

        getattr(self.signal, self.last_event.signal).emit(self.last_event)

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
