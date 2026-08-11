"""Language detection and automatic voice selection for edge-tts."""

import re
from typing import Optional, List, Dict

try:
    from langdetect import detect, DetectorFactory
    from langdetect.lang_detect_exception import LangDetectException
    
    # Set seed for consistent results
    DetectorFactory().set_seed(0)
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False

from .voices import VoicesManager, Voice
from .constants import DEFAULT_VOICE


# Pre-configured default voices for each language and gender
# These are high-quality neural voices that work well for general purposes
DEFAULT_VOICES_MAP: Dict[str, Dict[str, str]] = {
    "en": {"male": "en-US-AndrewMultilingualNeural", "female": "en-US-EmmaMultilingualNeural"},
    "zh": {"male": "zh-CN-YunxiNeural", "female": "zh-CN-XiaoxiaoNeural"},
    "zh-cn": {"male": "zh-CN-YunyangNeural", "female": "zh-CN-XiaoxiaoNeural"},
    "zh-tw": {"male": "zh-TW-YunJheNeural", "female": "zh-TW-HsiaoChenNeural"},
    "es": {"male": "es-ES-AlvaroNeural", "female": "es-ES-ElviraNeural"},
    "fr": {"male": "fr-FR-HenriNeural", "female": "fr-FR-DeniseNeural"},
    "de": {"male": "de-DE-ConradNeural", "female": "de-DE-KatjaNeural"},
    "it": {"male": "it-IT-DiegoNeural", "female": "it-IT-ElsaNeural"},
    "pt": {"male": "pt-BR-AntonioNeural", "female": "pt-BR-FranciscaNeural"},
    "ja": {"male": "ja-JP-KeitaNeural", "female": "ja-JP-NanamiNeural"},
    "ko": {"male": "ko-KR-InJoonNeural", "female": "ko-KR-SunHiNeural"},
    "ru": {"male": "ru-RU-DmitryNeural", "female": "ru-RU-SvetlanaNeural"},
    "ar": {"male": "ar-SA-HamedNeural", "female": "ar-SA-ZariyahNeural"},
    "hi": {"male": "hi-IN-MadhurNeural", "female": "hi-IN-SwaraNeural"},
    "nl": {"male": "nl-NL-MaartenNeural", "female": "nl-NL-ColetteNeural"},
    "pl": {"male": "pl-PL-MarekNeural", "female": "pl-PL-ZofiaNeural"},
    "tr": {"male": "tr-TR-AhmetNeural", "female": "tr-TR-EmelNeural"},
    "sv": {"male": "sv-SE-MattiasNeural", "female": "sv-SE-SofieNeural"},
    "da": {"male": "da-DK-JeppeNeural", "female": "da-DK-ChristelNeural"},
    "fi": {"male": "fi-FI-HarriNeural", "female": "fi-FI-NooraNeural"},
    "no": {"male": "nb-NO-FinnNeural", "female": "nb-NO-PernilleNeural"},
    "cs": {"male": "cs-CZ-AntoninNeural", "female": "cs-CZ-VlastaNeural"},
    "el": {"male": "el-GR-NestorasNeural", "female": "el-GR-AthinaNeural"},
    "he": {"male": "he-IL-AvriNeural", "female": "he-IL-HilaNeural"},
    "th": {"male": "th-TH-NiwatNeural", "female": "th-TH-PremwadeeNeural"},
    "vi": {"male": "vi-VN-NamMinhNeural", "female": "vi-VN-HoaiMyNeural"},
    "id": {"male": "id-ID-ArdiNeural", "female": "id-ID-GadisNeural"},
    "ms": {"male": "ms-MY-OsmanNeural", "female": "ms-MY-YasminNeural"},
    "tl": {"male": "fil-PH-AngeloNeural", "female": "fil-PH-BlessicaNeural"},
    "uk": {"male": "uk-UA-OstapNeural", "female": "uk-UA-PolinaNeural"},
    "ro": {"male": "ro-RO-EmilNeural", "female": "ro-RO-AlinaNeural"},
    "hu": {"male": "hu-HU-TamasNeural", "female": "hu-HU-NoemiNeural"},
    "sk": {"male": "sk-SK-LukasNeural", "female": "sk-SK-ViktoriaNeural"},
    "bg": {"male": "bg-BG-BorislavNeural", "female": "bg-BG-KalinaNeural"},
    "hr": {"male": "hr-HR-SreckoNeural", "female": "hr-HR-GabrijelaNeural"},
    "sr": {"male": "sr-RS-NicholasNeural", "female": "sr-RS-SophieNeural"},
    "sl": {"male": "sl-SI-RokNeural", "female": "sl-SI-PetraNeural"},
    "ca": {"male": "ca-ES-EnricNeural", "female": "ca-ES-JoanaNeural"},
    "et": {"male": "et-EE-KertNeural", "female": "et-EE-AnuNeural"},
    "lv": {"male": "lv-LV-NilsNeural", "female": "lv-LV-EveritaNeural"},
    "lt": {"male": "lt-LT-LeonasNeural", "female": "lt-LT-OnaNeural"},
}


def is_gender_option(value: str) -> bool:
    """Check if the provided value is a gender option (male/female)."""
    return value.lower() in ("male", "female")

def detect_language(text: str) -> str:
    """
    Detect the language of the given text.
    
    Args:
        text: The input text string.
        
    Returns:
        A lowercase language code (e.g., 'en', 'zh', 'es').
        Returns 'en' as fallback if detection fails or text is too short.
    """
    if not text or len(text.strip()) < 3:
        return "en"

    try:
        from langdetect import detect, DetectorFactory
        # Set seed for consistent results
        DetectorFactory.seed = 0
        lang = detect(text)
        return lang.lower()
    except ImportError:
        # Fallback if langdetect is not installed
        # Simple heuristic for CJK characters
        if re.search(r'[\u4e00-\u9fff]', text):
            return "zh"
        if re.search(r'[\u3040-\u309f\u30a0-\u30ff]', text):
            return "ja"
        if re.search(r'[\uac00-\ud7af]', text):
            return "ko"
        return "en"
    except Exception:
        return "en"

async def get_voice_for_language(
    language: str, 
    gender: str, 
    voices_manager: Optional[VoicesManager] = None
) -> str:
    """
    Get a specific voice name for a given language and gender.
    
    Args:
        language: Language code (e.g., 'en', 'zh').
        gender: 'male' or 'female'.
        voices_manager: Optional VoicesManager instance for dynamic lookup.
        
    Returns:
        The voice name string.
    """
    lang_lower = language.lower()
    gender_lower = gender.lower()

    #  Try pre-defined map first
    if lang_lower in DEFAULT_VOICES_MAP:
        return DEFAULT_VOICES_MAP[lang_lower][gender_lower]
    
    return "en-US-EmmaMultilingualNeural"

async def select_voice_auto(text: str, gender: str) -> str:
    """
    Automatically select a voice based on text content and desired gender.
    
    Args:
        text: The input text to synthesize.
        gender: 'male' or 'female'.
        
    Returns:
        The selected voice name.
    """
    if not is_gender_option(gender):
        raise ValueError(f"Invalid gender option: {gender}. Must be 'male' or 'female'.")
    
    lang = detect_language(text)

    return await get_voice_for_language(lang, gender, None)
    
