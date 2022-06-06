#!/usr/bin/env python
# -*- coding: utf-8 -*-

## BiblioButton is expressively dedicated to BiblioApplication
# TODO : remove all assertion with debug_with_assert

import time

import pygame
from baopig.pybao import WeakTypedList
from baopig._debug import debug_global_fps
from baopig.io import LOGGER, mouse, keyboard
from .style import HasStyle, Theme, StyleClass
from .widget import Widget, paint_lock
from .runable import _runables_manager
from .utilities import *
from .scene import Scene
from baopig.io import clipboard


class Application(HasStyle):
    """
    This is the main class in baopig
    It needs to be instanced before everything else
    """
    STYLE = StyleClass()

    def __init__(self, name=None, theme=None, size=None, mode=pygame.RESIZABLE):

        if name is None: name = self.__class__.__name__
        if theme is None: theme = Theme()
        HasStyle.__init__(self, theme)

        pygame.init()
        info = pygame.display.Info()

        self._name = name
        self._is_launched = False
        self._is_running = False
        self._fps = 50
        self._debug_fps = False
        self._default_mode = mode
        self._default_size = pygame.display.list_modes()[-1] if size is None else size
        self._current_mode = self._current_size = None
        self._max_resolution = (info.current_w, info.current_h)
        self._is_fullscreen_TO_REMOVE = False
        self._scenes = WeakTypedList(Scene)
        self._focused_scene = None
        self._caption = "baopig application"
        self._painter = None  # To be set in self.launch()
        self._time_manager = None  # To be set in self.launch()
        self._runables_manager = _runables_manager

        self.launch_time = time.time()

        mouse._application = self
        keyboard._application = self

        pygame.display.set_caption(self.name)

    default_mode = property(lambda self: self._default_mode)
    default_size = property(lambda self: self._default_size)
    display = property(lambda self: self._focused_scene._surface)
    focused_scene = property(lambda self: self._focused_scene)
    fps = property(lambda self: self._fps)
    is_fullscreen = property(lambda self: bool(self.default_mode & pygame.FULLSCREEN))
    is_launched = property(lambda self: self._is_launched)
    is_running = property(lambda self: self._is_running)
    max_resolution = property(lambda self: self._max_resolution)
    name = property(lambda self: self._name)
    painter = property(lambda self: self._painter)
    scenes = property(lambda self: self._scenes)
    size = property(lambda self: self._focused_scene.size)

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
                    self.exit("pressed F6")
            elif event.type == pygame.QUIT:
                self.exit("pygame.QUIT")

            elif event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                mouse.receive(event)
            elif event.type in (pygame.KEYDOWN, pygame.KEYUP):
                keyboard.receive(event)
            elif event.type == pygame.ACTIVEEVENT:
                continue
                """
                state : 1 -> focused
                        2 -> just clicked on application icon while iconified, focused, gain = 1
                        3 -> other application is focsed
                        4 -> just iconified tha application
                """
                if event.state == 2:
                    self.refresh()
                else:
                    if event.gain:
                        mouse._hover_display()
                    else:
                        mouse._unhover_display()
            # elif event.type == pygame.VIDEOEXPOSE:
            #     LOGGER.warning("VIDEOEXPOSE", event)
            elif event.type == pygame.VIDEORESIZE:
                if event.size != self.focused_scene.size:
                    self.focused_scene.resize(*event.size)
                else:
                    # We need and update
                    self.focused_scene.paint()

            # DEFAULT SHORTKEYS
            if event.type == pygame.KEYDOWN:
                if keyboard.mod.ctrl:
                    # Cmd + e -> toggle debugging
                    if event.key == pygame.K_e:  # pour debugger dans l'application
                        if keyboard.mod.maj:
                            c = self.focused_scene.children
                            raise AssertionError("Made for debugging")
                        self.toggle_debugging()
                    # Cmd + f -> toggle debug fps
                    elif event.key is keyboard.f:
                        self._debug_fps = not self._debug_fps
                        if not self._debug_fps:
                            self.set_caption(self._caption)
                    # Cmd + g -> collect garbage
                    elif event.key == pygame.K_g:
                        import gc
                        gc.collect()
                        LOGGER.info("Garbage collected")
                    # Cmd + n -> swap to the next scene
                    elif event.key == pygame.K_n:  # TODO : rewrite (-> menu bar ? one day ?)
                        # NOTE : resizing the application will release all pressed keys
                        index = self.scenes.index(self.focused_scene)
                        index = (index + 1) % len(self.scenes)
                        self.open(self.scenes[index])
                    # Cmd + u -> application freeze
                    elif event.key == keyboard.u:
                        def u_is_pressed():
                            for event in pygame.event.get():
                                if event.type is keyboard.KEYDOWN:
                                    if event.key is keyboard.F6:
                                        self.exit("Pressed F6")
                                    elif event.key is keyboard.u:
                                        return True
                                    elif event.key is keyboard.ESCAPE:  # quit fullscreen or exit
                                        if self.is_fullscreen:
                                            self.exit_fullscreen()
                                        else:
                                            self.exit("pressed ESCAPE")
                                    elif event.key is keyboard.F5:  # fullscreen
                                        self.focused_scene.toggle_fullscreen()
                                    elif event.key is keyboard.F4:  # minimize
                                        self.iconify()
                                    elif event.key is keyboard.F3:  # refresh
                                        self.refresh()
                                        LOGGER.info("Display refreshed")
                                    elif event.key is keyboard.F2:  # screenshot TODO : A faire avec un clic droit
                                        self.painter.screenshot()
                                        LOGGER.info("Screenchot !")
                            return False
                        self.freeze(until=u_is_pressed)
                    # Cmd + r -> toggle recording (if Maj: save application.surface only when it changes)
                    elif event.key == pygame.K_r:
                        if self.painter.is_recording:
                            self.painter.stop_recording()
                        else:
                            self.painter.start_recording(only_at_change=self.mod.maj)

                elif keyboard.mod.alt:
                    pass  # Nothing implemented

                elif event.key == pygame.K_ESCAPE:  # quit fullscreen or exit
                    if self.is_fullscreen:
                        self.set_display_mode(self.default_mode - pygame.FULLSCREEN)
                    else:
                        self.exit("pressed ESCAPE")
                elif event.key == pygame.K_F5:  # fullscreen
                    self.focused_scene.toggle_fullscreen()
                elif event.key == pygame.K_F4:  # minimize
                    self.iconify()
                elif event.key == pygame.K_F3:  # refresh
                    self.refresh()
                    LOGGER.info("Display refreshed")
                elif event.key == pygame.K_F2:  # screenshot TODO : A faire avec un clic droit
                    self.painter.screenshot()
                    LOGGER.info("Screenchot !")

            # TRANSMITTING EVENT
            if event.type in (pygame.KEYDOWN, pygame.KEYUP) and self.focused_scene.focused_comp is not None:
                if event.type == pygame.KEYDOWN:
                    self.focused_scene.focused_comp.signal.KEYDOWN.emit(event.key)
                else:
                    self.focused_scene.focused_comp.signal.KEYUP.emit(event.key)

            # Events optionnal treatment
            if self.focused_scene.is_enabled:
                self.focused_scene.receive(event)

    def _run(self):
        """
        Launch the application
        """

        try:

            self._is_running = True

            while self.is_running:

                # User events
                self._manage_events()

                # Possible advanced events treatments
                self._time_manager.update()
                self._runables_manager.run_once()

                # Possible coded stuff
                self.focused_scene.run()

                # If needed, drawing display
                if pygame.display.get_active():
                    self.painter._can_draw.set()

        except Exception as e:
            if isinstance(e, ApplicationExit):
                if str(e) == 'None':
                    LOGGER.info(f"{self.__class__.__name__} exit")
                else:
                    LOGGER.info("{} exit : '{}'".format(self.__class__.__name__, e))
            else:
                raise e

        if debug_global_fps:
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

        if self.is_launched:  # TODO : remove condition ?

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

            if debug_with_assert: assert pygame.display.get_surface() is self.focused_scene.surface

            if size != self._current_size:
                LOGGER.fine(f"Display size set to {size}")

            self._current_mode = mode
            self._current_size = size

    def exit(self, reason=None):

        self._is_running = False
        with paint_lock:
            self.painter.stop()

            # If the program launch the app again
            # self._is_launched = False
            # self._current_size = self._current_mode = None
            # NOTE : after some tests, a pygame error makes it impossible to restart a closed application
            # If you make it work, be sure to remove the following line
            # application_keeper[0] = None

            raise ApplicationExit(reason)

    def flash(self):
        """
        Create a short flash on the application
        Can be used when an error occurs, like a wrong user input
        """
        pass  # TODO : implemented this functionnality

    def freeze(self, until):  # TODO : until
        """Freeze the application until 'freeze' function returns True"""

        assert callable(until)

        with paint_lock:
            self.painter._can_draw.clear()
            self._time_manager.pause()
            mouse._release_all()
            keyboard._release_all()
            while not until(): pass
            mouse.update_hovered_comp()
            self._time_manager.resume()
            self.painter._can_draw.set()

    def iconify(self):

        with paint_lock:
            # if self.is_fullscreen:
            #     self.exit_fullscreen()  # TODO : test it
            pygame.display.iconify()

    def launch(self):

        assert not self.is_launched and pygame.get_init(), \
            "An application can only be launched once, due to pygame restrictions"
        self._is_launched = True

        from baopig.time.timemanager import time_manager
        self._time_manager = time_manager
        from baopig.threads import DrawingThread
        self._painter = DrawingThread(self)
        self.painter.set_fps(self._fps)

        events = pygame.event.get()
        mouse._pos = pygame.mouse.get_pos()
        mouse_is_hovering_application = True
        for event in events:
        # On ne prends pas compte des evenements qui ont eu lieu pendant le chargement de l'application
            if event.type == pygame.ACTIVEEVENT and event.gain == 0:
                mouse_is_hovering_application = False

        if len(self.scenes) == 0:
            from baopig.prefabs.presentationscene import PresentationScene
            PresentationScene(self)

        assert self.focused_scene is not None
        scene = self.focused_scene
        self._focused_scene = None
        scene.open()
        assert self.focused_scene is scene
        self.painter.start()

        if mouse_is_hovering_application:
            mouse._hover_display()
        # TODO : solve proper hovering display (is it a pygame error ?)

        self._run()

    def open(self, scene):

        if isinstance(scene, str):
            for s in self.scenes:
                if s.name == scene:
                    scene = s
                    break
        if not scene in self.scenes:
            raise PermissionError(f"Unknown scene : '{scene}' "
                                  f"(existing scenes : {tuple(str(s) for s in self.scenes)})")

        scene.open()

    def refresh(self):
        """
        Send an paintrequest to every containers in focused_scene
        if only_containers is False, send an paintrequest to every focused_scene's components
        """
        self.focused_scene.paint(recursive=True, only_containers=False)

    def set_caption(self, title, icontitle=""):

        self._caption = title
        pygame.display.set_caption(title, icontitle)

    def set_default_size(self, size):  # TODO : resize ?

        if size == self.default_size: return
        self._default_size = size
        for scene in self.scenes:
            if scene.asked_size is not None:
                scene.resize(*self.default_size)

    def set_fps(self, fps):

        self._fps = fps
        if self.painter is not None:
            self.painter.set_fps(fps)

    def set_icon(self, icon):

        pygame.display.set_icon(icon)

    def set_display_mode(self, mode):

        if mode is self.default_mode: return

        assert mode in (0, pygame.NOFRAME, pygame.RESIZABLE, pygame.FULLSCREEN)

        # if mode is pygame.FULLSCREEN and self.mode != mode:
          #   self._mode_before_fullscreen = self.focused_scene.mode
            # self._size_before_fullscreen = self.asked_size

            # mode = 0

        self._default_mode = mode
        self._update_display()

    def toggle_debugging(self):

        self.focused_scene.toggle_debugging()

    def warning(self, I_dont_know):

        # TODO : show the warning on screen
        raise PermissionError("Not implemented")

