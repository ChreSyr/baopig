

import functools
import pygame
from baopig.communicative import ApplicationExit
from baopig.io import LOGGER, mouse, keyboard


import threading
paint_lock = threading.RLock()

# TODO : deproteger les attributs handle_something


class Size(tuple):

    def __init__(self, size):
        assert len(self) == 2, f"Wrong length : {self} (a size only have 2 elements)"
        for coord in self:
            assert isinstance(coord, (int, float)), f"Wrong value in size : {coord} (must be a number)"
            assert coord >= 0, f"Wrong value in size : {coord} (must be positive)"


class Color(pygame.Color):
    """
    Very close to pygame.Color :

    Color(tuple) -> Color
    Color(name) -> Color
    Color(r, g, b, a) -> Color
    Color(rgbvalue) -> Color
    pygame object for color representations
    """

    def __init__(self, *args, transparency=None, **kwargs):

        if transparency is None:
            try:
                pygame.Color.__init__(self, *args, **kwargs)
            except ValueError:
                pygame.Color.__init__(self, *args[0])

        else:
            try:
                color = pygame.Color(*args, **kwargs)
            except ValueError:
                color = pygame.Color(*args[0])
            pygame.Color.__init__(self, color.r, color.g, color.b, transparency)

    def set_hsv(self, val):
        if val[1] > 100:
            val = val[0], 100, val[2]
        try:
            self.hsva = val + (100,)
        except ValueError as e:
            raise ValueError(str(e) + f" : {val}")
    hsv = property(lambda self: self.hsva[:-1], set_hsv)

    def set_hsl(self, val):
        if val[1] > 100:
            val = val[0], 100, val[2]
        try:
            self.hsla = val + (100,)
        except ValueError as e:
            raise ValueError(str(e) + f" : {val}")
    hsl = property(lambda self: self.hsla[:-1], set_hsl)

    def set_hue(self, h):
        self.hsv = (h,) + self.hsv[1:]
    h = property(lambda self: self.hsva[0], set_hue)

    def get_saturation(self):
        s = self.hsva[1]
        if s > 100:  # sometime 100.00000000000001
            s = 100
        return s
    def set_saturation(self, s):
        self.hsv = self.h, s, self.v
    s = property(get_saturation, set_saturation)

    def set_value(self, v):
        self.hsv = self.hsva[:2] + (v,)
    v = property(lambda self: self.hsva[2], set_value)

    def set_lightness(self, l):
        self.hsl = self.hsla[:2] + (l,)
    l = property(lambda self: self.hsla[2], set_lightness)

    def copy(self):
        return self.__class__(self)

    def has_transparency(self):

        return self.a < 255


class MarginType:
    # Once it is created, it can never change

    def __init__(self, margin):

        if margin is None:
            margin = 0, 0, 0, 0
        elif isinstance(margin, int):
            margin = tuple([margin] * 4)
        elif isinstance(margin, MarginType):
            margin = margin.left, margin.top, margin.right, margin.bottom
        else:
            l = len(margin)
            if l == 2:
                margin = tuple(margin) + tuple(margin)
            elif l == 3:
                margin = tuple(margin) + tuple([margin[1]])
            else:
                assert l == 4, f"Wrong value for margin type : {margin}"

        self._left = margin[0]
        self._top = margin[1]
        self._right = margin[2]
        self._bottom = margin[3]

    def __repr__(self):
        return f"MarginType(left={self.left}, top={self.top}, right={self.right}, bottom={self.bottom})"

    bottom = property(lambda self: self._bottom)
    is_null = property(lambda self: self.left == self.top == self.right == self.bottom == 0)
    left = property(lambda self: self._left)
    right = property(lambda self: self._right)
    top = property(lambda self: self._top)


class Enablable:

    def __init__(self):

        self._is_enabled = True
        self.create_signal("ENABLE")
        self.create_signal("DISABLE")

    is_enabled = property(lambda self: self._is_enabled)

    def disable(self):
        if self.is_enabled is False:
            return
        self._is_enabled = False
        self.handle_disable()
        self.signal.DISABLE.emit()

    def enable(self):
        if self.is_enabled:
            return
        self._is_enabled = True
        self.handle_enable()
        self.signal.ENABLE.emit()

    def handle_enable(self):
        """Stuff to do when enable is called (decorated method)"""

    @staticmethod
    def enabled_from(enables_list):

        return tuple(Enablable.ienabled_from(enables_list))

    def handle_disable(self):
        """Stuff to do when disable is called (decorated method)"""

    @staticmethod
    def ienabled_from(enables_list):

        for enablable in enables_list:
            if enablable.is_enabled:
                yield enablable


class Validable:

    def __init__(self, catching_errors=False):

        # self.validate = decorator_validate(self, self.handle_validate)

        self._catch_errors = catching_errors
        self.create_signal("VALIDATE")

    catching_erros = property(lambda self: self._catch_errors)

    def handle_validate(self):
        """Stuff to do when validate is called (decorated method)"""

    def validate(self):
        if self._catch_errors:
            try:
                self.handle_validate()
            except Exception as e:
                if isinstance(e, ApplicationExit):
                    raise e
                LOGGER.warning(f"Error while executing {self} validation: {e}")
        else:
            self.handle_validate()
        self.signal.VALIDATE.emit()


class Focusable(Enablable):
    """
    A Focusable is a Widget who listen to keyboard input, when it has the focus. Only one
    widget can be focused in the same time. When a new clic occurs and it doesn't collide
    this widget, it is defocused. If disabled, it cannot be focused.

    It has no 'focus' method since it is the application who decide who is focused or not.
    However, it can defocus itself or send a request for focusing the next focusable in the
    container parent

    When the mouse click on a Text inside a Button inside a focusable Zone inside a Scene,
    then only the youngest Focusable is focused
    Here, it is the Button -> display.focused_comp = Button
    """
    def __init__(self):

        Enablable.__init__(self)

        self._is_focused = False
        self.create_signal("FOCUS")
        self.create_signal("DEFOCUS")
        self.create_signal("KEYDOWN")
        self.create_signal("KEYUP")

        self.signal.DISABLE.connect(self.defocus, owner=self)
        self.signal.DEFOCUS.connect(self.handle_defocus, owner=self)
        self.signal.FOCUS.connect(self.handle_focus, owner=self)
        self.signal.KEYDOWN.connect(self.handle_keydown, owner=self)
        self.signal.KEYUP.connect(self.handle_keyup, owner=self)

    is_focused = property(lambda self: self._is_focused)

    def defocus(self):
        """Send a request for defocusing this widget"""
        if not self.is_focused:
            return
        self.scene._focus(None)

    def focus_antecedant(self):
        """
        Give the focus to the previous focusable (ranked by position) is self.parent
        """

        all_focs = []
        for child in self.parent.awake_children:
            if isinstance(child, Focusable):
                if child.is_enabled:
                    if child.is_visible:
                        all_focs.append(child)

        if len(all_focs) > 1:
            all_focs.sort(key=lambda c: (c.top, c.left))
            self.scene._focus(all_focs[(all_focs.index(self) -1) % len(all_focs)])

    def focus_next(self):
        """
        Give the focus to the next focusable (ranked by position) is self.parent
        """
        all_focs = []
        for child in self.parent.awake_children:
            if isinstance(child, Focusable):
                if child.is_enabled:
                    if child.is_visible:
                        all_focs.append(child)

        if len(all_focs) > 1:
            all_focs.sort(key=lambda c: (c.top, c.left))
            self.scene._focus(all_focs[(all_focs.index(self) + (1 if keyboard.mod.maj == 0 else -1)) % len(all_focs)])

    def handle_defocus(self):
        """Stuff to do when the widget loose the focus"""

    def handle_focus(self):
        """Stuff to do when the widget receive the focus"""

    def handle_keydown(self, key):
        """Stuff to do when a key is pressed"""

        if keyboard.mod.ctrl:
            if key in (pygame.K_a, pygame.K_c, pygame.K_v, pygame.K_x):
                if not hasattr(self, "_selection_rect_ref"):  # if not isinstance(self, Selector)
                    parent = self.parent
                    while not hasattr(parent, "_selection_rect_ref"):  # not infinite since Scene is a Selector
                        parent = parent.parent
                    parent.handle_keydown(key)  # parent is now the closest Selector parent

        elif key == pygame.K_TAB:
            if keyboard.mod.ctrl:  # Ctrl + TAB -> focus the previous Focusable inside this Selector
                if key == pygame.K_TAB:
                    self.focus_antecedant()
            else:  # TAB -> focus the next Focusable inside this Selector
                self.focus_next()
        elif key in (pygame.K_RIGHT, pygame.K_DOWN):
            self.focus_next()
        elif key in (pygame.K_LEFT, pygame.K_UP):
            self.focus_antecedant()

    def handle_keyup(self, key):
        """Stuff to do when a key is released"""


class Linkable(Focusable):
    """
    Abstract class for components who need to capture mouse clicks

    A Linkable is linked when a mouse LEFT BUTTON DOWN collide with it,
    and unlinked when the LEFT BUTTON UP occurs

    It has no 'link' or 'link_motion' method since it is the mouse who manages links.
    However, it can unlink itself

    WARNING : If a Linkable parent contains a Linkable child, and the LEFT BUTTON
              DOWN has occured on the child, then only the child will be linked

    NOTE : when a component is linked, you can access it via mouse.linked_comp
    """

    def __init__(self):

        Focusable.__init__(self)

        self.is_linked = False
        self.create_signal("LINK")  # TODO : Communicative ?
        self.create_signal("LINK_MOTION")
        self.create_signal("UNLINK")

        self.signal.LINK.connect(self.handle_link, owner=self)
        self.signal.LINK_MOTION.connect(self.handle_link_motion, owner=self)
        self.signal.UNLINK.connect(self.handle_unlink, owner=self)

    def handle_link(self):
        """Stuff to do when the widget gets linked"""

    def handle_link_motion(self, link_motion_event):
        """Stuff to do when the widget'link has changed"""

    def handle_unlink(self):
        """Stuff to do when the widget's link is over"""

    def unlink(self):
        """Send a request for unlinking this widget"""
        if self is not mouse.linked_comp:
            raise PermissionError(f"{self} is not linked")
        mouse._unlink()


class Clickable(Linkable, Validable):
    """
    Abstract class for components who need to handle when they are clicked

    A component is clicked when the link is released while the mouse is still
    hovering it (for more explanations about links, see Linkable)

    WARNING : If a Clickable parent contains a Clickable child, and the click
    has occured on the child, then only the child will handle the click
    """

    def __init__(self, catching_errors=False):

        Linkable.__init__(self)
        Validable.__init__(self, catching_errors=catching_errors)

        # def unlink():
        #     if self.collidemouse():
        #         self.validate()
        # self.signal.UNLINK.connect(unlink, owner=self)

    def handle_keydown(self, key):

        if key == pygame.K_RETURN:
            self.validate()

        else:
            super().handle_keydown(key)

    def handle_unlink(self):

        if self.collidemouse():
            self.validate()


class Dragable(Linkable):
    """
    Abstract class for components who want to be moved by mouse

    NOTE : a link_motion pointing a dragable's child will drag the parent if the child is not Linkable
    """
    # TODO : solve : a component can be set dragable two times, wich create an overdrag

    def __init__(self):

        Linkable.__init__(self)

        def drag(drag_event):
            self.move(*drag_event.rel)
        self.signal.LINK_MOTION.connect(drag, owner=self)

    @staticmethod
    def set_dragable(widget):
        if not hasattr(widget, "is_linked"):
            Linkable.__init__(widget)
            widget.is_linked = False
        # widget.handle_link.add(lambda: setattr(widget, "is_linked", True))
        # widget.handle_unlink.add(lambda: setattr(widget, "is_linked", False))

        def drag(drag_event):
            widget.move(*drag_event.rel)
        widget.signal.LINK_MOTION.connect(drag, owner=widget)


class Handler_SceneOpen:
    """
    A Handler_SceneOpen is a widget whose 'handle_scene_open' function is called when its scene gets open
    """
    def handle_scene_open(self):
        """Stuff to do when the widget's scene gets open"""


class Handler_SceneClose:
    """
    A Handler_SceneClose is a widget whose 'handle_scene_close' function is called when its scene is closed
    """
    def handle_scene_close(self):
        """Stuff to do when the widget'scene is closed"""

