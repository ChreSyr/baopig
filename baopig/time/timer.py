

import time
import threading
from baopig.pybao.objectutilities import PrefilledFunction
from baopig.communicative import Communicative, LOGGER
from .utilities import *


class Timer(Communicative):
    """
    A Timer is an object who start at a given time called interval and then count down
    Once this time countdown is over, it emits the TIMEOUT signal
    You can connect commands to this signal trough the 'commands' parameter in constructor

    A Time has the following signals :
        - START : emitted when the timer starts
        - TIMEOUT : emitted when the countdown is over
    """
    def __init__(self, interval, command=lambda: None, *args, **kwargs):

        assert interval >= 0

        Communicative.__init__(self)

        self._interval = interval
        self._start_time = None
        self._pause_time = None
        self._end_time = None

        self.create_signal("TIMEOUT")
        self.create_signal("START")
        if args or kwargs:
            command = PrefilledFunction(command, *args, **kwargs)
        self.signal.TIMEOUT.connect(command, owner=None)

    interval = property(lambda self: self._interval)
    is_paused = property(lambda self: self._pause_time is not None)  # NOTE : a paused Timer is not running
    is_running = property(lambda self: self in _running_timers)

    def __repr__(self):

        return "Timer(interval={}, time_left={})".format(self.interval, self.get_time_left())

    def __str__(self):

        return present_time(self.get_time_left() if self.is_running else self.interval)

    def cancel(self):
        """
        Cancel the timer
        
        NOTE : It is preferable not to mess with emitting the TIMEOUT signal here.
               You can do it yourself if you know what you are doing.
        """

        if self._start_time is None:
            return

        with timer_lock:
            if self.is_running:
                _running_timers.remove(self)
            self._start_time = None
            self._pause_time = None
            self._end_time = None

    def get_time_left(self):

        if self._start_time is None:
            return 0

        if self.is_paused:
            return self.interval - (self._pause_time - self._start_time)

        return max(self._end_time - time.time(), 0)

    def pause(self):

        if not self.is_running:
            return

        with timer_lock:
            self._pause_time = time.time()
            _running_timers.remove(self)

    def resume(self):

        if self._pause_time is None:
            return

        with timer_lock:
            self._start_time = self._start_time + (time.time() - self._pause_time)
            self._end_time = self._start_time + self.interval
            self._pause_time = None
            _running_timers.add(self)

    def set_interval(self, interval):

        self._interval = interval

    def start(self):

        if self in _running_timers:
            raise PermissionError("The timer has already started")
        if _running_timers.manager is None:
            # TODO
            LOGGER.debug("Timer started before the application's launch")
            # raise PermissionError("Must launch an Application before starting a Timer")

        with timer_lock:
            self._start_time = time.time()
            self._pause_time = None
            self._end_time = self._start_time + self.interval
            _running_timers.add(self)
            self.signal.START.emit()


class RepeatingTimer(Timer):
    """
    The repeat is carried by the manager

    If you enter a tuple for 'interval' parameter, the fisrt value will be used
    for the first interval, the second one for the other intervals
    """
    def __init__(self, interval, command, *args, **kwargs):

        if isinstance(interval, (int, float)):
            first_interval = repeat_interval = interval
        else:
            first_interval = interval[0]
            repeat_interval = interval[1]

        Timer.__init__(self, first_interval, command, *args, **kwargs)

        # interval returns the start of the current countdown
        self._first_interval = first_interval
        self._repeat_interval = repeat_interval

        self.create_signal("RESTART")

    first_interval = property(lambda self: self._first_interval)
    repeat_interval = property(lambda self: self._repeat_interval)

    def _repeat(self):
        """Should only be called by the manager"""

        left = self.get_time_left()
        assert left == 0, left
        assert self._start_time is not None

        with timer_lock:
            self._interval = self._repeat_interval
            self._start_time = self._end_time
            self._end_time += self._interval
            self.signal.RESTART.emit()

    def set_interval(self, interval):

        if isinstance(interval, (int, float)):
            self._first_interval = self._repeat_interval = self._interval = interval
        else:

            if self._interval is self._first_interval:
                self._interval = interval[0]
            else:
                self._interval = interval[1]
            self._first_interval = interval[0]
            self._repeat_interval = interval[1]


class SetattrTimer(Timer):
    """Set the attribute to value after a given delay (still a Timer, must be started)"""
    def __init__(self, owner, attr, val, delay):
        assert hasattr(owner, attr)
        Timer.__init__(self, delay, setattr, owner, attr, val)


class _RunningTimers(set):
    pass


timer_lock = threading.RLock()
_running_timers = _RunningTimers()
_running_timers.manager = None
