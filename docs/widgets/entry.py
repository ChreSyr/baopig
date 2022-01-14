

from baopig._lib import Validable, LOGGER
from .lineedit import LineEdit, keyboard


class Entry(LineEdit, Validable):
    """
    An Entry is a LineEdit who can be validated
    """

    def __init__(self, parent, entry_type, command=None, *args, validate_on_defocus=True, **kwargs):

        """

        :param parent:
        :param entry_type:
        :param command: function executed on validation, with self.text as parameter
        :param args:
        :param validate_on_defocus:
        :param kwargs:
        """

        LineEdit.__init__(self, parent, *args, **kwargs)
        Validable.__init__(self, catching_errors=False)

        self._entry_type = entry_type
        self.command = command

        if validate_on_defocus:
            self.connect("validate", self.signal.DEFOCUS)

    def accept(self, text):

        try:
            value = self._entry_type(text)
        except ValueError as e:
            LOGGER.warning(e)
            return False
        return True

    def handle_keydown(self, key):

        if key is keyboard.RETURN:
            if self.accept(self.text):
                self.validate()
        elif key is keyboard.TAB:
            self.focus_next()
        else:
            self.cursor.handle_keydown(key)

    def validate(self):

        if self.command is not None:
            self.command(self.text)
        self.defocus()
        return self._entry_type(self.text)