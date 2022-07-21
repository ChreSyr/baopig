
import os
import sys
import logging
import tempfile
import time
from logging import FileHandler

formatters = [logging.Formatter("%(asctime)s :: %(threadName)s :: %(module)s :: %(funcName)s :\n"
                                "    %(levelname)s :: %(msg)s"),  # WARNING, INFO
              logging.Formatter("%(asctime)s :: %(module)s :: %(funcName)s :\n    %(levelname)s :: %(msg)s"),
              logging.Formatter("%(module)s :: %(funcName)s :: %(levelname)s :: %(msg)s"),  # DEBUG
              logging.Formatter("%(asctime)s :: %(levelname)s :: %(msg)s"),
              logging.Formatter("%(levelname)s :: %(msg)s")]  # Console


class PersonalizedLogger(logging.Logger):

    CRITICAL = logging.CRITICAL  # 50
    FATAL = logging.FATAL        # 50
    ERROR = logging.ERROR        # 40
    WARNING = logging.WARNING    # 30
    WARN = logging.WARN          # 30
    INFO = logging.INFO          # 20
    DEBUG = logging.DEBUG        # 10
    FINE = 5
    NOTSET = logging.NOTSET      # 0

    def __init__(self):
        logging.Logger.__init__(self, "LOGGER", level=logging.NOTSET)

        # File Handler
        # Will create the file activity.log in the directory /logs
        # from the directory where the application have been launched
        basename = os.path.splitext(os.path.basename(sys.argv[0]))[0]
        # self.logs_directory = os.path.abspath("logs") + os.path.sep + basename + os.path.sep
        self.logs_directory = tempfile.gettempdir() + "/logs" + os.path.sep + basename + os.path.sep
        os.makedirs(self.logs_directory, exist_ok=True)
        self.open_file_handlers = {}
        for level in (logging.WARNING, logging.INFO):
            self.add_filehandler(level)

        # Console Handler
        self.cons_handler = logging.StreamHandler()
        self.cons_handler.setFormatter(formatters[-1])
        self.cons_handler.setLevel(logging.INFO)
        self.addHandler(self.cons_handler)

        # Done
        self.debug("File and Console logging successfully initialised")

    def add_filehandler(self, level):
        """
        Add to self.handlers a new FileHandler
        His level is set with the argument 'level'
        :param level: a logging existing level
        :return: None
        """
        assert isinstance(level, int), "level must be an integer"

        level_name = logging.getLevelName(level)
        filename = self.logs_directory + level_name + ".log"
        file = open(filename, 'w')
        file.write("\n-------------------------------------------------------------")
        file.write("\n                LOG FILE")
        file.write("\n            {}".format(time.strftime("%b %d, %Y at %H:%M and %S seconds", time.localtime())))
        file.write("\n            File log level:{}".format(level_name))
        file.write("\n            Executing script:{}".format(sys.argv[0]))
        file.write("\n-------------------------------------------------------------\n\n")
        file.close()
        file_handler = FileHandler(filename)
        file_handler.setLevel(level)
        if level != logging.DEBUG:
            file_handler.setFormatter(formatters[0])
        if level == logging.DEBUG:
            file_handler.setFormatter(formatters[2])
        self.addHandler(file_handler)
        self.open_file_handlers[level] = (1, file_handler)

    def add_debug_filehandler(self):
        if logging.DEBUG not in self.open_file_handlers:
            self.add_filehandler(logging.DEBUG)

    def fine(self, msg, *args, **kwargs):
        """
        Log 'msg % args' with severity 'FINE'.

        To pass exception information, use the keyword argument exc_info with
        a true value, e.g.

        logger.fine("Houston, we have a %s", "interesting problem", exc_info=1)
        """
        if self.isEnabledFor(self.FINE):
            self._log(self.FINE, msg, args, **kwargs)


LOGGER = PersonalizedLogger()
# logging.addLevelName(LOGGER.FINE, "FINE")
