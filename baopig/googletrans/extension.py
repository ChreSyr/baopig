import os
import sys
import importlib
from httpcore import ConnectError
import baopig as bp
from .client import Translator


class Dictionnary(dict):

    def __init__(self, lang_id):

        dict.__init__(self)

        self.lang_id = lang_id

        assert lang_id not in dicts
        dicts[lang_id] = self

        if lang_manager.dicts_path is None:
            raise PermissionError("You have to define the path to the dictionnaries before creating one")

        if os.path.exists(f"{lang_manager.dicts_path}{os.sep}dict_{lang_id}.py"):

            import pathlib
            file_path = f"{lang_manager.dicts_path}{os.sep}dict_{lang_id}.py"
            file_name = f"dict_{lang_id}"
            spec = importlib.util.spec_from_file_location(file_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for text_id, text in enumerate(module.texts):
                self[text_id] = text

        else:
            if self.lang_id == lang_manager.ref_language:
                raise FileNotFoundError("The dictionnary for the ref language has not been found")

            if not lang_manager.is_connected_to_network:
                raise ConnectionError("Translation impossible : "
                                      "baopig.googletrans.lang_manager is not connected to internet")

            try:
                import time
                start_time = time.time()

                translations = translator.optimized_translate(list(dicts[lang_manager.ref_language].values()),
                                                              src=lang_manager.ref_language, dest=lang_id)

                end_time = time.time()
                bp.LOGGER.fine(f"Language loading time : {end_time - start_time}")

            except Exception as e:
                bp.LOGGER.warning(e)
                raise e

            for text_id, translation in zip(dicts[lang_manager.ref_language].keys(), translations):
                self[text_id] = translation

    def save(self):

        absfilename = f"{os.path.abspath(os.path.dirname(sys.argv[0]))}{os.sep}lang{os.sep}dict_{self.lang_id}.py"

        with open(absfilename, 'w', encoding='utf8') as writer:

            writer.write('texts = [\n')
            writer.write(f'    "{self[0]}", "{self[1]}", "{self[2]}",\n')

            for i, text in self.items():
                if i > 2:
                    text = text.replace('\n', '\\n')
                    writer.write(f'    "{text}",\n')

            writer.write(']')


class LangManager(bp.Communicative):

    def __init__(self):

        bp.Communicative.__init__(self)

        self._dicts_path = None  # path to the dictionnary files

        self._ref_texts = {}
        self._textid_by_widget = {}
        self._ref_language = self._language = None

        self._is_connected_to_network = True

        self.create_signal("UPDATE_LANGUAGE")
        self.create_signal("NEW_CONNECTION_STATE")

    dicts_path = property(lambda self: self._dicts_path)
    is_connected_to_network = property(lambda self: self._is_connected_to_network)
    language = property(lambda self: self._language)
    ref_language = property(lambda self: self._ref_language)

    def get_text_from_id(self, text_id):
        try:
            return dicts[self._language][text_id]
        except KeyError:
            return dicts[self._ref_language][text_id]

    def remove_widget(self, widget):
        self._ref_texts.pop(widget)
        self._textid_by_widget.pop(widget)

    def set_connected(self, connected):

        if bool(connected) == self.is_connected_to_network:
            return

        if connected:
            if translator.test_connection():
                self._is_connected_to_network = True
            else:
                return

        else:
            self._is_connected_to_network = False

        self.signal.NEW_CONNECTION_STATE.emit()

    def set_language(self, lang_id):

        if lang_id == self._language:
            return

        if lang_id not in dicts:
            Dictionnary(lang_id)

        self._language = lang_id

        if self._language == self._ref_language:

            for widget, text in self._ref_texts.items():
                widget.set_text(text)
                widget.fit()

        else:

            for widget in self._ref_texts:
                widget.set_text(self.get_text_from_id(widget.text_id))
                widget.fit()

        self.signal.UPDATE_LANGUAGE.emit()

    def set_dicts_path(self, dicts_path):

        self._dicts_path = dicts_path

    def set_ref_language(self, ref_lang_id):

        assert self._ref_language is None, f"The reference language is already set to {self._ref_language}"
        assert isinstance(ref_lang_id, str) and len(ref_lang_id) == 2

        self._ref_language = self._language = ref_lang_id

        if ref_lang_id not in dicts:
            Dictionnary(ref_lang_id)

    def set_ref_text(self, widget, text_id):

        text = dicts["fr"][text_id]
        self._ref_texts[widget] = text
        self._textid_by_widget[widget] = text_id
        widget.text_id = text_id
        widget.set_text(self.get_text_from_id(widget.text_id))
        widget.fit()


class OptimizedTranslator(Translator):

    def optimized_translate(self, text, src, dest):

        if isinstance(text, list):

            sep = '\n'
            sep_transition = '▓'
            sep_encoded = '░'
            ln = len(text)
            joined = sep_transition.join(text)
            joined = joined.replace(sep, sep_encoded)
            joined = joined.replace(sep_transition, sep)
            joined_translated = self.optimized_translate(joined, dest=dest, src=src)
            joined_translated = joined_translated.replace(sep, sep_transition)
            joined_translated = joined_translated.replace(sep_encoded, sep)
            result = joined_translated.split(sep_transition)
            if ln == len(result):
                return result
            else:
                bp.LOGGER.info("Translation optimization has failed")

            return tuple(self.optimized_translate(t, src=src, dest=dest) for t in text)

        elif not text:
            return ""

        try:
            data, response = self._translate(text, dest, src, None)

        except ConnectError:
            bp.LOGGER.warning(f"Couldn't translate {text} from {src} to {dest}")
            return ""

        # this code will be updated when the format is changed.
        return ''.join([d[0] if d[0] else '' for d in data[0]])

    def test_connection(self):

        try:
            super()._translate("Bonjour", src="fr", dest="en", override=None)
        except ConnectError:
            return False
        else:
            return True


dicts = {}
lang_manager = LangManager()
translator = OptimizedTranslator()
