

from .entry import Entry, LOGGER, Validable


class NumEntry(Entry):
    """
    A NumEntry is an Entry who only accepts numbers
    It can accept a defined range of numbers
    """
    # TODO : work on it, right now it's awful
    # TODO : Writing a long number va faire une retour à la ligne
    STYLE = Entry.STYLE.substyle()
    STYLE.modify(
        width = 40
    )

    def __init__(self, parent, min=None, max=None, default=None,
                 accept_floats=True, *args, **kwargs):

        type = float if accept_floats else int
        Entry.__init__(self, parent, entry_type=type, *args, **kwargs)

        self._min = min
        self._max = max
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

        if self._min and value < self._min:
            LOGGER.warning("Wrong value : {}, the minimum value is {}".format(value, self._min))
            return False

        if self._max and value > self._max:
            LOGGER.warning("Wrong value : {}, the maximum value is {}".format(value, self._max))
            return False

        if self._accepted_numbers and value not in self._accepted_numbers:
            LOGGER.warning("Wrong value : {}, must be one of {}".format(value, self._accepted_numbers))
            return False

        return True
