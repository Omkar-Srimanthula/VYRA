import os
import sys
from pathlib import Path

# Add WinGet FFmpeg DLL directory on Windows
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

from services.tts_service import generate_speech

def test_tts():
    print("Testing TTS Resilience & Voice Generation...")
    output_wav = Path("storage/audio/test_narration_resilience.wav")
    speaker_sample = Path("storage/voice/voice_sample.wav")

    res = generate_speech(
        text="Welcome to VYRA AI Video Studio. Real facts and authentic media powers modern content.",
        output_path=str(output_wav),
        speaker_wav=str(speaker_sample),
        language="en"
    )

    assert Path(res).exists(), "Output narration WAV file does not exist"
    assert Path(res).stat().st_size > 1000, "Output WAV file is too small"
    print(f"[OK] TTS Resilience Test PASSED: {res} ({Path(res).stat().st_size:,} bytes)")

if __name__ == "__main__":
    test_tts()
