

import time
import pygame
from baopig.pybao.objectutilities import Object, History, debug
from baopig.communicative import Communicative
from .logging import LOGGER


class MouseEvent(Object):

    def __init__(self, signal, **kwargs):

        Object.__init__(self, signal=signal, type=getattr(mouse, signal), **kwargs)
        mouse.last_event = self

    def __str__(self):
        global __mouse_signals
        return "<MouseEvent({}-{} {})>".format(
            self.type,
            list(mouse._signals.keys())[list(mouse._signals.values()).index(self.type)],
            self.__dict__
        )
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
    DRAG = next(iterator)
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
        "DRAG": DRAG,
        "RELEASEDRAG": RELEASEDRAG,
    }

    def __init__(self):

        Communicative.__init__(self)

        for signal in self._signals:
            self.create_signal(signal)

        self._pos = (0, 0)
        self._rel = (0, 0)  # Le dernier deplacement de la souris

        # L'etat des bouttons de la souris (il y en a 5)
        # self.button[3] -> is the button 3 pressed ?
        # There is no button 0, so self.button[0] = None
        # For pygame, the 4 and 5 buttons are wheel up and down,
        # so these buttons are implemented as mouse.SCROLL

        self._pressed_button = None  # TODO : why not a tuple of pressed buttons ?

        # [None, 0, 0, 0]  # WARNING : A mouse can have additionnals buttons

        # Using an empty clic avoid testing if the mouse has clicks in memory or not
        empty_clic = Object(
            time=-1,  # heure du clic - en secondes
            button=None,  # numero du bouton
            pos=None)  # position du clic
        historic_size = 3  # Pour le triple-clic
        self.clic_history = History(object, maxlen=historic_size, seq=[empty_clic] * historic_size)

        """
        When the mouse is hovering a Text inside a Button inside a Zone inside a Scene,
        then the Text is hovered
        """
        self._hovered_comp = None

        """
        When the mouse click on a Text inside a Button inside a Zone inside a Scene,
        then the Text is linked
        """
        self._linked_comp = None

        """
        When a drag occurs, the youngest clicked container is selecting
        The selection is a rect from drag_origin to mouse.pos
        """
        self.drag_origin = None

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
        self._is_hovering_display = False
        self.last_event = None

    def __repr__(self):
        return "<Mouse(" + str(self.__dict__) + ")>"

    def __str__(self):
        return "<Mouse('pos': {}, 'pressed_button': {}, 'last_event': {})>" \
               "".format(self.pos, self.pressed_button, self.last_event)

    pos = property(lambda self: self._pos)
    x = property(lambda self: self._pos[0])  # TODO : allow moving mouse by doing mouse.move(dx, dy)
    y = property(lambda self: self._pos[1])  #         -> (for joystick control over mouse)

    application = property(lambda self: self._application)
    scene = property(lambda self: self._application._focused_scene)
    is_hovering_display = property(lambda self: self._is_hovering_display)
    linked_comp = property(lambda self: self._linked_comp)
    hovered_comp = property(lambda self: self._hovered_comp)
    pressed_button = property(lambda self: self._pressed_button)

    def _link(self, comp):

        assert self.is_hovering_display
        assert self.linked_comp is None

        if comp is not None:
            # assert comp.is_visible
            assert not comp.is_linked

            self._linked_comp = comp
            comp.is_linked = True
            self.linked_comp.signal.LINK.emit()

    def _get_pointed_comp(self):

        def get_pointed_comp(cont):

            if cont.collidemouse():
                for layer in reversed(tuple(cont.layers_manager.touchable_layers)):
                    assert layer.touchable
                    for comp in reversed(layer):
                        if comp.is_visible and comp.collidemouse():
                            if hasattr(comp, "children"):
                                return get_pointed_comp(comp)
                            return comp
                return cont

        return get_pointed_comp(self.scene)

    pointed_comp = property(_get_pointed_comp)

    def _hover_display(self):

        if self.is_hovering_display:
            return
        self._is_hovering_display = True
        self.update_hovered_comp()
        # print("HOVER APP")

    def _release_all(self):
        """
        Only called by Application.freeze()
        Release the pressed button
        """
        if self.pressed_button is not None:
            self.receive(Object(type=pygame.MOUSEBUTTONUP, button=self.pressed_button))

    def _unhover_display(self):

        if not self.is_hovering_display:
            return
        self._hover(None)
        self._is_hovering_display = False
        # print("UNHOVER APP")

    def _hover(self, comp):

        # if not self.is_hovering_display:
        #     assert self.hovered_comp is None
        #     return

        if comp is self.hovered_comp: return

        # UNHOVER
        old_hovered = self.hovered_comp
        if self.hovered_comp is not None:
            try:
                assert old_hovered.is_hovered
                old_hovered._is_hovered = False
            except:
                print("Hovering error")

        self._hovered_comp = comp

        # HOVER
        if comp is not None:
            assert comp.is_visible, repr(comp)
            assert not comp.is_hovered
            comp._is_hovered = True

        # SIGNALS
        if old_hovered is not None and hasattr(old_hovered.signal, "UNHOVER"):
            old_hovered.signal.UNHOVER.emit()
        if comp is not None and hasattr(comp.signal, "HOVER"):
            comp.signal.HOVER.emit()

    def _unlink(self):
        """
        This method unlink a Linkable component from the mouse

        It can exceptionnaly be called when a clicked component disappears
        Then the component calls itself this function, trougth Linkable.unlink()
        """

        try:
            assert self.linked_comp.is_linked or self.linked_comp.is_dead
        except AssertionError as e:
            raise e

        comp = self.linked_comp
        self._linked_comp = None

        if comp.is_alive:
            comp.is_linked = False
            comp.signal.UNLINK.emit()
        # While the mouse left button was press, we didn't update hovered_comp
        self.update_hovered_comp()

    def defocus_TBR(self, comp):
        """
        Permit to a component to defocus itself
        """
        assert self.scene.focused_comp == comp
        self.scene._focus(None)

    def get_pos_relative_to(self, comp):

        return comp.abs_rect.referencing(self.pos)

    def is_pressed(self, button):

        return button == self.pressed_button

    def receive(self, event):

        if event.type not in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION):
            LOGGER.warning("Unknown event : {}".format(event))
            return

        if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):

            if event.button not in (1, 2, 3, 4, 5):
                LOGGER.warning("Unknown button id : {} (event : {})".format(event.button, event))
                return

            if self.pressed_button is not None and self.pressed_button != event.button:
                # Another button is already pressed, we skip
                LOGGER.info("Another button is already pressed, we skip")
                return

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button in (4, 5):
                    # It's a wheel end of scrolling, wich is useless
                    return

                if not self.is_pressed(event.button):
                    # This button's DOWN event have been skiped, so we skip it's UP event
                    return

        elif event.type == pygame.MOUSEMOTION:

            if event.rel == (0, 0):
                # Don't care
                return

        # Real work

        if event.type == pygame.MOUSEBUTTONDOWN:

            # ACTUALIZING MOUSE STATE

            if event.button not in (4, 5):  # Ignore wheel
                self.clic_history.append(Object(time=time.time(), button=event.button, pos=event.pos))
                self._pressed_button = event.button

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

                def first_focusable_in_family_tree(widget):
                    # The recursivity always come to an end because a Scene is focusable
                    if hasattr(widget, "is_focused") and widget.is_enabled:
                        return widget
                    if widget.parent is widget:
                        return None
                    return first_focusable_in_family_tree(widget.parent)

                # Le focus passe avant le link parce que Linkable est une sous-class de Focusable
                focused = first_focusable_in_family_tree(self._get_pointed_comp())
                self.scene._focus(focused)
                if hasattr(focused, "is_linked"):
                    self._link(focused)
                else:
                    self._link(None)

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
                self.update_hovered_comp()
            elif event.button == 5:
                MouseEvent(
                    signal="SCROLL",
                    direction=-1,
                )
                self.update_hovered_comp()

        elif event.type == pygame.MOUSEBUTTONUP:

            # We don't consider an event of a pressed button when another button is already pressed
            # So this is the prevention
            assert self.is_pressed(event.button)

            # ACTUALIZING MOUSE STATE
            self._pressed_button = None

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

            if self.drag_origin is not None:
                MouseEvent(
                    signal="RELEASEDRAG",
                    pos=self.pos,
                    origin=self.drag_origin,
                    total_rel=(self.pos[0] - self.drag_origin[0], self.pos[1] - self.drag_origin[1]),
                    button=event.button,
                )
                self.drag_origin = None

            # UPDATING CLICKS, FOCUSES, HOVERS...

            if self.linked_comp:
                self._unlink()

        elif event.type == pygame.MOUSEMOTION:

            # ACTUALIZING MOUSE STATE
            self._pos = event.pos
            if self.drag_origin is None:
                # NOTE : Sometimes, pygame.MOUSEMOTION doesn't have attribute 'buttons'
                if self.pressed_button is not None:
                    self.drag_origin = (self.pos[0] - event.rel[0], self.pos[1] - event.rel[1])

            # MOUSE EVENTS TRANSMISSION
            if self.drag_origin is None:
                self.update_hovered_comp()
                MouseEvent(
                    signal="MOTION",
                    pos=self.pos,
                    rel=event.rel,
                )
            else:
                MouseEvent(
                    signal="DRAG",
                    pos=self.pos,
                    origin=self.drag_origin,
                    rel=event.rel,
                    total_rel=(self.pos[0] - self.drag_origin[0], self.pos[1] - self.drag_origin[1]),
                    button=self.pressed_button
                )
                # HANDLINGS
                if self.pressed_button == 1 and self.linked_comp:  # left button drag
                    self.linked_comp.signal.LINK_MOTION.emit(self.last_event)

        getattr(self.signal, self.last_event.signal).emit(self.last_event)

    def update_hovered_comp(self):

        if self.linked_comp is not None: return
        def first_hoverable_in_family_tree(widget):
            if widget.scene is widget:
                if hasattr(widget, "is_hovered"):
                    return widget
                return None
            if hasattr(widget, "is_hovered"):
                return widget
            else:
                return first_hoverable_in_family_tree(widget.parent)
        pointed = self._get_pointed_comp()
        if pointed is None:
            self._hover(None)
        else:
            self._hover(first_hoverable_in_family_tree(pointed))


mouse = _Mouse()
del _Mouse