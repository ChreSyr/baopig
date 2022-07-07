
import pygame
from baopig.io import LOGGER, mouse, keyboard
from baopig.documentation import Hoverable as HoverableDoc
from baopig.communicative import ApplicationExit
from baopig.time.timer import RepeatingTimer
from .widget import Widget


class Hoverable(HoverableDoc, Widget):

    def __init__(self, parent, **kwargs):
        Widget.__init__(self, parent, **kwargs)

        self._is_hovered = False
        self._indicator = None

        self.create_signal("HOVER")
        self.create_signal("UNHOVER")

        self.signal.HOVER.connect(self.handle_hover, owner=self)
        self.signal.UNHOVER.connect(self.handle_unhover, owner=self)

        def drop_hover():
            if self._is_hovered:
                mouse.update_hovered_comp()

        self.signal.HIDE.connect(drop_hover, owner=self)
        self.signal.SLEEP.connect(drop_hover, owner=self)

        def drop_hover_on_kill():
            if self._is_hovered:
                self.set_nontouchable()
                mouse.update_hovered_comp()

        self.signal.KILL.connect(drop_hover_on_kill, owner=self)

        def check_hover_gain():
            if self.collidemouse():
                mouse.update_hovered_comp()

        self.signal.SHOW.connect(check_hover_gain, owner=self)
        self.signal.WAKE.connect(check_hover_gain, owner=self)

        def check_hover():
            if self._is_hovered and not self.collidemouse():
                mouse.update_hovered_comp()
            elif self.collidemouse():
                mouse.update_hovered_comp()

        self.signal.MOTION.connect(check_hover, owner=self)
        self.signal.RESIZE.connect(check_hover, owner=self)

        if self.collidemouse():
            mouse.update_hovered_comp()

    indicator = property(lambda self: self._indicator)
    is_hovered = property(lambda self: self._is_hovered)


class Paintable(Widget):

    def __init__(self, parent, **kwargs):

        Widget.__init__(self, parent, **kwargs)

        """
        dirty is True while the component's surface have not been updated
        
        Particularly usefull when a hidden component got updated
        We wait until it get visible before rendering it
        
        0 : don't need to be updated
        1 : need to be updated once
        2 : need to be updated as much as possible
        """
        self._dirty = 0
        self._waiting_line = self.parent._children_to_paint

        def check_dirty():
            if self.dirty:
                self._waiting_line.add(self)

        self.signal.WAKE.connect(check_dirty, owner=self)

    dirty = property(lambda self: self._dirty)

    def paint(self):
        """
        This method is made for being overriden

        In your implementation, you can update the component's surface.
        If you use send_paint_request(), this method will be called when the next frame is rendered
        In fact, you can use paint() at any moment, but it is more efficient
        to update it through send_paint_request() if it is changing very often

        WARNING : never call this method yourself, always use self.send_paint_request()
        WARNING : don't forget to include a self.send_display_request()
        """

    def send_paint_request(self):

        if self._dirty == 0:
            self._dirty = 1
            if self.is_awake:  # the widget has no parent
                self._waiting_line.add(self)

    def set_dirty(self, dirty):
        """
        Works as pygame.DirtySprite :

        if set to 1, it is repainted and then set to 0 again
        if set to 2 then it is always dirty (repainted each scene, flag is not reset)
        0 means that it is not dirty and therefor not repainted again
        """

        assert dirty in (0, 1, 2)

        self._dirty = dirty
        if dirty:
            self._waiting_line.add(self)
        elif self in self._waiting_line:
            self._waiting_line.remove(self)


class _RunablesManager:
    def __init__(self):

        self._runables = set()
        self._running = set()
        self._paused = set()

    def add(self, runable):

        assert isinstance(runable, Runable)
        self._runables.add(runable)

    def pause(self, runable):

        assert runable in self._running
        self._running.remove(runable)
        self._paused.add(runable)

    def remove(self, runable):

        assert runable in self._runables
        self._runables.remove(runable)
        if runable in self._running:
            self._running.remove(runable)

    def resume(self, runable):

        assert runable in self._paused
        self._paused.remove(runable)
        self._running.add(runable)

    def start_running(self, runable):

        assert runable in self._runables
        assert runable not in self._running
        assert runable not in self._paused
        self._running.add(runable)

    def stop_running(self, runable):

        assert runable in self._running
        self._running.remove(runable)

    def run_once(self):

        for runable in self._running:
            runable.run()


_runables_manager = _RunablesManager()
del _RunablesManager


class Runable(Widget):

    def __init__(self, parent, start=False, **kwargs):

        Widget.__init__(self, parent, **kwargs)

        _runables_manager.add(self)

        self._is_running = False
        self._is_paused = False

        self.signal.SLEEP.connect(self.pause, owner=self)
        self.signal.WAKE.connect(self.resume, owner=self)
        self.signal.KILL.connect(lambda: _runables_manager.remove(self), owner=None)

        if start:
            self.start_running()

    is_paused = property(lambda self: self._is_paused)
    is_running = property(lambda self: self._is_running)

    def run(self):
        """Stuff to do when the object is running"""

    def pause(self):

        if not self.is_running:
            raise PermissionError("Cannot pause a Runable who didn't start yet")

        if self.is_paused is True:
            return

        _runables_manager.pause(self)
        self._is_running = False
        self._is_paused = True
        self.handle_pause()
        # self.signal.PAUSE.emit()

    def handle_pause(self):
        """Stuff to do when the object is paused"""

    def resume(self):

        if self.is_paused is False:
            raise PermissionError("Cannot resume a Runable who isn't paused")

        _runables_manager.resume(self)
        self._is_running = True
        self._is_paused = False
        self.handle_resume()
        # self.signal.RESUME.emit()

    def handle_resume(self):
        """Stuff to do when the object resume"""

    def start_running(self):

        if self.is_running is True:
            return

        _runables_manager.start_running(self)
        self._is_running = True
        self.handle_startrunning()
        # self.signal.START_RUNNING.emit()

    def handle_startrunning(self):
        """Stuff to do when the object starts to run"""

    def stop_running(self):

        if self.is_paused is True:
            self.resume()

        if self.is_running is False:
            return

        _runables_manager.stop_running(self)
        self._is_running = False
        self.handle_stoprunning()
        # self.signal.STOP_RUNNING.emit()

    def handle_stoprunning(self):
        """Stuff to do when the object stops to run"""


class Validable(Widget):

    def __init__(self, parent, catching_errors=False, **kwargs):

        Widget.__init__(self, parent, **kwargs)

        self._catch_errors = catching_errors
        self.create_signal("VALIDATE")

    catching_errors = property(lambda self: self._catch_errors)

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


class Enablable(Widget):

    def __init__(self, parent, **kwargs):

        Widget.__init__(self, parent, **kwargs)

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


class Focusable(Enablable):
    """
    A Focusable is a Widget who listen to keyboard input, when it has the focus. Only one
    widget can be focused in the same time. When a new clic occurs, and it doesn't collide
    this widget, it is defocused. If disabled, it cannot be focused.

    It has no 'focus' method since it is the application who decide who is focused or not.
    However, it can defocus itself or send a request for focusing the next focusable in the
    container parent

    When the mouse click on a Text inside a Button inside a focusable Zone inside a Scene,
    then only the youngest Focusable is focused
    Here, it is the Button -> display.focused_comp = Button
    """

    def __init__(self, parent, **kwargs):

        Enablable.__init__(self, parent, **kwargs)

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
        Give the focus to the previous focusable (ranked by position) in parent
        """

        all_focs = []
        for child in self.parent.children:
            if isinstance(child, Focusable):
                if child.is_enabled:
                    if child.is_visible:
                        all_focs.append(child)

        if len(all_focs) > 1:
            all_focs.sort(key=lambda c: (c.top, c.left))
            self.scene._focus(all_focs[(all_focs.index(self) - 1) % len(all_focs)])

    def focus_next(self):
        """
        Give the focus to the next focusable (ranked by position) in parent
        """
        all_focs = []
        for child in self.parent.children:
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
    Abstract class for widgets who need to capture mouse clicks

    A Linkable is linked when a mouse LEFT BUTTON DOWN collide with it,
    and unlinked when the LEFT BUTTON UP occurs

    It has no 'link' or 'link_motion' method since it is the mouse who manages links.
    However, it can unlink itself

    WARNING : If a Linkable parent contains a Linkable child, and the LEFT BUTTON
              DOWN has occured on the child, then only the child will be linked

    NOTE : when a widget is linked, you can access it via mouse.linked_comp
    """

    def __init__(self, parent, **kwargs):
        Focusable.__init__(self, parent, **kwargs)

        self.is_linked = False
        self.create_signal("LINK")
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
    Abstract class for widgets who need to handle when they are clicked

    A widget is clicked when the link is released while the mouse is still
    hovering it (for more explanations about links, see Linkable)

    WARNING : If a Clickable parent contains a Clickable child, and the click
    has occured on the child, then only the child will handle the click
    """

    def __init__(self, parent, catching_errors=False, **kwargs):

        Linkable.__init__(self, parent, **kwargs)
        Validable.__init__(self, parent, catching_errors=catching_errors)

    def handle_keydown(self, key):

        if key == pygame.K_RETURN:
            self.validate()

        else:
            super().handle_keydown(key)

    def handle_unlink(self):
        # TODO : test : if a linked Clickable is hidden, UNLINK is emitted but VALIDATE is not emitted

        if self.collidemouse():
            self.validate()


class Draggable(Linkable):
    """
    Class for widgets who want to be moved by mouse

    NOTE : a LINK_MOTION pointing a dragable's child will drag the parent if the child is not Linkable
    """

    def handle_link_motion(self, link_motion_event):
        self.move(*link_motion_event.rel)


class ResizableWidget(Widget):  # TODO : solve : try_it_yourself.code is not resized
    """Class for widgets who can be resized"""

    STYLE = Widget.STYLE.substyle()
    STYLE.create(
        width=None,  # must be filled
        height=None,  # must be filled
    )

    def __init__(self, parent, size=None, **kwargs):
        """NOTE : can be size=(50, 45) or width=50, height=45"""

        self.inherit_style(parent, options=kwargs)

        if size is None:
            self._asked_size = self.style["width"], self.style["height"]
        else:
            self._asked_size = size

        if "surface" not in kwargs:
            kwargs["surface"] = pygame.Surface(self._get_asked_size(), pygame.SRCALPHA)

        # assert not hasattr(self, "_weakref")
        Widget.__init__(self, parent, **kwargs)

        self.signal.RESIZE.connect(self.handle_resize, owner=None)
        self.origin.reference.signal.RESIZE.connect(self._update_size, owner=self)

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
                    size[i] = self.parent.content_rect.size[i] * int(coord[:-1]) / 100

        return size

    def _update_size(self):

        asked_size = self._asked_size
        self.resize(*self._get_asked_size())
        self._asked_size = asked_size

    def handle_resize(self):
        """Stuff to do when the widget is resized"""

    def resize(self, w, h):
        """Sets up the new component's surface"""

        if self.has_locked("width"):
            raise PermissionError("Cannot resize : the width is locked")
        if self.has_locked("height"):
            raise PermissionError("Cannot resize : the height is locked")
        # if (w, h) == self._asked_size:
        #     return

        self._asked_size = w, h

        asked_size = self._get_asked_size()
        if asked_size == self.size:
            return

        self.set_surface(pygame.Surface(asked_size, pygame.SRCALPHA))

    def resize_height(self, h):

        self.resize(self._asked_size[0], h)

    def resize_width(self, w):

        self.resize(w, self._asked_size[1])


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
