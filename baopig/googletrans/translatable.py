import baopig as bp
from .extension import lang_manager


class Translatable(bp.Widget):

    def __init__(self, parent, text_id=None, **kwargs):
        bp.Widget.__init__(self, parent, **kwargs)

        self.text_id = text_id
        lang_manager.set_ref_text(self, text_id)

        def handle_kill():
            lang_manager.remove_widget(self)

        self.signal.KILL.connect(handle_kill, owner=self)

    def fit(self):
        """ Called each time the text has been translated, and need to be ajusted """

    def set_ref_text(self, text_id):
        lang_manager.set_ref_text(self, text_id)


class TranslatableText(bp.Text, Translatable):

    def __init__(self, parent, text_id=None, **kwargs):
        bp.Text.__init__(self, parent=parent, text=lang_manager.get_text_from_id(text_id), **kwargs)
        Translatable.__init__(self, parent, text_id=text_id)


class PartiallyTranslatableText(TranslatableText):

    def __init__(self, parent, get_args: tuple, **kwargs):
        TranslatableText.__init__(self, parent, **kwargs)

        assert self.text.count("{}") == len(get_args)

        self.partial_text = self.translated_partial_text = self.text
        self.get_args = get_args

    def complete_text(self):

        inserts = tuple(lang_manager.get_text_from_id(text_id=get_arg()) for get_arg in self.get_args)
        complete_text = self.translated_partial_text.format(*inserts)
        self.set_text(complete_text)

    def set_text(self, text):
        if "{}" in text:
            self.translated_partial_text = text
            try:
                self.complete_text()
            except:  # still in construction, self.get_args is not defined
                # or a function in get_args raised an exception
                super().set_text(text)
        else:
            super().set_text(text)
