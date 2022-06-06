

import inspect
from baopig.pybao.objectutilities import PackedFunctions, Object, TypedSet
from baopig.io.logging import LOGGER


class ApplicationExit(Exception):
    pass


class Signal:

    def __init__(self, emitter, id, catching_errors):

        assert isinstance(emitter, Communicative), emitter
        assert isinstance(id, str) and (id == id.upper()), id

        self._emitter = emitter
        self._id = id
        self._connections = []
        self._catching_errors = catching_errors
        self.emit = self.emit_with_catch if catching_errors else self.emit_no_catch

    def __str__(self):

        return f"Signal(id={self._id}, emitter={self._emitter})"

    def connect(self, command, owner=None, **options):  # TODO : rename as connect
        """
        Connect the command to the signal
        When self will emits 'signal', the owner's method 'command' will be executed
        if option 'need_arguments' is False, the emitted argumaents will be ignored
        :param command: a method of owner
        :param owner: an Communicative object
        NOTE : The "owner" parameter is very important when it comes to deletion
               When the owner is deleted, this connection is automatically killed
        """
        if not callable(command):
            raise TypeError("'{}' object is not callable".format(command))
        for con in self._connections:
            if con.slot is command:
                return
                raise PermissionError(f"{command} already connected to {self}")
        Connection(owner, self, command, **options)

    def disconnect(self, listener):
        """
        Remove all connections from this signal to the listener
        """
        for con in tuple(self._connections):
            if con.owner is listener:
                con.kill()

    def emit_with_catch(self, *args):
        """
        Emitting a signal will execute all its connected commands
        If an error occurs while executing a command, it will be logged
        The error ApplicationExit is not catched
        """

        for con in self._connections:
            try:
                con.transmit(*args) if args else con.slot()  # little optimization ?
            except ApplicationExit as e:
                raise e
            except Exception as e:
                LOGGER.warning("Error : {} -- while exectuting {}".format(e, con))

    def emit_no_catch(self, *args, catching_errors=None):
        """
        Emitting a signal will execute all its connected commands
        If an error occurs while executing a command, it will be raised
        """
        for con in self._connections:
            con.transmit(*args) if args else con.slot()  # little optimization TODO : signal.transmit_arguments

    def rem_command(self, command):

        for con in tuple(self._connections):
            if con.slot is command:
                con.kill()

    def set_catching_errors(self, catching_errors):

        self._catching_errors = bool(catching_errors)
        self.emit = self.emit_with_catch if catching_errors else self.emit_no_catch


class Signals(Object): pass


class Connection:

    def __init__(self, owner, signal, slot, **options):

        need_arguments = False
        if len(inspect.signature(slot).parameters) > 0:
            need_arguments = True
        if "need_arguments" in options:
            need_arguments = options.pop("need_arguments")

        self.owner = owner
        self.signal = signal
        self.slot = slot
        self.transmit = slot if need_arguments else lambda *args: slot()

        signal._connections.append(self)
        if owner is not None:
            owner._connections.add(self)

    def kill(self):

        self.signal._connections.remove(self)
        self.owner._connections.remove(self)


class Communicative:

    def __init__(self):

        self.signal = Signals()
        self._connections = TypedSet(Connection)

    def connect(self, method_name, signal, **options):
        """
        Connect the method called 'method_name' to the signal
        When the 'signal' will be emited, the self's method 'method_name' will be executed
        :param signal: a Signal
        :param method_name: a string representing a method of self
        """
        method = getattr(self, method_name)
        # if not inspect.ismethod(method):  # can be a decorator
        #     raise ValueError("The method_name must be a string representing a method of '{}' object"
        #                      "".format(self.__class__.__name__))
        assert isinstance(signal, Signal), signal

        signal.connect(method, owner=self, **options)

    def create_signal(self, signal_id, catching_errors=False):  # TODO : change catching_errors for testing
        # TODO : rename signal_id as name

        if not isinstance(signal_id, str) or not (signal_id == signal_id.upper()):
            raise PermissionError("A signal id must be an uppercase str")
        if hasattr(self.signal, signal_id):
            raise PermissionError("A signal already has this id : {}".format(signal_id))

        setattr(self.signal, signal_id, Signal(emitter=self, id=signal_id, catching_errors=catching_errors))

    def disconnect(self, *, signal=None, emitter=None, command=None):
        """
        Remove connections from any signal to commands owned by self
        :param signal: if set, only remove connections from this signal to commands owned by self
        :param emitter: if set, only remove connections from this emitter to commands owned by self
        """
        if signal is not None:
            signal.disconnect(self)
        elif emitter is not None:
            for signal in emitter.signal.__dict__.values():
                signal.disconnect(self)
        elif command is not None:
            for signal in self.signal:
                signal.rem_command(command)
        else:
            for con in tuple(self._connections):
                con.kill()
