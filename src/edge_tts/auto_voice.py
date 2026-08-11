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

# Language code mapping from langdetect output to edge-tts format
LANG_CODE_MAP = {
    "zh-cn": "zh",
    "zh-tw": "zh",
    "zh": "zh",
    "en": "en",
    "es": "es",
    "fr": "fr",
    "de": "de",
    "it": "it",
    "pt": "pt",
    "ja": "ja",
    "ko": "ko",
    "ru": "ru",
    "ar": "ar",
    "hi": "hi",
    "nl": "nl",
    "pl": "pl",
    "tr": "tr",
    "sv": "sv",
    "da": "da",
    "fi": "fi",
    "no": "no",
    "cs": "cs",
    "el": "el",
    "he": "he",
    "th": "th",
    "vi": "vi",
    "id": "id",
    "ms": "ms",
    "tl": "tl",
    "uk": "uk",
    "ro": "ro",
    "hu": "hu",
    "sk": "sk",
    "bg": "bg",
    "hr": "hr",
    "sr": "sr",
    "sl": "sl",
    "ca": "ca",
    "et": "et",
    "lv": "lv",
    "lt": "lt",
}


def detect_language(text: str, min_length: int = 20) -> Optional[str]:
    """
    Detect the language of the given text.
    
    Args:
        text: The text to analyze
        min_length: Minimum text length for reliable detection
        
    Returns:
        Language code (e.g., 'en', 'zh', 'es') or None if detection fails
    """
    if not LANGDETECT_AVAILABLE:
        return None
    
    if len(text.strip()) < min_length:
        # For very short text, use character-based heuristic
        return _detect_by_chars(text)
    
    try:
        lang_code = detect(text)
        # Map to our supported language codes
        return LANG_CODE_MAP.get(lang_code.lower(), None)
    except LangDetectException:
        return _detect_by_chars(text)


def _detect_by_chars(text: str) -> Optional[str]:
    """
    Fallback language detection based on character ranges.
    
    Args:
        text: The text to analyze
        
    Returns:
        Language code or None if unknown
    """
    # Count characters in different ranges
    chinese_chars = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
    japanese_chars = sum(1 for c in text if '\u3040' <= c <= '\u30ff')
    korean_chars = sum(1 for c in text if '\uac00' <= c <= '\ud7af')
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06ff')
    hebrew_chars = sum(1 for c in text if '\u0590' <= c <= '\u05ff')
    thai_chars = sum(1 for c in text if '\u0e00' <= c <= '\u0e7f')
    cyrillic_chars = sum(1 for c in text if '\u0400' <= c <= '\u04ff')
    
    total_chars = len(text.replace(" ", ""))
    if total_chars == 0:
        return None
    
    # Check for dominant non-Latin scripts
    if chinese_chars / total_chars > 0.3:
        return "zh"
    if japanese_chars / total_chars > 0.3:
        return "ja"
    if korean_chars / total_chars > 0.3:
        return "ko"
    if arabic_chars / total_chars > 0.3:
        return "ar"
    if hebrew_chars / total_chars > 0.3:
        return "he"
    if thai_chars / total_chars > 0.3:
        return "th"
    if cyrillic_chars / total_chars > 0.5:
        return "ru"
    
    # Default to English for Latin script
    return "en"


async def get_voice_for_language(
    language: str,
    gender: str,
    custom_voices: Optional[List[Voice]] = None,
) -> Optional[str]:
    """
    Get a voice name for the specified language and gender.
    
    Args:
        language: Language code (e.g., 'en', 'zh', 'es')
        gender: 'male' or 'female'
        custom_voices: Optional custom list of voices to search
        
    Returns:
        Voice name string or None if not found
    """
    gender_lower = gender.lower()
    if gender_lower not in ("male", "female"):
        raise ValueError(f"Gender must be 'male' or 'female', got: {gender}")
    
    # First try the pre-configured default
    if language in DEFAULT_VOICES_MAP:
        return DEFAULT_VOICES_MAP[language].get(gender_lower)
    
    # If not in defaults, try to find dynamically
    try:
        voices_manager = await VoicesManager.create(custom_voices)
        
        # Try to find voices matching the language
        # Note: VoicesManager uses full locale codes, so we need to search differently
        matching_voices = [
            v for v in voices_manager.voices 
            if v.get("Locale", "").startswith(language) and 
               v.get("Gender", "").lower() == gender_lower
        ]
        
        if matching_voices:
            # Return the first match (could be improved with better selection logic)
            return matching_voices[0]["ShortName"]
    except Exception:
        pass
    
    return None


async def select_voice_auto(
    text: str,
    gender: str,
    custom_voices: Optional[List[Voice]] = None,
) -> str:
    """
    Automatically select a voice based on text language and gender.
    
    Args:
        text: The text to analyze
        gender: 'male' or 'female'
        custom_voices: Optional custom list of voices
        
    Returns:
        Voice name string
    """
    gender_lower = gender.lower()
    if gender_lower not in ("male", "female"):
        raise ValueError(f"Gender must be 'male' or 'female', got: {gender}")
    
    # Detect language
    language = detect_language(text)
    
    if language is None:
        # If detection fails, use default voice
        return DEFAULT_VOICE
    
    # Get voice for detected language
    voice = await get_voice_for_language(language, gender_lower, custom_voices)
    
    if voice is None:
        # Fallback to default voice with appropriate gender if possible
        # Try to find any voice with the requested gender
        try:
            voices_manager = await VoicesManager.create(custom_voices)
            matching_voices = [
                v for v in voices_manager.voices 
                if v.get("Gender", "").lower() == gender_lower
            ]
            if matching_voices:
                return matching_voices[0]["ShortName"]
        except Exception:
            pass
        
        return DEFAULT_VOICE
    
    return voice


def is_gender_option(value: str) -> bool:
    """Check if a value is a gender option ('male' or 'female')."""
    return value.lower() in ("male", "female")
