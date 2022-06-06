

import sys
import os
import time
import threading
import pygame
from baopig.pybao.objectutilities import PrefilledFunction, History, TypedList, Object
from baopig._debug import infinite_fps, debug_global_fps
from baopig.time.timer import RepeatingTimer
from baopig._lib import paint_lock
from .thread import ExtraThread, LOGGER


class DrawingThread(ExtraThread):  # TODO : rename as _PainterThread

    def __init__(self, app):

        ExtraThread.__init__(self, app)

        basename = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        self.out_directory = os.path.abspath("out") + os.path.sep + basename + os.path.sep
        self._is_recording = False
        self.record_index = 1

        self._required_fps = None

        # TODO : debug_global_fps (it is a little consuming)
        if debug_global_fps:
            def _tick_fps():
                # being a deque, it manages its data itself
                self.fps_history.append(self.scenes_rendered_during_current_second)
                self.scenes_rendered_during_current_second = 0
            self.scenes_rendered_during_current_second = 0
            self.fps_history = History(int, seq=[], maxlen=500)
            self.fps_history_updater = RepeatingTimer(1, _tick_fps)

        # The clock is the object who freeze enough the thread in order to have maximum app.required_fps FPS
        self.clock = pygame.time.Clock()
        self._can_draw = threading.Event()

    def __del__(self):

        if debug_global_fps:
            self.fps_history_updater.cancel()

    executable_requests = property(lambda self: self._executable_requests)
    is_recording = property(lambda self: self._is_recording)
    required_fps = property(lambda self: self._required_fps)

    def _paint(self):

        # Updating then drawing
        with paint_lock:
            try:
                self.app.focused_scene.container_paint()
            except Exception as e:
                LOGGER.exception(e)

        # FPS Tracer
        """if self.fps_label.is_visible:
            for i, required_fps in enumerate(self.fps_history):
                color = 127
                pygame.draw.line(self.display,
                                 (color, color, color),
                                 (i + 10, self.rect.bottom - 10),
                                 (i + 10, self.rect.bottom - 10 - required_fps * 10))"""

    def get_current_fps(self):
        """

        :return:
        """
        if debug_global_fps:
            if len(self.fps_history) > 0:
                return self.fps_history[-1]
            else:
                return None
        else:
            return self.clock.get_fps()

    def init(self):

        if debug_global_fps:
            self.fps_history_updater.start()

    def screenshot(self):

        os.makedirs(self.out_directory, exist_ok=True)
        screenshot = self.app.display.copy()
        name = time.strftime("%Y.%m.%d-%Hh%M-%S.png", time.localtime())
        print(self.out_directory + name)
        pygame.image.save(screenshot, self.out_directory + name)

    def send_request(self, request):
        """
        Method for objects who need that an action is operated by the main thread

        request is a callable object
        """
        # TODO : remove
        assert callable(request), "A callable is required, got {} instead".format(request)

        self.executable_requests.append(request)

    def set_fps(self, fps):

        assert isinstance(fps, int) and fps > 0
        self._required_fps = fps

    def stop(self):

        super().stop()
        if debug_global_fps:
            self.fps_history_updater.cancel()

    def start_recording(self, only_at_change=False):

        os.makedirs(self.out_directory, exist_ok=True)
        self._is_recording = Object(only_at_change=only_at_change)
        LOGGER.info("Start recording" + (" (only at display updates)" if only_at_change else ""))

    def stop_recording(self):

        self._is_recording = False
        LOGGER.info("Stop recording")

    def update(self):

        self._can_draw.wait()

        try:

            # Threads communication
            # for executable_request in self.executable_requests:
            #     executable_request()
            # self.executable_requests.clear()

            # Drawings
            # TODO : render the display only if at least one run in Application is done
            self._paint()

            # launch time
            if self.app.launch_time is not None:
                import time
                LOGGER.info("{} launched in {} seconds".format(self.app.name, time.time() - self.app.launch_time))
                self.app.launch_time = None

            # record
            if self.is_recording:
                if not self.is_recording.only_at_change:
                    pygame.image.save(self.app.display, self.out_directory + "record_{:0>3}.png".format(self.record_index))
                    self.record_index += 1

            # FPS
            if debug_global_fps:
                self.scenes_rendered_during_current_second += 1
            # NOTE : Pour mieux tester les FPS, on ne fait pas ticker l'horloge
            if infinite_fps is False:
                self.clock.tick(self.required_fps)  # keep the game running slower than the given FPS
            else:
                self.clock.tick(0)
            if self.app._debug_fps:
                pygame.display.set_caption(f"fps : {int(self.clock.get_fps()*100)/100}")
            self._can_draw.clear()

        except pygame.error as e:
            # print(e.__str__())
            if e.__str__() == "video system not initialized":
                self.stop()
                LOGGER.error("The window have been closed")
            else:
                raise e
