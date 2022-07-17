import pygame
from baopig.io import LOGGER, mouse, keyboard
from baopig.documentation import ApplicationExit, Selector
from baopig.documentation import Focusable as FocusableDoc
from baopig.documentation import HoverableByMouse as HoverableByMouseDoc
from baopig.documentation import LinkableByMouse as LinkableByMouseDoc
from baopig.documentation import Paintable as PaintableDoc
from baopig.documentation import ResizableWidget as ResizableWidgetDoc
from baopig.documentation import Runable as RunableDoc
from baopig.documentation import Validable as ValidableDoc
from baopig.time.timer import RepeatingTimer
from .widget import Widget, HasStyle


class Validable(ValidableDoc):

    def __init__(self, catching_errors=False):

        self._catching_errors = catching_errors

    catching_errors = property(lambda self: self._catching_errors)

    def handle_validate(self):
        """ Stuff to do when validate is called """

    def validate(self):
        if self._catching_errors:
            try:
                self.handle_validate()
            except ApplicationExit as e:
                raise e
            except Exception as e:
                LOGGER.warning(f"Error while executing {self} validation: {e}")
        else:
            self.handle_validate()


class Paintable(PaintableDoc, Widget):

    def __init__(self, parent, **kwargs):

        Widget.__init__(self, parent, **kwargs)

        self._dirty = 0
        self._waiting_line = self.parent._children_to_paint

        def check_dirty():
            if self.dirty:
                self._waiting_line.add(self)

        self.signal.WAKE.connect(check_dirty, owner=self)

    dirty = property(lambda self: self._dirty)

    def send_paint_request(self):

        if self._dirty == 0:
            self._dirty = 1

            if self.is_awake:
                self._waiting_line.add(self)

    def set_dirty(self, val):

        assert val in (0, 1, 2)

        self._dirty = val

        if self.is_awake:
            if val:
                self._waiting_line.add(self)
            elif self in self._waiting_line:
                self._waiting_line.remove(self)


class Runable(RunableDoc, Widget):

    def __init__(self, parent, **kwargs):
        Widget.__init__(self, parent, **kwargs)

        self._is_running = False

    is_running = property(lambda self: self._is_running)

    def set_running(self, val):
        self._is_running = bool(val)


class HoverableByMouse(HoverableByMouseDoc, Widget):  # TODO : auomatic update when scroll

    def __init__(self, parent, **kwargs):
        Widget.__init__(self, parent, **kwargs)

        self._is_hovered = False
        self._indicator = None

        # NOTE : these signals are necessary for Indicator
        self.create_signal("HOVER")
        self.create_signal("UNHOVER")

        self.signal.HOVER.connect(self.handle_hover, owner=self)
        self.signal.UNHOVER.connect(self.handle_unhover, owner=self)

        # def drop_hover():
        #     if self._is_hovered:
        #         mouse.update_hovered_widget()
        #
        # self.signal.HIDE.connect(drop_hover, owner=self)
        # self.signal.SLEEP.connect(drop_hover, owner=self)
        #
        # def drop_hover_on_kill():
        #     if self._is_hovered:
        #         mouse.update_hovered_widget()
        #
        # self.signal.KILL.connect(drop_hover_on_kill, owner=self)
        #
        # def check_hover_gain():
        #     if self.collidemouse():
        #         mouse.update_hovered_widget()
        #
        # self.signal.SHOW.connect(check_hover_gain, owner=self)
        # self.signal.WAKE.connect(check_hover_gain, owner=self)
        #
        # def check_hover():
        #     if self._is_hovered and not self.collidemouse():
        #         mouse.update_hovered_widget()
        #     elif self.collidemouse():
        #         mouse.update_hovered_widget()
        #
        # self.signal.MOTION.connect(check_hover, owner=self)
        # self.signal.RESIZE.connect(check_hover, owner=self)
        #
        # if self.collidemouse():
        #     mouse.update_hovered_widget()

    indicator = property(lambda self: self._indicator)
    is_hovered = property(lambda self: self._is_hovered)


# ...


class LinkableByMouse(LinkableByMouseDoc, HoverableByMouse):

    def __init__(self, parent, **kwargs):
        HoverableByMouse.__init__(self, parent, **kwargs)

        self.is_linked = False  # non-protected field, manipulated by the mouse

    def handle_link(self):
        """Stuff to do when the widget gets linked"""

    def handle_link_motion(self, rel):
        """Stuff to do when the widget'link has changed"""

    def handle_unlink(self):
        """Stuff to do when the widget's link is over"""

    def unlink(self):
        """Send a request for unlinking this widget"""
        if self.is_linked:
            mouse._unlink()


class Focusable(FocusableDoc, LinkableByMouse):

    def __init__(self, parent, **kwargs):

        LinkableByMouse.__init__(self, parent, **kwargs)

        self._is_focused = False

    is_focused = property(lambda self: self._is_focused)

    def defocus(self):
        """ Send a request for defocusing this widget """
        if self.is_focused:
            self.scene.focus(None)

    def handle_defocus(self):
        """ Called when the widget looses the focus """

    def handle_focus(self):
        """ Called when the widget receives the focus """

    # KEY EVENTS LISTENING

    is_listening_keyevents = property(lambda self: self._is_focused)

    def handle_keydown(self, key):
        """ Called when a key is pressed """

        if keyboard.mod.ctrl:  # TODO : ctrl or cmd
            if key in (pygame.K_a, pygame.K_c, pygame.K_v, pygame.K_x):
                if not isinstance(self, Selector):  # if not isinstance(self, Selector)
                    selector = self.parent
                    while not isinstance(selector, Selector):  # not infinite since Scene is a Selector
                        selector = selector.parent
                    selector.handle_keydown(key)  # parent is now the closest Selector parent

        if key == pygame.K_TAB:
            self.handle_tab()

    def handle_tab(self):
        """
        Give the focus to the next Focusable (ranked by position) in parent
        If maj is pressed, gives the focus to the previous Focusable
        """
        all_focs = []
        for child in self.parent.children:
            if isinstance(child, Focusable):
                if child.is_visible:
                    all_focs.append(child)

        # TAB       -> focus the next Focusable inside this widget's parent
        # Maj + TAB -> focus the previous Focusable inside this widget's parent
        d = 1 if keyboard.mod.maj == 0 else -1

        if len(all_focs) > 1:
            all_focs.sort(key=lambda c: (c.rect.top, c.rect.left))
            self.scene.focus(all_focs[(all_focs.index(self) + d) % len(all_focs)])


class DraggableByMouse(LinkableByMouse):
    """
    Class for widgets who want to be moved by mouse
    """

    def handle_link_motion(self, rel):
        self.move(*rel)


class ResizableWidget(ResizableWidgetDoc, Widget):  # TODO : merge with Widget

    def __init__(self, parent, size=None, **kwargs):
        """NOTE : can be size=(50, 45) or width=50, height=45"""

        HasStyle.__init__(self, parent, options=kwargs)

        if size is None:
            self._asked_size = self.style["width"], self.style["height"]
        else:
            self._asked_size = size

        if "surface" not in kwargs:
            kwargs["surface"] = pygame.Surface(self._get_asked_size(), pygame.SRCALPHA)

        # assert not hasattr(self, "_weakref")
        Widget.__init__(self, parent, **kwargs)

        def update_size_from_askedsize():

            asked_size = self._asked_size
            self.resize(*self._get_asked_size())
            self._asked_size = asked_size

        self.signal.WAKE.connect(update_size_from_askedsize, owner=self)
        self.pos_manager.reference.signal.RESIZE.connect(update_size_from_askedsize, owner=self)

    def _get_asked_size(self):

        size = self._asked_size
        with_percentage = False
        for coord in size:
            if isinstance(coord, str):
                # hard stuff
                assert coord[-1] == '%', size
                with_percentage = True
            else:
                assert isinstance(coord, (int, float)), f"Wrong value in size : {coord} (must be a number)"
                assert coord >= 0, f"Wrong value in size : {coord} (must be positive)"

        if with_percentage:
            size = list(size)
            for i, coord in enumerate(size):
                if isinstance(coord, str):
                    size[i] = self.parent.rect.size[i] * float(coord[:-1]) / 100

        return size

    def _update_surface_from_resize(self, asked_size):  # TODO : envisager une fusion avec paint()
        """ Update the surface from the asked size - Only called by resize()"""

        self.set_surface(pygame.Surface(asked_size, pygame.SRCALPHA))

    def resize(self, width, height):
        """Sets up the new widget's surface"""

        if self.has_locked("width"):
            raise PermissionError("Cannot resize : the width is locked")
        if self.has_locked("height"):
            raise PermissionError("Cannot resize : the height is locked")

        self._asked_size = width, height

        if self.is_asleep:
            return

        asked_size = self._get_asked_size()
        if asked_size == self.rect.size:
            return

        self._update_surface_from_resize(asked_size)

    def resize_height(self, height):

        self.resize(self._asked_size[0], height)

    def resize_width(self, width):

        self.resize(width, self._asked_size[1])


class RepetivelyAnimated(Widget):  # TODO : rework default anitmations
    """
    A RepetivelyAnimated is a widget who blinks every interval seconds

    Exemple :

        class Lighthouse(RepetivelyAnimated):

    """

    def __init__(self, parent, interval, **kwargs):
        """
        The widget will appear and disappear every interval seconds
        :param interval: the time between appear and disappear
        """

        Widget.__init__(self, parent, **kwargs)

        assert isinstance(interval, (int, float)), "interval must be a float or an integer"

        self.interval = interval

        def blink():
            if self.is_visible:
                self.hide()
            else:
                self.show()

        self._countdown_before_blink = RepeatingTimer(interval, blink)
        self._need_start_animation = False
        self.signal.SLEEP.connect(self.handle_sleep, owner=None)
        self.signal.WAKE.connect(self.handle_wake, owner=None)
        self.signal.KILL.connect(self._countdown_before_blink.cancel, owner=None)

    def handle_sleep(self):

        self._need_start_animation = self._countdown_before_blink.is_running
        self._countdown_before_blink.cancel()

    def start_animation(self):

        if self.is_asleep:
            self._need_start_animation = True
            return

        if self._countdown_before_blink.is_running:
            self._countdown_before_blink.cancel()
        self._countdown_before_blink.start()

    def stop_animation(self):

        if self.is_asleep:
            self._need_start_animation = False
            return

        self._countdown_before_blink.cancel()

    def handle_wake(self):

        if self._need_start_animation:
            self._countdown_before_blink.start()
        self._need_start_animation = False
