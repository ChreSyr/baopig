
import time

from baopig.communicative import Communicative
from .utilities import present_time


class Stopwatch(Communicative):
    """
    A Stopwatch has the following signals :
        - START : emitted when the stopwatch starts
        - STOP : emitted when the stopwatch stops
        - RESET : emmitted when the stopwatch is reset
    """

    def __init__(self):

        Communicative.__init__(self)

        self._start_time = None
        self._stop_time = None

        self.create_signal("START")
        self.create_signal("STOP")
        self.create_signal("RESET")

    def __str__(self):

        return present_time(self.get_time())

    is_running = property(lambda self: self in _running_stopwatches)

    def get_time(self):
        """
        Return the current stopwatch time
        :return:
        """
        if self._start_time is None:
            return 0
        if self._stop_time is None:
            return time.time() - self._start_time
        return self._stop_time - self._start_time

    def reset(self):
        """
        Resets the stopwatch
        Only if the stopwatch is stopped
        """
        if self.is_running:
            raise PermissionError("You must stop a stopwatch before reset")
        if self.get_time() == 0:
            raise PermissionError("The stopwatch is already reset")

        self._start_time = None
        self._stop_time = None
        self.signal.RESET.emit()

    def start(self):
        """
        Starts the stopwatch
        A stopwatch can only be started if stopped
        """
        if _running_stopwatches.manager is None:
            raise PermissionError("Must launch an Application before starting a Stopwatch")
        if self.is_running:
            raise PermissionError("The stopwatch has already stared")

        if self._start_time is None:
            self._start_time = time.time()
        else:
            self._start_time = time.time() - self.get_time()
            self._stop_time = None
        _running_stopwatches.add(self)
        self.signal.START.emit()

    def stop(self):
        """
        Stops the stopwatch at current time
        """
        if not self.is_running:
            raise PermissionError("The stopwatch is not running")

        self._stop_time = time.time()
        _running_stopwatches.remove(self)
        self.signal.STOP.emit()


class _RunningStopwatches(set):
    pass


_running_stopwatches = _RunningStopwatches()
_running_stopwatches.manager = None
