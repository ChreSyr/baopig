"""Free Google Translate API for Python. Translates totally free of charge."""
__all__ = 'Translator',
__version__ = '3.1.0-alpha'

from .client import Translator
from .constants import LANGCODES, LANGUAGES, LANGUAGES_TRANSLATED  # noqa

from .extension import Dictionnary, dicts, lang_manager, translator
from .translatable import Translatable, TranslatableText, PartiallyTranslatableText, TranslatableIndicator
