"""edge-tts allows you to use Microsoft Edge's online text-to-speech service without
needing Windows or the edge browser."""

from . import exceptions
from .auto_voice import (
    DEFAULT_VOICES_MAP,
    detect_language,
    get_voice_for_language,
    is_gender_option,
    select_voice_auto,
)
from .communicate import Communicate
from .submaker import SubMaker
from .version import __version__, __version_info__
from .voices import VoicesManager, list_voices

__all__ = [
    "DEFAULT_VOICES_MAP",
    "Communicate",
    "SubMaker",
    "VoicesManager",
    "__version__",
    "__version_info__",
    "detect_language",
    "exceptions",
    "get_voice_for_language",
    "is_gender_option",
    "list_voices",
    "select_voice_auto",
]
