

from .entry import Entry, LOGGER


class NumEntry(Entry):
    """
    A NumEntry is an Entry who only accepts numbers
    It can accept a defined range of numbers
    """
    # TODO : work on it, right now it's awful
    # TODO : Writing a long number va faire une retour à la ligne
    STYLE = Entry.STYLE.substyle()
    STYLE.modify(
        width=40
    )

    def __init__(self, parent, minval=None, maxval=None, default=None,
                 accept_floats=True, *args, **kwargs):

        entry_type = float if accept_floats else int
        Entry.__init__(self, parent, entry_type=entry_type, *args, **kwargs)

        self._minval = minval
        self._maxval = maxval
        self._accepted_numbers = None  # TODO : use or remove ?
        if default is not None:
            assert self.accept(default)
            self.set_text(str(default))

    def accept(self, text):

        try:
            value = self._entry_type(text)
        except ValueError as e:
            LOGGER.warning(e)
            return False

        if self._minval and value < self._minval:
            LOGGER.warning("Wrong value : {}, the minimum value is {}".format(value, self._minval))
            return False

        if self._maxval and value > self._maxval:
            LOGGER.warning("Wrong value : {}, the maximum value is {}".format(value, self._maxval))
            return False

        if self._accepted_numbers and value not in self._accepted_numbers:
            LOGGER.warning("Wrong value : {}, must be one of {}".format(value, self._accepted_numbers))
            return False

        return True
