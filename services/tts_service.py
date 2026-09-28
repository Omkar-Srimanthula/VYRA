import os
import sys
import subprocess
from pathlib import Path

# Add WinGet FFmpeg DLL directory on Windows so torchcodec / TTS loads cleanly
if sys.platform == "win32" and hasattr(os, "add_dll_directory"):
    winget_packages = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if winget_packages.exists():
        for dll_file in winget_packages.rglob("avcodec-*.dll"):
            try:
                os.add_dll_directory(str(dll_file.parent))
                os.environ["PATH"] = str(dll_file.parent) + os.pathsep + os.environ.get("PATH", "")
                break
            except Exception:
                pass

import torch
from TTS.api import TTS
import shutil


# ==========================================================
# VYRA LOCAL VOICE CLONING — XTTS v2
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models" / "XTTS-v2"
DEFAULT_VOICE_SAMPLE = BASE_DIR / "storage" / "voice" / "voice_sample.wav"

_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
_tts = None


SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "pl": "Polish",
    "tr": "Turkish",
    "ru": "Russian",
    "nl": "Dutch",
    "cs": "Czech",
    "ar": "Arabic",
    "zh-cn": "Chinese",
    "ja": "Japanese",
    "hu": "Hungarian",
    "ko": "Korean",
}

LANGUAGE_ALIASES = {
    "english": "en",
    "spanish": "es",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "portuguese": "pt",
    "polish": "pl",
    "turkish": "tr",
    "russian": "ru",
    "dutch": "nl",
    "czech": "cs",
    "arabic": "ar",
    "chinese": "zh-cn",
    "japanese": "ja",
    "hungarian": "hu",
    "korean": "ko",
}


def normalize_language(language: str) -> str:
    if not language:
        return "en"

    lang_lower = str(language).strip().lower()
    if lang_lower in SUPPORTED_LANGUAGES:
        return lang_lower

    if lang_lower in LANGUAGE_ALIASES:
        return LANGUAGE_ALIASES[lang_lower]

    return "en"


def get_ffmpeg():
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg:
        return ffmpeg

    winget_path = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
    if winget_path.exists():
        matches = list(winget_path.rglob("ffmpeg.exe"))
        if matches:
            return str(matches[0])

    raise FileNotFoundError("FFmpeg executable not found.")


def get_tts():
    global _tts
    if _tts is None:
        print()
        print("=" * 60)
        print("LOADING VYRA LOCAL XTTS v2")
        print("=" * 60)
        print(f"Model directory: {MODEL_DIR}")
        print(f"Device: {_DEVICE}")

        model_file = MODEL_DIR / "model.pth"
        config_file = MODEL_DIR / "config.json"

        if not MODEL_DIR.exists():
            raise FileNotFoundError(f"XTTS model directory not found: {MODEL_DIR}")
        if not model_file.exists():
            raise FileNotFoundError(f"XTTS model file not found: {model_file}")
        if not config_file.exists():
            raise FileNotFoundError(f"XTTS config file not found: {config_file}")

        print("Loading local model...")
        _tts = TTS(
            model_path=str(MODEL_DIR),
            config_path=str(config_file),
            progress_bar=False,
            gpu=torch.cuda.is_available()
        )
        print("XTTS v2 local model loaded successfully.")

    return _tts


def generate_speech(
    text: str,
    output_path: str,
    speaker_wav: str | None = None,
    language: str = "en"
) -> str:
    """
    Generate narration using XTTS-v2 voice cloning with automatic GPU error recovery
    and gTTS fallback safety.
    """

    if not text or not text.strip():
        raise ValueError("Speech text is empty.")

    clean_text = str(text).strip()
    language_code = normalize_language(language)

    output_file = Path(output_path).resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if speaker_wav:
        reference_file = Path(speaker_wav).resolve()
    else:
        reference_file = DEFAULT_VOICE_SAMPLE.resolve()

    print()
    print("=" * 60)
    print("GENERATING VYRA CLONED VOICE")
    print("=" * 60)
    print(f"Reference voice: {reference_file}")
    print(f"Language: {language_code}")
    print(f"Output: {output_file}")
    print(f"Device: {_DEVICE}")

    # Level 1: Try Local XTTS-v2 Cloned Voice
    try:
        if reference_file.exists() and reference_file.stat().st_size > 0:
            tts = get_tts()
            tts.tts_to_file(
                text=clean_text,
                speaker_wav=[str(reference_file)],
                language=language_code,
                file_path=str(output_file),
                split_sentences=True
            )
            if output_file.exists() and output_file.stat().st_size > 1000:
                print(f"CLONED VOICE GENERATED SUCCESSFULLY: {output_file.stat().st_size:,} bytes")
                return str(output_file)
    except Exception as e:
        print(f"[TTS CUDA WARNING] XTTS-v2 generation failed: {e}")
        if torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass

    # Level 2: Native gTTS Audio Fallback
    print(f"[TTS Fallback] Using native gTTS audio fallback for language '{language_code}'...")
    try:
        from gtts import gTTS
        gtts_lang = language_code if len(language_code) <= 2 else language_code.split("-")[0]
        tts_engine = gTTS(text=clean_text, lang=gtts_lang)

        temp_mp3 = output_file.with_suffix(".temp.mp3")
        tts_engine.save(str(temp_mp3))

        ffmpeg = get_ffmpeg()
        cmd = [ffmpeg, "-y", "-i", str(temp_mp3), "-ac", "1", "-ar", "22050", str(output_file)]
        subprocess.run(cmd, capture_output=True, check=True)

        if temp_mp3.exists():
            try:
                temp_mp3.unlink()
            except Exception:
                pass

        if output_file.exists() and output_file.stat().st_size > 1000:
            print(f"Native gTTS fallback audio generated successfully: {output_file.stat().st_size:,} bytes")
            return str(output_file)
    except Exception as fallback_error:
        print(f"[TTS Fallback Error] gTTS generation failed: {fallback_error}")

    raise RuntimeError("Voice generation failed across XTTS and fallback engines.")