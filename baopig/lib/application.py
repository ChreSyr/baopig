#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time

from baopig.pybao import WeakList
from baopig.documentation import ApplicationExit
from baopig.io import keyboard, mouse, LOGGER
from .style import HasStyle, Theme, StyleClass
from .widget import Widget
from .utilities import *


class Application(HasStyle):
    """
    This is the main class in baopig
    It needs to be instanced before everything else
    """
    STYLE = StyleClass()

    def __init__(self, name=None, theme=None, size=None, mode=pygame.RESIZABLE):

        if name is None:
            name = self.__class__.__name__
        if theme is None:
            theme = Theme()

        HasStyle.__init__(self, theme)

        pygame.init()
        info = pygame.display.Info()

        self._name = name
        self._is_launched = False
        self._is_running = False
        self._fps = None
        self._default_mode = mode
        self._default_size = pygame.display.list_modes()[2] if size is None else size
        self._current_mode = self._current_size = None
        self._max_resolution = (info.current_w, info.current_h)
        self._is_fullscreen_TO_REMOVE = False
        self._scenes = WeakList()
        self._focused_scene = None
        self._caption = self.name
        self._painter = None  # To be set in self.launch()
        self._time_manager = None  # To be set in self.launch()

        # debug attributes
        self._debug_averagefps = False
        self._debug_launchtime = False

        mouse._application = self
        keyboard._application = self

        pygame.display.set_caption(self.name)

        self.launch_time = time.time()

    default_mode = property(lambda self: self._default_mode)
    default_size = property(lambda self: self._default_size)
    focused_scene = property(lambda self: self._focused_scene)
    fps = property(lambda self: self._fps)
    is_fullscreen = property(lambda self: bool(self.default_mode & pygame.FULLSCREEN))
    is_launched = property(lambda self: self._is_launched)
    max_resolution = property(lambda self: self._max_resolution)
    name = property(lambda self: self._name)
    painter = property(lambda self: self._painter)
    scenes = property(lambda self: self._scenes)
    size = property(lambda self: self._focused_scene.rect.size)

    def _add_scene(self, scene):

        assert scene not in self.scenes
        if not self.scenes:
            self._focused_scene = scene
        self.scenes.append(scene)

    def _manage_events(self):

        # Events listening
        # Only apply on keyboard, mouse and application's operations
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F6:
                self.exit("FORCED EXIT (F6)")
            elif event.type == pygame.QUIT:
                self.exit()

            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                mouse.receive(event)
            elif event.type in (pygame.KEYDOWN, pygame.KEYUP):
                keyboard.receive(event)
            elif event.type == pygame.ACTIVEEVENT:
                """
                gain  : 1 -> mouse in window
                        2 -> mouse outside window
                        
                state : 0 -> no state change
                        1 -> focus state just changed
                        2 -> iconify state just changed
                """
                if not hasattr(event, "gain"):  # Empty ACTIVEEVENT
                    continue
                if event.state == 2 and event.gain == 1:
                    self.refresh()
            elif event.type == pygame.VIDEORESIZE:
                if event.size != self.focused_scene.size:
                    self._default_size = event.size
                    self.focused_scene.resize(*event.size)
                else:
                    # We need an update
                    self.refresh()

            # DEFAULT SHORTKEYS
            if event.type == pygame.KEYDOWN:
                if keyboard.mod.ctrl:
                    # Cmd + e -> toggle debugging
                    if event.key == pygame.K_e:
                        if keyboard.mod.maj:
                            _ = self.focused_scene.children
                            raise Exception("Made for debugging")
                        self.toggle_debugging()
                    # Cmd + g -> collect garbage
                    elif event.key == pygame.K_g:
                        import gc
                        gc.collect()
                        LOGGER.info("Garbage collected")
                    # Cmd + r -> toggle recording (if Maj: save application.surface only when it changes)
                    elif event.key == pygame.K_r:
                        if self.painter.is_recording:
                            self.painter.stop_recording()
                        else:
                            self.painter.start_recording(only_at_change=keyboard.mod.maj)

                elif keyboard.mod.alt:
                    pass  # Nothing implemented

                elif event.key == pygame.K_ESCAPE:  # quit fullscreen or exit
                    if self.is_fullscreen:
                        self.set_display_mode(self.default_mode - pygame.FULLSCREEN)
                    else:
                        self.exit("pressed ESCAPE")
                # elif event.key == pygame.K_F5:  # fullscreen
                #     self.focused_scene.toggle_fullscreen()
                elif event.key == pygame.K_F4:  # minimize
                    self.iconify()
                elif event.key == pygame.K_F3:  # refresh
                    self.refresh()
                    LOGGER.info("Display refreshed")
                elif event.key == pygame.K_F2:  # screenshot TODO : A faire avec un clic droit
                    self.painter.screenshot()
                    LOGGER.info("Screenchot !")

            # TRANSMITTING EVENT
            focused = self.focused_scene.focused_widget
            if focused is not None:
                if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                    assert focused.is_focused
                    assert focused.is_alive
                    assert focused.is_visible  # ?
                    assert focused.is_awake
                if event.type == pygame.KEYDOWN:
                    focused.handle_keydown(event.key)
                elif event.type == pygame.KEYUP:
                    focused.handle_keyup(event.key)
            # TODO
            # else:
            #     raise AssertionError

            # Events optionnal treatment
            self.focused_scene.handle_event(event)

    def _run(self):
        """
        Launch the application
        """

        try:

            self._is_running = True

            while self._is_running:

                # User events
                self._manage_events()

                # Possible advanced events treatments
                self._time_manager.update()
                self.focused_scene._container_run()

                # Possible coded stuff
                self.focused_scene.run()

                # If needed, drawing display
                if pygame.display.get_active():
                    self.painter._can_draw.set()

        except Exception as e:
            if isinstance(e, ApplicationExit):
                if str(e) != 'None':
                    LOGGER.info("{} exit : '{}'".format(self.__class__.__name__, e))
            else:
                raise e

        if self._debug_averagefps:
            fps_history = self.painter.fps_history
            if len(fps_history) > 0:
                fps_moy = sum(fps_history) / len(fps_history)
                LOGGER.info("{} ran with a global average of {} FPS"
                            "".format(self.__class__.__name__, fps_moy))
            else:
                LOGGER.info("{} didn't ran enough for a global FPS average".format(self.__class__.__name__))

        self._is_launched = False
        pygame.quit()

    def _update_display(self):
        """Updates display mode and size"""

        if self.is_launched:

            # self._is_fullscreen_TO_REMOVE = self.focused_scene.size == self.max_resolution

            # current_size = pygame.display.get_window_size()
            # current_mode = pygame.display.get

            size = self.focused_scene.asked_size
            if size is None:
                size = self.default_size

            # TODO : remove scene.mode ?
            mode = self.default_mode

            if size == self._current_size and mode == self._current_mode:
                Widget.set_surface(self.focused_scene, pygame.display.get_surface())
                return

            Widget.set_surface(self.focused_scene, pygame.display.set_mode(size, mode))

            if size != self._current_size:
                LOGGER.fine(f"Display size set to {size}")

            self._current_mode = mode
            self._current_size = size

    def set_debug(self, **kwargs):
        """
        arguments must be True or False
        keywords must be from this list :
            averagefps, launchtime
        """

        for kw, arg in kwargs.items():
            if arg is not None:
                assert hasattr(self, "_debug_" + kw)
                self.__setattr__("_debug_" + kw, arg)

    def exit(self, reason=None):

        self._is_running = False
        self.painter.stop()
        self.handle_app_close()

        # NOTE : after some tests, a pygame error makes it impossible to restart a closed application
        #        If I can make it work, and the program launches the app again
        # self._is_launched = False
        # self._current_size = self._current_mode = None

        raise ApplicationExit(reason)

    def flash(self):
        """
        Create a short flash on the application
        Can be used when an error occurs, like a wrong user input
        """
        pass  # TODO : implemented this functionnality

    def handle_app_close(self):
        """Stuff to do when the app is closed"""

    @staticmethod
    def iconify():

        with paint_lock:
            # if self.is_fullscreen:
            #     self.exit_fullscreen()  # TODO : test it
            pygame.display.iconify()

    def launch(self):

        if len(self.scenes) == 0:
            from baopig.prefabs.presentationscene import PresentationScene
            PresentationScene(self)

        assert not self.is_launched and pygame.get_init(), \
            "An application can only be launched once, due to pygame restrictions"
        self._is_launched = True

        from baopig.time.timemanager import time_manager
        self._time_manager = time_manager
        from baopig.threads import PainterThread
        self._painter = PainterThread(self)
        self.painter.set_fps(self._fps)

        assert self.focused_scene is not None
        scene = self.focused_scene
        self._focused_scene = None  # whitout this line, scene.open() does nothing, because it thinks it's already open
        scene.open()
        assert self.focused_scene is scene

        pygame.display.set_mode(self.size, self.default_mode)  # prevents a threading lag with painter.start()
        self.focused_scene.focus(self.focused_scene)
        self.painter.start()

        pygame.scrap.init()  # clipboard uses
        pygame.event.get()  # ignore events that took place during the app's load
        mouse._pos = pygame.mouse.get_pos()
        self._run()

    def open(self, scene):

        if isinstance(scene, str):
            for s in self.scenes:
                if s.name == scene:
                    scene = s
                    break
        if scene not in self.scenes:
            raise PermissionError(f"Unknown scene : '{scene}' "
                                  f"(existing scenes : {tuple(str(s) for s in self.scenes)})")

        scene.open()

    def refresh(self):
        """
        Send a paintrequest to every container in focused_scene
        if only_containers is False, sends a paintrequest to every focused_scene's children
        """
        # TODO : refresh & screenshot buttons by default
        self.focused_scene._container_refresh(recursive=True, only_containers=False)

    def set_caption(self, title, icontitle=""):

        self._caption = title
        pygame.display.set_caption(title, icontitle)

    def set_default_size(self, size):  # TODO : resize ?

        if size == self.default_size:
            return
        self._default_size = size
        for scene in self.scenes:
            if scene.asked_size is not None:
                scene.resize(*self.default_size)

    def set_fps(self, fps):

        self._fps = fps
        if self.painter is not None:
            self.painter.set_fps(fps)

    @staticmethod
    def set_icon(icon):

        pygame.display.set_icon(icon)

    def set_display_mode(self, mode):

        if mode is self.default_mode:
            return

        assert mode in (0, pygame.NOFRAME, pygame.RESIZABLE, pygame.FULLSCREEN)

        # if mode is pygame.FULLSCREEN and self.mode != mode:
        #   self._mode_before_fullscreen = self.focused_scene.mode
        # self._size_before_fullscreen = self.asked_size

        # mode = 0

        self._default_mode = mode
        self._update_display()

    def toggle_debugging(self):

        self.focused_scene.toggle_debugging()

    def warning(self, i_dont_know):

        # TODO : show the warning on screen
        raise PermissionError("Not implemented")
