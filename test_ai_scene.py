from pathlib import Path

import torch
from diffusers import StableDiffusionPipeline


# ==========================================================
# PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent

MODELS_DIR = BASE_DIR / "models"
OUTPUT_DIR = BASE_DIR / "storage" / "ai_scenes"

MODELS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==========================================================
# SETTINGS
# ==========================================================

MODEL_ID = "runwayml/stable-diffusion-v1-5"

OUTPUT_FILE = OUTPUT_DIR / "test_ai_scene.png"

PROMPT = (
    "cinematic realistic photograph of Bitcoin and digital "
    "finance, glowing golden Bitcoin coin surrounded by "
    "subtle digital financial data, futuristic city at night, "
    "dramatic lighting, highly detailed, realistic, "
    "professional documentary style, vertical composition"
)

NEGATIVE_PROMPT = (
    "blurry, low quality, distorted, deformed, text, "
    "watermark, logo, duplicate objects, cartoon"
)


# ==========================================================
# GPU CHECK
# ==========================================================

print()
print("=" * 60)
print("VYRA AI IMAGE GENERATION TEST")
print("=" * 60)

print("PyTorch:", torch.__version__)
print("CUDA:", torch.cuda.is_available())

if not torch.cuda.is_available():
    raise RuntimeError(
        "CUDA is not available. VYRA requires the NVIDIA GPU "
        "for this test."
    )

print("GPU:", torch.cuda.get_device_name(0))


# ==========================================================
# LOAD MODEL
# ==========================================================

print()
print("=" * 60)
print("LOADING STABLE DIFFUSION")
print("=" * 60)

print("Model:", MODEL_ID)
print("This may take a while the first time.")
print("The model will be downloaded automatically.")


pipe = StableDiffusionPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    safety_checker=None,
)


# ==========================================================
# LOW VRAM SETTINGS
# ==========================================================

pipe.enable_attention_slicing()

try:
    pipe.enable_vae_slicing()
except Exception:
    pass

try:
    pipe.enable_vae_tiling()
except Exception:
    pass

pipe = pipe.to("cuda")


# ==========================================================
# GENERATE
# ==========================================================

print()
print("=" * 60)
print("GENERATING AI IMAGE")
print("=" * 60)

print("Resolution: 512x512")
print("Prompt:")
print(PROMPT)
print()


with torch.inference_mode():

    image = pipe(
        prompt=PROMPT,
        negative_prompt=NEGATIVE_PROMPT,
        width=512,
        height=512,
        num_inference_steps=20,
        guidance_scale=7.0,
    ).images[0]


# ==========================================================
# SAVE
# ==========================================================

image.save(OUTPUT_FILE)


# ==========================================================
# VERIFY
# ==========================================================

if not OUTPUT_FILE.exists():
    raise RuntimeError(
        "AI image was not created."
    )

print()
print("=" * 60)
print("AI IMAGE GENERATION SUCCESSFUL")
print("=" * 60)

print("Output:")
print(OUTPUT_FILE.resolve())

print(
    f"File size: "
    f"{OUTPUT_FILE.stat().st_size / 1024:.2f} KB"
)

print()
print("VYRA now has a real AI-generated scene image.")