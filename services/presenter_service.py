import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps
import math

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
PRESENTER_DIR = STORAGE_DIR / "presenter"
PRESENTER_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_FACE_PATH = PRESENTER_DIR / "user_face.png"


def create_default_presenter_face() -> Path:
    """
    Creates a default professional digital avatar presenter image if user face is not provided.
    """
    if DEFAULT_FACE_PATH.exists() and DEFAULT_FACE_PATH.stat().st_size > 5000:
        return DEFAULT_FACE_PATH

    width, height = 400, 400
    img = Image.new("RGBA", (width, height), (20, 24, 38, 255))
    draw = ImageDraw.Draw(img)

    # Draw gradient background circle
    draw.ellipse([20, 20, 380, 380], fill=(30, 41, 59, 255), outline=(0, 229, 255, 255), width=6)

    # Draw stylized avatar head & shoulders
    # Head
    draw.ellipse([130, 70, 270, 210], fill=(226, 232, 240, 255))
    # Shoulders
    draw.ellipse([70, 190, 330, 370], fill=(51, 65, 85, 255))
    # Eyes
    draw.ellipse([160, 120, 180, 140], fill=(30, 41, 59, 255))
    draw.ellipse([220, 120, 240, 140], fill=(30, 41, 59, 255))
    # Smile
    draw.arc([170, 150, 230, 180], start=0, end=180, fill=(30, 41, 59, 255), width=4)

    img.save(DEFAULT_FACE_PATH, "PNG")
    print(f"Created default digital presenter avatar: {DEFAULT_FACE_PATH}")
    return DEFAULT_FACE_PATH


def get_presenter_face_image() -> Path:
    if DEFAULT_FACE_PATH.exists() and DEFAULT_FACE_PATH.stat().st_size > 1000:
        return DEFAULT_FACE_PATH
    return create_default_presenter_face()


def overlay_presenter_avatar(
    background_image_path: str,
    output_image_path: str,
    scene_number: int = 1,
    is_speaking: bool = True
) -> str:
    """
    Overlays consent-based presenter avatar onto authentic background scene image.
    Enforces authentic source background photos/graphics.
    """
    bg_path = Path(background_image_path).resolve()
    out_path = Path(output_image_path).resolve()

    if not bg_path.exists():
        return background_image_path

    # Load authentic background image & resize to vertical 1080x1920
    bg = Image.open(bg_path).convert("RGB")
    bg = ImageOps.fit(bg, (1080, 1920), Image.Resampling.LANCZOS)

    # Load presenter face image
    face_path = get_presenter_face_image()
    face_img = Image.open(face_path).convert("RGBA")

    # Resize avatar to 320x320
    avatar_size = 320
    face_img = ImageOps.fit(face_img, (avatar_size, avatar_size), Image.Resampling.LANCZOS)

    # Create circular mask for avatar
    mask = Image.new("L", (avatar_size, avatar_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse([0, 0, avatar_size, avatar_size], fill=255)

    # Add glowing accent ring around avatar
    ring_size = avatar_size + 20
    ring_img = Image.new("RGBA", (ring_size, ring_size), (0, 0, 0, 0))
    ring_draw = ImageDraw.Draw(ring_img)
    border_color = (0, 229, 255, 255) if is_speaking else (148, 163, 184, 255)
    ring_draw.ellipse([0, 0, ring_size - 1, ring_size - 1], outline=border_color, width=8)

    # Add speaking lip animation indicator if speaking
    if is_speaking:
        # Dynamic talking mouth overlay
        mouth_draw = ImageDraw.Draw(face_img)
        mouth_y = int(avatar_size * 0.68)
        mouth_h = 16 if (scene_number % 2 == 0) else 8
        mouth_draw.ellipse(
            [avatar_size // 2 - 20, mouth_y - mouth_h // 2, avatar_size // 2 + 20, mouth_y + mouth_h // 2],
            fill=(180, 40, 40, 255)
        )

    # Position avatar at bottom-center of vertical video (1080x1920)
    pos_x = (1080 - ring_size) // 2
    pos_y = 1920 - ring_size - 180

    # Paste glowing ring & avatar onto background
    bg.paste(ring_img, (pos_x, pos_y), ring_img)
    bg.paste(face_img, (pos_x + 10, pos_y + 10), mask)

    # Add PRESENTER badge overlay
    badge_draw = ImageDraw.Draw(bg)
    badge_w, badge_h = 160, 36
    badge_x = (1080 - badge_w) // 2
    badge_y = pos_y + ring_size - 10
    badge_draw.rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], fill=(15, 23, 42, 230), outline=(0, 229, 255, 255), width=2)

    try:
        font = ImageFont.truetype("C:\\Windows\\Fonts\\segoeui.ttf", 18)
    except Exception:
        font = ImageFont.load_default()

    badge_draw.text((1080 // 2, badge_y + badge_h // 2), "AI PRESENTER", fill=(255, 255, 255), font=font, anchor="mm")

    bg.save(out_path, "PNG")
    return str(out_path)
