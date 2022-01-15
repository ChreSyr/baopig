

import functools
from baopig.communicative import ApplicationExit, Communicative
from .widget import Widget


def decorator_start_running(widget, start_running):
    functools.wraps(start_running)
    def wrapped_func(*args, **kwargs):
        if widget.is_running is True: return
        _runables_manager.start_running(widget)
        widget._is_running = True
        res = start_running(*args, **kwargs)
        widget.signal.START_RUNNING.emit()
        return res
    return wrapped_func

def decorator_pause(widget, pause):
    functools.wraps(pause)
    def wrapped_func(*args, **kwargs):
        if widget.is_running is False: raise PermissionError("Cannot pause a Runable who didn't start yet")
        if widget.is_paused is True: return
        _runables_manager.pause(widget)
        widget._is_running = False
        widget._is_paused = True
        res = pause(*args, **kwargs)
        widget.signal.PAUSE.emit()
        return res
    return wrapped_func

def decorator_resume(widget, resume):
    functools.wraps(resume)
    def wrapped_func(*args, **kwargs):
        if widget.is_paused is False: raise PermissionError("Cannot resume a Runable who isn't paused")
        _runables_manager.resume(widget)
        widget._is_running = True
        widget._is_paused = False
        res = resume(*args, **kwargs)
        widget.signal.RESUME.emit()
        return res
    return wrapped_func

def decorator_stop_running(widget, stop_running):
    functools.wraps(stop_running)
    def wrapped_func(*args, **kwargs):
        if widget.is_paused is True: widget.resume()
        if widget.is_running is False: return
        _runables_manager.stop_running(widget)
        widget._is_running = False
        res = stop_running(*args, **kwargs)
        widget.signal.STOP_RUNNING.emit()
        return res
    return wrapped_func


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

    # TODO : application.runables instead of parent.children.runables, don't depend on Widget
    # -> if widget, sleeping will not run
    def __init__(self, start=False):

        _runables_manager.add(self)

        if not hasattr(self, "signal"):  # if Communicative.__init__(self) haven't been called elsewhere
            Communicative.__init__(self)

        self.start_running = decorator_start_running(self, self.start_running)
        self.pause = decorator_pause(self, self.pause)
        self.resume = decorator_resume(self, self.resume)
        self.stop_running = decorator_stop_running(self, self.stop_running)

        self._is_running = False
        self._is_paused = False

        self.create_signal("START_RUNNING")
        self.create_signal("PAUSE")
        self.create_signal("RESUME")
        self.create_signal("STOP_RUNNING")

        if isinstance(self, Widget):
        # if hasattr(self, "_dirty") and hasattr(self, "_is_sleeping"):  # if sub-classed by a Widget
            self.connect("pause", self.signal.ASLEEP)
            self.connect("resume", self.signal.WAKE)
            self.signal.KILL.connect(lambda: _runables_manager.remove(self))

        if start:
            self.start_running()

    is_paused = property(lambda self: self._is_paused)
    is_running = property(lambda self: self._is_running)

    def run(self):
        """Stuff to do when the object is running"""

    def pause(self):
        """Stuff to do when the object is paused"""

    def resume(self):
        """Stuff to do when the object resume"""

    def start_running(self):
        """Stuff to do when the object starts to run"""

    def stop_running(self):
        """Stuff to do when the object stops to run"""
