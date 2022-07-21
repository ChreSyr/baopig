import time
from baopig.time.stopwatch import _running_stopwatches
from baopig.time.timer import _running_timers, timer_lock, RepeatingTimer


# TODO : baopig.time.init() for chifoumi__server


class _TimeManager:

    def __init__(self):

        self._paused_timers = None
        self._paused_stopwatches = None

    """def pause_TBR(self):

        if self._paused_timers is not None:
            raise PermissionError("The TimeThread is already paused")

        self._paused_timers = tuple(_running_timers)
        for timer in self._paused_timers:
            timer.pause()
        self._paused_stopwatches = tuple(_running_stopwatches)
        for stopwatch in self._paused_stopwatches:
            stopwatch.stop()
        self._is_paused = True

    def resume_TBR(self):

        if self._paused_timers is None:
            raise PermissionError("The TimeThread is already running")

        for timer in self._paused_timers:
            timer.resume()
        self._paused_timers = None
        for stopwatch in self._paused_stopwatches:
            stopwatch.start()
        self._paused_stopwatches = None"""

    @staticmethod
    def update():

        current_time = time.time()

        with timer_lock:
            for timer in tuple(_running_timers):

                if timer._end_time is None:  # happens when timer.TIMEOUT provokes another_timer.cancel()
                    continue

                if timer._end_time <= current_time:
                    if isinstance(timer, RepeatingTimer):
                        timer._repeat()
                    else:
                        _running_timers.remove(timer)
                    timer.signal.TIMEOUT.emit()


time_manager = _TimeManager()
_running_timers.manager = time_manager
_running_stopwatches.manager = time_manager
del _TimeManager
