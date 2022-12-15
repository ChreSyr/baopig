import os
import sys
import importlib
from httpcore import ConnectError
import baopig as bp
from .constants import LANGUAGES
from .client import Translator


class Dictionnaries(dict):

    def add(self, lang_id, text):
        raise NotImplemented

        # text_id = len(self[lang_id])
        # self[lang_id][text_id] = text
        # return text_id


class Dictionnary(dict):

    def __init__(self, lang_id, translated_lang_name=None):

        dict.__init__(self)

        self.lang_id = lang_id
        self.lang_name_in_english = LANGUAGES[lang_id]
        self.translated_lang_name = translated_lang_name  # TODO : LANGUAGES_TRANSLATED

        assert lang_id not in dicts
        dicts[lang_id] = self

        if os.path.exists(f"{os.path.abspath(os.path.dirname(sys.argv[0]))}{os.sep}lang{os.sep}dict_{lang_id}.py"):

            module = importlib.import_module(f"lang.dict_{lang_id}")

            self.translated_lang_name = module.translated_lang_name

            for text_id, text in enumerate(module.texts):
                self[text_id] = text

    def save(self):

        absfilename = f"{os.path.abspath(os.path.dirname(sys.argv[0]))}{os.sep}lang{os.sep}dict_{self.lang_id}.py"

        with open(absfilename, 'w', encoding='utf8') as writer:

            writer.write('texts = [\n')
            # writer.write(f'    "{self[0]}", "{self[1]}", "{self[2]}",\n')

            for i, text in self.items():
                if i > 2:
                    text = text.replace('\n', '\\n')
                    writer.write(f'    "{text}",\n')
                elif i == 0:
                    writer.write(f'    "{text}",')
                elif i == 1:
                    writer.write(f' "{text}",')
                elif i == 2:
                    writer.write(f' "{text}",\n')

            writer.write(']\n')
            writer.write(f'translated_lang_name = "{self.translated_lang_name}"')


class LangManager(bp.Communicative):

    def __init__(self):

        bp.Communicative.__init__(self)

        self._ref_texts = {}
        self._textid_by_widget = {}
        self._ref_language = self._language = None

        self._is_connected_to_network = True

        self.create_signal("UPDATE_LANGUAGE")
        self.create_signal("NEW_CONNECTION_STATE")

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

            if not self.is_connected_to_network:
                raise ConnectionError("Translation impossible : "
                                      "baopig.googletrans.lang_manager is not connected to internet")

            old_cursor = bp.pygame.mouse.get_cursor()
            bp.pygame.mouse.set_cursor(bp.SYSTEM_CURSOR_WAIT)

            try:
                import time
                start_time = time.time()

                translations = translator.optimized_translate(list(dicts[self._ref_language].values()),
                                                              src=self._ref_language, dest=lang_id)

                end_time = time.time()
                bp.LOGGER.info(f"Language loading time : {end_time - start_time}")

            except Exception as e:
                bp.LOGGER.warning(e)
                raise e

            finally:
                bp.pygame.mouse.set_cursor(old_cursor)

            new_dict = Dictionnary(lang_id)

            for text_id, translation in zip(dicts[self._ref_language].keys(), translations):
                if translation is not None:
                    new_dict[text_id] = translation

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

            sep = '¸'

            ln = len(text)
            joined = sep.join(text)
            joined_translated = self.optimized_translate(joined, dest=dest, src=src)
            result = joined_translated.split(sep)
            if ln != len(result):
                for t in text:
                    if sep in t:
                        raise ValueError(f"Cannot translate a text containing the {sep} symbol")
                bp.LOGGER.warning("Translation optimization has failed")
                result = tuple(self.optimized_translate(t, src=src, dest=dest) for t in text)
            # for t in result:
            #     print(t)
            return result

        elif not text:
            return None

        try:
            data, response = self._translate(text, dest, src, None)

        except ConnectError:
            bp.LOGGER.warning(f"Couldn't translate {text} from {src} to {dest}")
            return None

        # this code will be updated when the format is changed.
        return ''.join([d[0] for d in data[0]])

    def test_connection(self):

        try:
            super()._translate("Bonjour", src="fr", dest="en", override=None)
        except ConnectError:
            return False
        else:
            return True


dicts = Dictionnaries()
lang_manager = LangManager()
translator = OptimizedTranslator()
