from baopig.io import LOGGER
from .utilities import *
from .style import Theme
from .layer import Layer
from .zone import Zone, Widget
from .selections import Selector


class Scene(Zone, Selector, Handler_SceneOpen, Handler_SceneClose):
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

    def __init__(self, application, size=None, can_select=True, **options):

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
        Selector.__init__(self, parent=self, can_select=can_select)

        # self._mode = 0
        self._asked_size = self.size
        self._mode_before_fullscreen = None
        self._size_before_fullscreen = None
        self._focused_comp_ref = lambda: None

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
        self._container_close()
        self.handle_scene_close()
        Widget.set_surface(self, pygame.Surface(self.size))  # not pygame.display anymore
        self._focus(None)
        self.application._focused_scene = None

        # LOGGER.debug("Close scene : {}".format(self))

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

    def _warn_parent(self, rect):

        pygame.display.update(rect)

        if self.painter.is_recording and self.painter.is_recording.only_at_change:
            pygame.image.save(self.surface,
                              self.painter.out_directory + "record_{:0>3}.png".format(
                                  self.painter.record_index))
            self.painter.record_index += 1

    def divide(self, side, width):
        raise PermissionError("Cannot divide a Scene")  # TODO : rework Zone.divide

    def kill(self):

        if not self.is_alive:
            return
        if self.app.focused_scene is self:
            raise PermissionError("Cannot kill a focused scene")

        with paint_lock:
            for child in tuple(self.all_children):
                child.kill()
            self.disconnect()
            self.signal.KILL.emit(self._weakref)
            self._weakref._comp = None
            self.app.scenes.remove(self)

        del self

    def open(self):

        app = self.application
        if app.focused_scene is self:
            return

        with paint_lock:
            self.pre_open()
            scene_to_close = app.focused_scene
            app._focused_scene = self
            if scene_to_close:
                scene_to_close._close()
            app._update_display()
            self._container_open()
            self.handle_scene_open()
            self.paint(recursive=True)

        LOGGER.debug("Open scene : {}".format(self))

    def pre_open(self):
        """Stuff to do right before this scene is open"""

    def receive(self, event):
        """This method is called at every pygame event"""

    def resize(self, w, h):

        if (w, h) == self.asked_size: return
        self._asked_size = w, h
        if self is self.application.focused_scene:
            self.application._update_display()

    def run(self):
        """Stuff to repeat endlessly while this scene is focused"""

    def set_mode_TBR(self, mode):

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

    def toggle_fullscreen(self):  # TODO : fullscreen

        if self.mode == pygame.FULLSCREEN:
            self.set_mode(self._mode_before_fullscreen)
        else:
            self.set_mode(pygame.FULLSCREEN)

    def sleep(self): raise PermissionError("A Scene cannot sleep")
    def wake(self): raise PermissionError("A Scene cannot sleep")
    def show(self): pass
    def hide(self): pass
