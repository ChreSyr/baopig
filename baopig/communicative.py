

import inspect
from baopig.pybao.objectutilities import Object
from baopig.io.logging import LOGGER
from .documentation import ApplicationExit
from .documentation import Communicative as CommunicativeDoc


class Signal:

    def __init__(self, emitter, id):

        assert isinstance(emitter, Communicative), emitter
        assert isinstance(id, str) and (id == id.upper()), id

        self._emitter = emitter
        self._id = id
        self._connections = []

    def __str__(self):

        return f"Signal(id={self._id}, emitter={self._emitter})"

    def connect(self, command, owner):
        """
        Connect the command to the signal
        When self will emit 'signal', the owner's method 'command' will be executed
        :param command: a method of owner
        :param owner: a Communicative object
        NOTE : The "owner" parameter is very important when it comes to deletion
               When the owner is deleted, this connection is automatically killed
        """
        if not callable(command):
            raise TypeError(f"'{command}' object is not callable")
        for con in self._connections:
            if con.slot is command:
                raise PermissionError(f"This command is already connected to the signal {self._id}")

        conn = Connection(owner, self, command)
        self._connections.append(conn)
        if owner is not None:
            owner._connections.add(conn)

    def disconnect(self, command):

        for con in tuple(self._connections):
            if con.slot == command:
                con.kill()
                return
        raise ValueError(f"This command is not connected to the signal {self._id}")

    def emit(self, *args):
        """
        Emitting a signal will execute all its connected commands
        If an error occurs while executing a command, it will be raised
        """
        for con in self._connections:
            if con.need_arguments:
                con.slot(*args)
            else:
                con.slot()

    def emit_with_catch(self, *args):
        """
        Emitting a signal will execute all its connected commands
        If an error occurs while executing a command, it will be logged
        The error ApplicationExit is not catched
        """

        for con in self._connections:
            try:
                if con.need_arguments:
                    con.slot(*args)
                else:
                    con.slot()
            except ApplicationExit as e:
                raise e
            except Exception as e:
                LOGGER.warning(f"Error : {e} -- while exectuting {con}")


class Connection:

    def __init__(self, owner, signal, slot):

        self.owner = owner
        self.signal = signal
        self.slot = slot
        self.need_arguments = len(inspect.signature(slot).parameters) > 0

    def kill(self):

        self.signal._connections.remove(self)
        if self.owner is not None:
            self.owner._connections.remove(self)


class Communicative(CommunicativeDoc):

    def __init__(self):

        self.signal = Object()
        self._connections = set()

    def create_signal(self, signal_id):

        if not isinstance(signal_id, str) or not (signal_id == signal_id.upper()):
            raise PermissionError("A signal id must be an uppercase str")
        if hasattr(self.signal, signal_id):
            raise PermissionError("A signal already has this id : {}".format(signal_id))

        setattr(self.signal, signal_id, Signal(emitter=self, id=signal_id))

    def disconnect(self):

        for con in tuple(self._connections):
            con.kill()
