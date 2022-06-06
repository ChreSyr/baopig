

from baopig._debug import debug_screen_updates
from .utilities import *
from .style import Theme
from .layer import Layer
from .zone import Zone, Widget
from .selections import Selector


def decorator_open(scene, open):
    functools.wraps(open)
    def wrapped_func(*args, **kwargs):
        app = scene.application
        if app.focused_scene is scene: return

        with paint_lock:
            scene.pre_open()
            if app.focused_scene:
                app.focused_scene._close()
            app._focused_scene = scene
            app._update_display()
            scene.container_open()
            res = open(*args, **kwargs)
            scene.paint(recursive=True)

        LOGGER.debug("Open scene : {}".format(scene))
        # scene.signal.OPEN.emit()
        return res
    return wrapped_func


class Scene(Zone, Selector, Openable, Closable):
    """
    A Scene is like a page in an application. It can be the menu, the parameters page...

    If size parameter is filled, then when we swap to this scene, the application will be resized
    to 'size'. When it will swap again to another scene, if no size is required, the application
    will be resized to its original size.
    """

    STYLE = Zone.STYLE.substyle()
    STYLE.modify(
        background_color="theme-color-scene_background",
    )

    def __init__(self, application, size=None, **options):

        self.open = decorator_open(self, self.open)

        if "name" not in options:
            options["name"] = self.__class__.__name__
        self._application = self._app = application

        if "theme" in options:
            theme = options.pop("theme")
            if not isinstance(theme, str):  # theme name
                assert isinstance(theme, Theme)
                if not theme.issubtheme(application.theme):
                    raise PermissionError("Must be an application sub-theme")
        else:
            theme = application.theme.subtheme()
        self.inherit_style(theme)

        Zone.__init__(
            self,
            parent=self,
            pos=(0, 0),
            size=application.default_size if size is None else size,
            **options
        )
        Selector.__init__(self)

        # self._mode = 0
        self._asked_size = size
        self._mode_before_fullscreen = None
        self._size_before_fullscreen = None
        self._focused_comp_ref = lambda: None

        self.enable_selecting()

    def __str__(self):

        return self.name

    abs_left = 0  # End of recursive call
    abs_top = 0  # End of recursive call
    application = property(lambda self: self._application)
    asked_size = property(lambda self: self._asked_size)
    focused_comp = property(lambda self: self._focused_comp_ref())
    # mode = property(lambda self: self._mode)
    painter = property(lambda self: self._application._painter)
    scene = property(lambda self: self)  # End of recursive call

    def _add_child(self, widget):

        if widget is self:
            return self.application._add_scene(self)  # a scene is a root
        super()._add_child(widget)

    def _close(self):

        if self.application.focused_scene is not self: return
        self.container_close()
        self.close()
        Widget.set_surface(self, pygame.Surface(self.size))  # not pygame.display anymore
        self._focus(None)
        self.application._focused_scene = None

        # LOGGER.debug("Close scene : {}".format(self))

    def _dirty_child_TBR(self, child, dirty):

        if child is self:
            self._dirty = dirty
            return
        super()._dirty_child(child, dirty)

    def _focus(self, widget):

        if widget == self.focused_comp: return

        # DEFOCUS
        old_focused = self.focused_comp
        if old_focused is not None:
            assert old_focused.is_focused
            old_focused._is_focused = False

        if widget is None:
            widget = self
        else:
            assert widget.is_visible
        assert not widget.is_focused

        # FOCUS
        widget._is_focused = True
        self._focused_comp_ref = widget.get_weakref()  # (lambda: None) if widget is None else

        if old_focused is not None: old_focused.signal.DEFOCUS.emit()
        widget.signal.FOCUS.emit()
        # print("FOCUS", widget)

    def _update_rect(self):

        if self._rect_to_update is None: return
        assert self.application.focused_scene is self

        with paint_lock:

            rect = self._rect_to_update
            self._rect_to_update = None
            # for rect in rects_to_update:  # TODO : rect_to_update ? try fps
            self.surface.fill(self.background_color, rect)
            for layer in self.layers:
                for child in layer.visible:
                    if child.hitbox.colliderect(rect):
                        try:
                            collision = child.hitbox.clip(rect)
                            self.surface.blit(
                                child.surface.subsurface(
                                    (collision.left - child.rect.left, collision.top - child.rect.top) + collision.size),
                                collision.topleft
                            )
                        except pygame.error as e:
                            # can be raised from a child.surface who is a subsurface from self.surface
                            assert child.surface.get_parent() is self.surface
                            child._flip_without_update()  # overdraw child.hitbox

            if debug_screen_updates:
                LOGGER.info("update in {} :  {}".format(self, rect))

            if debug_with_assert: assert pygame.display.get_surface() is self.surface
            pygame.display.update(rect)

        if self.painter.is_recording and self.painter.is_recording.only_at_change:
            pygame.image.save(self.surface,
                              self.painter.record_directory + "record_{:0>3}.png".format(
                                  self.painter.record_index))
            self.painter.record_index += 1

    def _warn_parent(self, rect):
        raise PermissionError("Should never be called")

    def divide(self, side, width):
        raise PermissionError("Cannot divide a Scene")  # TODO : rework Zone.divide

    def pre_open(self):
        """Stuff to do right before this scene is open"""

    def receive(self, event):
        """This method is called at every pygame event"""

    def resize(self, w, h):

        if (w, h) == self.asked_size: return
        self._asked_size = (w, h)
        if self is self.application.focused_scene:
            self.application._update_display()

    def run(self):
        """Stuff to repeat endlessly while this scene is focused"""

    def set_mode_TO_REMOVE(self, mode):

        if mode is self.mode: return

        assert mode in (0, pygame.NOFRAME, pygame.RESIZABLE, pygame.FULLSCREEN)

        if mode is pygame.FULLSCREEN and self.mode != mode:
            self._mode_before_fullscreen = self.mode
            self._size_before_fullscreen = self.asked_size

            # print("Asked for fullscreen")
            # mode = 0

        self._mode = mode
        self.application._update_display()

    def toggle_debugging(self):

        if not hasattr(self, "debug_layer"):
            self.debug_layer = Layer(self, name="debug_layer", level=self.layers_manager.FOREGROUND)
            from baopig.prefabs.debugzone import DebugZone
            self.debug_zone = DebugZone(self)
        else:
            self.debug_zone.toggle_debugging()

    def toggle_fullscreen(self):

        if self.mode == pygame.FULLSCREEN:
            self.set_mode(self._mode_before_fullscreen)
        else:
            self.set_mode(pygame.FULLSCREEN)

    def asleep(self): raise PermissionError("A Scene cannot sleep")
    def wake(self): raise PermissionError("A Scene cannot sleep")
    def show(self): pass
    def hide(self): pass
