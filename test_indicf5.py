
from pathlib import Path
import numpy as np
import soundfile as sf
import torch

from f5_tts.model import DiT
from f5_tts.infer.utils_infer import (
    load_vocoder,
    load_checkpoint,
    preprocess_ref_audio_text,
    infer_process,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

VOICE_FILE = BASE_DIR / "storage" / "voice" / "voice_sample.wav"
OUTPUT_FILE = BASE_DIR / "storage" / "audio" / "indicf5_telugu_test.wav"

CHECKPOINT = Path(
    r"C:\Users\omkar\.cache\huggingface\hub\models--SWivid--F5-TTS"
    r"\snapshots\84e5a410d9cead4de2f847e7c9369a6440bdfaca"
    r"\F5TTS_Base\model_1200000.safetensors"
)

VOCAB_FILE = Path(
    r"C:\Users\omkar\.cache\huggingface\hub\models--SWivid--F5-TTS"
    r"\snapshots\84e5a410d9cead4de2f847e7c9369a6440bdfaca"
    r"\F5TTS_Base\vocab.txt"
)


# ============================================================
# DEVICE
# ============================================================

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


# ============================================================
# TEXT
# ============================================================

REFERENCE_TEXT = (
    "I have shown you interesting software out of Punjab, "
    "Artificial Intelligence. I am working on improving my technology. "
    "I also have experience working on academic college projects "
    "and solving problems."
)

TELUGU_TEXT = (
    "కృత్రిమ మేధస్సు మన జీవితాలను వేగంగా మార్చుతోంది. "
    "భవిష్యత్తులో మనం సాంకేతికతను మరింత తెలివిగా "
    "ఉపయోగించుకోగలము."
)


# ============================================================
# HELPERS
# ============================================================

def print_header(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


# ============================================================
# START
# ============================================================

print_header("VYRA — F5-TTS TELUGU VOICE GENERATION")

print("Device:", DEVICE)
print("Voice:", VOICE_FILE)
print("Checkpoint:", CHECKPOINT)
print("Vocab:", VOCAB_FILE)
print("Output:", OUTPUT_FILE)


# ============================================================
# CHECK FILES
# ============================================================

if not VOICE_FILE.exists():
    raise FileNotFoundError(f"Voice sample not found: {VOICE_FILE}")

if not CHECKPOINT.exists():
    raise FileNotFoundError(f"Checkpoint not found: {CHECKPOINT}")

if not VOCAB_FILE.exists():
    raise FileNotFoundError(f"Vocab file not found: {VOCAB_FILE}")

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

print()
print("Voice sample found.")
print("Voice size:", VOICE_FILE.stat().st_size, "bytes")

print("Checkpoint found.")
print("Checkpoint size:", CHECKPOINT.stat().st_size, "bytes")

print("Vocab found.")
print("Vocab size:", VOCAB_FILE.stat().st_size, "bytes")


# ============================================================
# IMPORT
# ============================================================

print_header("IMPORTING F5-TTS")

print("F5-TTS imports successful.")


# ============================================================
# MODEL CONFIGURATION
# ============================================================

print_header("MODEL CONFIGURATION")

MODEL_CONFIG = {
    "dim": 1024,
    "depth": 22,
    "heads": 16,
    "ff_mult": 2,
    "text_dim": 512,
    "conv_layers": 4,
}

print(MODEL_CONFIG)


# ============================================================
# BUILD MODEL
# ============================================================

print_header("BUILDING MODEL ARCHITECTURE")

model = DiT(**MODEL_CONFIG)

print("Model architecture created.")


# ============================================================
# LOAD CHECKPOINT
# ============================================================

print_header("LOADING CHECKPOINT")

model = load_checkpoint(
    model,
    str(CHECKPOINT),
    DEVICE,
    use_ema=True,
)

model.eval()

print("Checkpoint loaded successfully.")


# ============================================================
# LOAD VOCODER
# ============================================================

print_header("LOADING VOCOS VOCODER")

print("Loading Vocos...")
print("If this is the first run, it may download/load model files.")

vocoder = load_vocoder(
    vocoder_name="vocos",
    device=DEVICE,
)

print("Vocos loaded successfully.")


# ============================================================
# REFERENCE AUDIO
# ============================================================

print_header("PREPARING REFERENCE VOICE")

print("Reference audio:")
print(VOICE_FILE)

print()
print("Reference text:")
print(REFERENCE_TEXT)

ref_audio, ref_text = preprocess_ref_audio_text(
    str(VOICE_FILE),
    REFERENCE_TEXT,
    clip_short=False,
    device=DEVICE,
)

print()
print("Reference voice prepared.")


# ============================================================
# TELUGU GENERATION
# ============================================================

print_header("TELUGU TEXT")

print(TELUGU_TEXT)

print()
print("Starting F5-TTS inference...")
print("This may take several minutes on the RTX 3050.")


# ============================================================
# INFERENCE
# ============================================================

generated_wave, sample_rate, spectrogram = infer_process(
    ref_audio=ref_audio,
    ref_text=ref_text,
    gen_text=TELUGU_TEXT,
    model_obj=model,
    vocoder=vocoder,
    mel_spec_type="vocos",
    target_rms=0.1,
    cross_fade_duration=0.15,
    nfe_step=32,
    cfg_strength=2.0,
    sway_sampling_coef=-1,
    speed=1.0,
    fix_duration=None,
    device=DEVICE,
)


# ============================================================
# SAVE AUDIO
# ============================================================

print_header("SAVING GENERATED AUDIO")

generated_wave = np.asarray(generated_wave, dtype=np.float32)

sf.write(
    str(OUTPUT_FILE),
    generated_wave,
    sample_rate,
)

print("Audio generation complete.")
print()
print("Output:", OUTPUT_FILE)
print("Sample rate:", sample_rate)
print("Samples:", len(generated_wave))
print("Duration:", round(len(generated_wave) / sample_rate, 2), "seconds")
print("File size:", OUTPUT_FILE.stat().st_size, "bytes")


# ============================================================
# SUCCESS
# ============================================================

print_header("SUCCESS")

print("VYRA generated Telugu speech using:")
print("  ✓ F5-TTS")
print("  ✓ RTX 3050 GPU")
print("  ✓ Your reference voice")
print("  ✓ Telugu text")
print("  ✓ Vocos vocoder")

print()
print("Generated file:")
print(OUTPUT_FILE)

