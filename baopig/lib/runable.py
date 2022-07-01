import functools
from baopig.communicative import Communicative
from .widget import Widget


# TODO : merge _RunablesManager & _TimeManager
# TODO : baopig.time.init() for chifoumi__server


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
        assert not runable in self._running
        assert not runable in self._paused
        self._running.add(runable)

    def stop_running(self, runable):

        assert runable in self._running
        self._running.remove(runable)

    def run_once(self):

        for runable in self._running:
            runable.run()


_runables_manager = _RunablesManager()
del _RunablesManager


class Runable(Communicative):
    """
    A Runable is a Communicative object with 4 signals:
        - START_RUNNING
        - PAUSE
        - RESUME
        - STOP_RUNNING
    Its 'run' method is called at each application loop
    """

    def __init__(self, start=False):

        _runables_manager.add(self)

        if not hasattr(self, "signal"):  # if Communicative.__init__(self) haven't been called elsewhere
            Communicative.__init__(self)

        self._is_running = False
        self._is_paused = False

        self.create_signal("START_RUNNING")
        self.create_signal("PAUSE")
        self.create_signal("RESUME")
        self.create_signal("STOP_RUNNING")

        if isinstance(self, Widget):
            self.signal.ASLEEP.connect(self.pause, owner=self)
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
        self.signal.PAUSE.emit()

    def handle_pause(self):
        """Stuff to do when the object is paused"""

    def resume(self):

        if self.is_paused is False:
            raise PermissionError("Cannot resume a Runable who isn't paused")

        _runables_manager.resume(self)
        self._is_running = True
        self._is_paused = False
        self.handle_resume()
        self.signal.RESUME.emit()

    def handle_resume(self):
        """Stuff to do when the object resume"""

    def start_running(self):

        if self.is_running is True:
            return

        _runables_manager.start_running(self)
        self._is_running = True
        self.handle_startrunning()
        self.signal.START_RUNNING.emit()

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
        self.signal.STOP_RUNNING.emit()

    def handle_stoprunning(self):
        """Stuff to do when the object stops to run"""
