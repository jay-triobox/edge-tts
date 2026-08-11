#!/usr/bin/env python3

"""Example demonstrating automatic voice selection based on text language and gender."""

import asyncio
import edge_tts

# Example texts in different languages
TEXTS = {
    "english": "Hello, this is a test of the automatic voice selection feature.",
    "chinese": "你好，这是自动语音选择功能的测试。",
    "spanish": "Hola, esta es una prueba de la función de selección automática de voz.",
    "french": "Bonjour, ceci est un test de la fonction de sélection automatique de voix.",
    "japanese": "こんにちは、これは自動音声選択機能のテストです。",
}


async def test_gender_voice(language: str, text: str, gender: str) -> None:
    """Test TTS with automatic voice selection for a given language and gender."""
    print(f"\n{'='*60}")
    print(f"Language: {language}, Gender: {gender}")
    print(f"Text: {text[:50]}...")
    
    # Use the new 'male' or 'female' option
    communicate = edge_tts.Communicate(text, gender)
    output_file = f"{language}_{gender}.mp3"
    
    try:
        await communicate.save(output_file)
        print(f"✓ Audio saved to: {output_file}")
        print(f"  Used voice: {communicate.voice}")
    except Exception as e:
        print(f"✗ Error: {e}")


async def amain() -> None:
    """Main function to demonstrate automatic voice selection."""
    print("Edge-TTS Automatic Voice Selection Demo")
    print("=" * 60)
    print("This demo shows how to use 'male' or 'female' as the --voice option")
    print("to automatically select a voice based on the detected language.")
    
    # Test each language with both male and female voices
    for lang, text in TEXTS.items():
        for gender in ["male", "female"]:
            await test_gender_voice(lang, text, gender)
    
    print("\n" + "=" * 60)
    print("Demo complete! Check the generated MP3 files.")


if __name__ == "__main__":
    asyncio.run(amain())
