import pygame
from baopig.io import LOGGER, mouse, keyboard
from baopig.documentation import ApplicationExit, Selector
from baopig.documentation import Focusable as FocusableDoc
from baopig.documentation import HoverableByMouse as HoverableByMouseDoc
from baopig.documentation import LinkableByMouse as LinkableByMouseDoc
from baopig.documentation import Runable as RunableDoc
from baopig.documentation import Validable as ValidableDoc
from baopig.time.timer import RepeatingTimer
from .widget import Widget


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

    def handle_mousebuttondown(self, event):
        """Stuff to do when the mouse clicks on the widget - called before handle_link()"""

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

        self.create_signal("FOCUS")
        self.create_signal("DEFOCUS")

        self.signal.HIDE.connect(self.defocus, owner=None)
        self.signal.SLEEP.connect(self.defocus, owner=None)

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


class MaintainableByFocus(Widget):
    """ Class for widgets who need to be open as long as they have a focused maintainer """

    def __init__(self, parent, is_valid_maintainer):

        Widget.__init__(self, parent)

        self._maintainer_ref = lambda: None  # this is the child that is focused
        self.is_valid_maintainer = is_valid_maintainer

    maintainer = property(lambda self: self._maintainer_ref())

    def _handle_maintainer_defocus(self):

        self.maintainer.signal.DEFOCUS.disconnect(self._handle_maintainer_defocus)

        focused_widget = self.scene.focused_widget
        if focused_widget is None:
            return self.close()

        if self.is_valid_maintainer(focused_widget):
            self._maintainer_ref = focused_widget.get_weakref()
            self.maintainer.signal.DEFOCUS.connect(self._handle_maintainer_defocus, owner=self)

        else:
            self.close()

    def close(self):
        """ Stuff to do when there is no focused maintainer anymore """

    def open(self, maintainer):

        if not self.is_valid_maintainer(maintainer):
            raise PermissionError(f"Invalid maintainer : {maintainer}")

        self._maintainer_ref = maintainer.get_weakref()
        self.maintainer.signal.DEFOCUS.connect(self._handle_maintainer_defocus, owner=self)


class DraggableByMouse(LinkableByMouse):
    """
    Class for widgets who want to be moved by mouse
    """

    def handle_link_motion(self, rel):
        self.move(*rel)


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
