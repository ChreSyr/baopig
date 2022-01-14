

class NumEntry(Entry):
    """
    A NumEntry is an Entry who only accepts numbers
    It can accept a defined range of numbers
    """

    def __init__(self, parent, min=None, max=None, accepted_numbers=None, accept_negatives=True, *args, **kwargs):

        Entry.__init__(self, parent, *args, **kwargs)

        self._min = min
        self._max = max
        self._accepted_numbers = accepted_numbers
        self._accept_negatives = bool(accept_negatives)

    def accept(self, text):


