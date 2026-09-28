from pathlib import Path
from TTS.api import TTS

MODEL_DIR = Path("models/XTTS-v2")
VOICE_SAMPLE = Path("storage/voice/voice_sample.wav")
OUTPUT = Path("storage/audio/xtts_clone_test.wav")

print("Checking files...")

if not VOICE_SAMPLE.exists():
    raise FileNotFoundError(f"Voice sample not found: {VOICE_SAMPLE}")

if not (MODEL_DIR / "model.pth").exists():
    raise FileNotFoundError("XTTS model not found.")

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

print("Loading local XTTS-v2...")
print("This may take a while on CPU.")

tts = TTS(
    model_path=str(MODEL_DIR),
    config_path=str(MODEL_DIR / "config.json"),
    progress_bar=True,
    gpu=False,
)

print("XTTS loaded successfully.")
print("Generating cloned voice...")

tts.tts_to_file(
    text="Hello, this is VYRA. This is a test of my cloned voice.",
    speaker_wav=str(VOICE_SAMPLE),
    language="en",
    file_path=str(OUTPUT),
)

print()
print("===================================")
print("VOICE CLONING TEST SUCCESSFUL")
print("===================================")
print(f"Output: {OUTPUT.resolve()}")