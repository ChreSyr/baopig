
import threading
from baopig.io import LOGGER


class ExtraThread(threading.Thread):

    def __init__(self, app):

        threading.Thread.__init__(self, name=self.__class__.__name__, daemon=True)

        self._application = app
        self._stop_event = threading.Event()
        self._stop_event.set()

    def __str__(self):

        return self.name

    app = property(lambda self: self._application)
    is_running = property(lambda self: not self._stop_event.is_set())
    is_stopped = property(lambda self: self._stop_event.is_set())

    def init(self):
        """
        Called when the thread restart
        """

    def run(self):

        while True:

            assert self.is_alive()
            if self.is_running:

                LOGGER.debug("Start to run thread : {}".format(self))
                self.init()

                while self.is_running:

                    try:
                        self.update()
                    except Exception as e:
                        LOGGER.exception("Exception on {} :  {}".format(self, e))

                LOGGER.debug("Stop to run thread : {}".format(self))

    def start(self):

        threading.Thread.start(self)
        self._stop_event.clear()

    def stop(self):

        self._stop_event.set()
        self.update = lambda: None

    def update(self):
        """
        Called as much as possible while the thread is running
        """
