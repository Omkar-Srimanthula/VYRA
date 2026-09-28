from pathlib import Path
import subprocess
import shutil
import gc
import random

from PIL import Image, ImageDraw, ImageFont
import torch
from diffusers import StableDiffusionPipeline

from .visual_retrieval_service import get_authentic_scene_visual
from .presenter_service import overlay_presenter_avatar



# ==========================================================
# PROJECT PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

STORAGE_DIR = BASE_DIR / "storage"
AI_SCENES_DIR = STORAGE_DIR / "ai_scenes"
SCENES_DIR = STORAGE_DIR / "scenes"

STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

AI_SCENES_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SCENES_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================================
# SETTINGS
# ==========================================================

MODEL_ID = "runwayml/stable-diffusion-v1-5"


# ----------------------------------------------------------
# DEVICE
# ----------------------------------------------------------

DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


# ----------------------------------------------------------
# DATA TYPE
# ----------------------------------------------------------

DTYPE = (
    torch.float16
    if DEVICE == "cuda"
    else torch.float32
)


# ----------------------------------------------------------
# PROMPT SETTINGS
# ----------------------------------------------------------

# Stable Diffusion 1.5 uses CLIP with a 77-token limit.
# Keeping prompts short prevents truncation.
MAX_PROMPT_WORDS = 55


# ----------------------------------------------------------
# IMAGE SETTINGS
# ----------------------------------------------------------

IMAGE_WIDTH = 512
IMAGE_HEIGHT = 512


# ----------------------------------------------------------
# AI GENERATION SETTINGS
# ----------------------------------------------------------

INFERENCE_STEPS = 15

GUIDANCE_SCALE = 7.0


# ----------------------------------------------------------
# VIDEO SETTINGS
# ----------------------------------------------------------

VIDEO_WIDTH = 1080
VIDEO_HEIGHT = 1920

VIDEO_FPS = 30


# ----------------------------------------------------------
# CAMERA SETTINGS
# ----------------------------------------------------------

# Starting zoom.
START_ZOOM = 1.0

# Maximum zoom.
#
# 1.06 = subtle
# 1.08 = cinematic
# 1.10 = stronger
#
# We use 1.08.
MAX_ZOOM = 1.08

# Zoom speed.
#
# Lower = slower.
ZOOM_SPEED = 0.00035


# ==========================================================
# GLOBAL MODEL
# ==========================================================

_PIPE = None


# ==========================================================
# FIND FFMPEG
# ==========================================================

def get_ffmpeg():

    ffmpeg = shutil.which(
        "ffmpeg"
    )

    if ffmpeg:
        return ffmpeg

    base_path = (
        Path.home()
        / "AppData"
        / "Local"
        / "Microsoft"
        / "WinGet"
        / "Packages"
    )

    if base_path.exists():

        matches = list(
            base_path.rglob(
                "ffmpeg.exe"
            )
        )

        # Prefer executable from Shared folder
        shared_matches = [
            path
            for path in matches
            if "Shared" in str(path)
        ]

        if shared_matches:

            return str(
                shared_matches[0]
            )

        if matches:

            return str(
                matches[0]
            )

    raise FileNotFoundError(
        "FFmpeg was not found. "
        "Please make sure FFmpeg is installed."
    )


# ==========================================================
# LOAD AI MODEL
# ==========================================================

def get_pipeline():

    global _PIPE

    # ------------------------------------------------------
    # USE EXISTING MODEL
    # ------------------------------------------------------

    if _PIPE is not None:

        return _PIPE

    print()
    print("=" * 60)
    print("LOADING VYRA AI IMAGE MODEL")
    print("=" * 60)

    print(
        "Model:",
        MODEL_ID
    )

    print(
        "Device:",
        DEVICE
    )

    # ------------------------------------------------------
    # LOAD MODEL
    # ------------------------------------------------------

    _PIPE = StableDiffusionPipeline.from_pretrained(
        MODEL_ID,
        torch_dtype=DTYPE,
        safety_checker=None,
    )

    # ------------------------------------------------------
    # MEMORY OPTIMIZATION
    # ------------------------------------------------------

    try:

        _PIPE.enable_attention_slicing()

    except Exception:

        pass

    try:

        _PIPE.vae.enable_slicing()

    except Exception:

        pass

    try:

        _PIPE.vae.enable_tiling()

    except Exception:

        pass

    # ------------------------------------------------------
    # MOVE MODEL TO DEVICE
    # ------------------------------------------------------

    if DEVICE == "cuda":

        _PIPE = _PIPE.to(
            "cuda"
        )

    else:

        _PIPE = _PIPE.to(
            "cpu"
        )

    print()
    print(
        "VYRA AI IMAGE MODEL READY"
    )

    return _PIPE


# ==========================================================
# SCENE CATEGORY
# ==========================================================

def detect_scene_category(
    description
):

    text = str(
        description or ""
    ).lower()

    categories = {

        # --------------------------------------------------
        # SPACE
        # --------------------------------------------------

        "space": [

            "space",
            "planet",
            "planets",
            "galaxy",
            "galaxies",
            "universe",
            "cosmic",
            "cosmos",
            "star",
            "stars",
            "sun",
            "moon",
            "mars",
            "earth",
            "saturn",
            "jupiter",
            "nebula",
            "asteroid",
            "astronaut",
            "rocket",
            "orbit",
            "solar system",

        ],

        # --------------------------------------------------
        # SLEEP
        # --------------------------------------------------

        "sleep": [

            "sleep",
            "sleeping",
            "bed",
            "bedroom",
            "wake",
            "waking",
            "morning",
            "rest",

        ],

        # --------------------------------------------------
        # EXERCISE
        # --------------------------------------------------

        "exercise": [

            "exercise",
            "exercising",
            "workout",
            "gym",
            "running",
            "jogging",
            "fitness",
            "training",
            "sport",

        ],

        # --------------------------------------------------
        # FOOD
        # --------------------------------------------------

        "food": [

            "food",
            "eat",
            "eating",
            "healthy",
            "vegetable",
            "vegetables",
            "cooking",
            "meal",
            "kitchen",
            "nutrition",

        ],

        # --------------------------------------------------
        # READING
        # --------------------------------------------------

        "reading": [

            "read",
            "reading",
            "book",
            "books",
            "study",
            "studying",
            "library",
            "learning",

        ],

        # --------------------------------------------------
        # GRATITUDE
        # --------------------------------------------------

        "gratitude": [

            "gratitude",
            "grateful",
            "thank",
            "thanks",
            "smiling",
            "positive",
            "happy",

        ],

        # --------------------------------------------------
        # TECHNOLOGY
        # --------------------------------------------------

        "technology": [

            "computer",
            "technology",
            "phone",
            "laptop",
            "software",
            "ai",
            "artificial intelligence",
            "robot",
            "digital",
            "cyber",

        ],

        # --------------------------------------------------
        # MONEY / FINANCE
        # --------------------------------------------------

        "money": [

            "money",
            "wealth",
            "finance",
            "stock",
            "stocks",
            "crypto",
            "bitcoin",
            "trading",
            "investment",
            "market",

        ],
    }

    # ------------------------------------------------------
    # DETECT CATEGORY
    # ------------------------------------------------------

    for category, keywords in categories.items():

        for keyword in keywords:

            if keyword in text:

                return category

    # ------------------------------------------------------
    # DEFAULT
    # ------------------------------------------------------

    return "general"


# ==========================================================
# CATEGORY VISUAL STYLE
# ==========================================================

def get_category_style(
    category
):

    styles = {

        # --------------------------------------------------
        # SPACE
        # --------------------------------------------------

        "space": (
            "cinematic space photography, "
            "deep cosmic atmosphere, "
            "dramatic sunlight, "
            "realistic"
        ),

        # --------------------------------------------------
        # SLEEP
        # --------------------------------------------------

        "sleep": (
            "cinematic peaceful bedroom, "
            "soft nighttime lighting, "
            "realistic photography"
        ),

        # --------------------------------------------------
        # EXERCISE
        # --------------------------------------------------

        "exercise": (
            "cinematic fitness photography, "
            "dynamic athletic environment, "
            "dramatic lighting"
        ),

        # --------------------------------------------------
        # FOOD
        # --------------------------------------------------

        "food": (
            "cinematic food photography, "
            "fresh ingredients, "
            "natural lighting, "
            "realistic"
        ),

        # --------------------------------------------------
        # READING
        # --------------------------------------------------

        "reading": (
            "cinematic educational photography, "
            "books and learning environment, "
            "warm realistic lighting"
        ),

        # --------------------------------------------------
        # GRATITUDE
        # --------------------------------------------------

        "gratitude": (
            "cinematic emotional lifestyle photography, "
            "warm natural lighting, "
            "positive atmosphere"
        ),

        # --------------------------------------------------
        # TECHNOLOGY
        # --------------------------------------------------

        "technology": (
            "cinematic futuristic technology, "
            "modern digital environment, "
            "blue atmospheric lighting, "
            "realistic"
        ),

        # --------------------------------------------------
        # MONEY
        # --------------------------------------------------

        "money": (
            "cinematic financial photography, "
            "modern finance environment, "
            "dramatic golden lighting, "
            "realistic"
        ),

        # --------------------------------------------------
        # GENERAL
        # --------------------------------------------------

        "general": (
            "cinematic realistic photography, "
            "professional documentary style, "
            "dramatic lighting"
        ),
    }

    return styles.get(
        category,
        styles["general"]
    )


# ==========================================================
# NEGATIVE PROMPT
# ==========================================================

def get_negative_prompt(
    category
):

    base = (
        "blurry, low quality, "
        "distorted, deformed, "
        "bad anatomy, extra limbs, "
        "duplicate objects, "
        "text, watermark, logo, "
        "UI, cartoon, oversaturated"
    )

    # ------------------------------------------------------
    # SPACE
    # ------------------------------------------------------

    if category == "space":

        return (
            base
            + ", unrealistic planet, "
            "flat lighting"
        )

    # ------------------------------------------------------
    # MONEY
    # ------------------------------------------------------

    if category == "money":

        return (
            base
            + ", fake currency, "
            "messy composition"
        )

    # ------------------------------------------------------
    # TECHNOLOGY
    # ------------------------------------------------------

    if category == "technology":

        return (
            base
            + ", broken computer, "
            "messy cables"
        )

    return base


# ==========================================================
# CLEAN PROMPT
# ==========================================================

def clean_prompt(
    text,
    max_words=MAX_PROMPT_WORDS
):

    text = str(
        text or ""
    ).strip()

    # ------------------------------------------------------
    # REMOVE NEWLINES
    # ------------------------------------------------------

    text = text.replace(
        "\n",
        " "
    )

    # ------------------------------------------------------
    # REMOVE EXTRA SPACES
    # ------------------------------------------------------

    text = " ".join(
        text.split()
    )

    # ------------------------------------------------------
    # LIMIT WORD COUNT
    # ------------------------------------------------------

    words = text.split()

    if len(words) > max_words:

        text = " ".join(
            words[:max_words]
        )

    return text


# ==========================================================
# BUILD SHORT AI PROMPT
# ==========================================================

def build_scene_prompt(
    description,
    category,
    scene_number
):

    style = get_category_style(
        category
    )

    # ------------------------------------------------------
    # KEEP DESCRIPTION SHORT
    # ------------------------------------------------------

    description = clean_prompt(
        description,
        32
    )

    # ------------------------------------------------------
    # CAMERA STYLE
    #
    # NOTE:
    # This affects the AI-generated image composition,
    # NOT the FFmpeg camera movement.
    # ------------------------------------------------------

    camera_styles = [

        "wide cinematic shot",

        "dramatic close-up",

        "medium cinematic shot",

        "dynamic perspective",

        "cinematic low angle",

        "cinematic aerial perspective",

    ]

    camera = camera_styles[
        (scene_number - 1)
        % len(camera_styles)
    ]

    # ------------------------------------------------------
    # BUILD PROMPT
    # ------------------------------------------------------

    prompt = (
        f"{style}, "
        f"{camera}, "
        f"{description}, "
        "vertical composition, "
        "strong subject separation, "
        "dramatic depth, "
        "photorealistic, "
        "high detail"
    )

    # ------------------------------------------------------
    # FINAL CLEAN
    # ------------------------------------------------------

    return clean_prompt(
        prompt,
        MAX_PROMPT_WORDS
    )


# ==========================================================
# CREATE AI IMAGE
# ==========================================================

def generate_ai_image(
    description,
    scene_number
):

    pipeline = get_pipeline()

    description = str(
        description or ""
    ).strip()

    # ------------------------------------------------------
    # CATEGORY
    # ------------------------------------------------------

    category = detect_scene_category(
        description
    )

    # ------------------------------------------------------
    # PROMPT
    # ------------------------------------------------------

    prompt = build_scene_prompt(
        description,
        category,
        scene_number
    )

    # ------------------------------------------------------
    # NEGATIVE PROMPT
    # ------------------------------------------------------

    negative_prompt = get_negative_prompt(
        category
    )

    # ------------------------------------------------------
    # OUTPUT
    # ------------------------------------------------------

    output_file = (
        AI_SCENES_DIR
        / f"scene_{scene_number}.png"
    )

    # ======================================================
    # INFORMATION
    # ======================================================

    print()
    print("=" * 60)
    print("GENERATING AI SCENE IMAGE")
    print("=" * 60)

    print(
        "Scene:",
        scene_number
    )

    print(
        "Category:",
        category
    )

    print(
        "Description:",
        description
    )

    print()
    print(
        "Optimized Prompt:"
    )

    print(
        prompt
    )

    print()
    print(
        "Prompt words:",
        len(prompt.split())
    )

    # ======================================================
    # RANDOM SEED
    # ======================================================

    generator = None

    if DEVICE == "cuda":

        generator = torch.Generator(
            device="cuda"
        ).manual_seed(
            random.randint(
                1,
                2_000_000_000
            )
        )

    # ======================================================
    # GENERATE IMAGE
    # ======================================================

    with torch.inference_mode():

        if generator is not None:

            result = pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=IMAGE_WIDTH,
                height=IMAGE_HEIGHT,
                num_inference_steps=INFERENCE_STEPS,
                guidance_scale=GUIDANCE_SCALE,
                generator=generator,
            )

        else:

            result = pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=IMAGE_WIDTH,
                height=IMAGE_HEIGHT,
                num_inference_steps=INFERENCE_STEPS,
                guidance_scale=GUIDANCE_SCALE,
            )

        image = result.images[0]

    # ======================================================
    # SAVE
    # ======================================================

    image.save(
        output_file
    )

    # ======================================================
    # VERIFY
    # ======================================================

    if not output_file.exists():

        raise RuntimeError(
            f"AI image for scene "
            f"{scene_number} was not created."
        )

    if output_file.stat().st_size == 0:

        raise RuntimeError(
            f"AI image for scene "
            f"{scene_number} is empty."
        )

    # ======================================================
    # INFORMATION
    # ======================================================

    print()
    print(
        f"AI image created: "
        f"{output_file.resolve()}"
    )

    print(
        f"Image size: "
        f"{output_file.stat().st_size / 1024:.2f} KB"
    )

    return str(
        output_file.resolve()
    )


# ==========================================================
# MOTION FILTERS
# ==========================================================

def get_motion_filter(motion_type):
    """
    Returns FFmpeg zoompan filter expressions (zoom_expr, x_expr, y_expr)
    based on the requested camera motion.
    """
    m = str(motion_type or "").lower().strip()

    if m == "zoom_out":
        zoom_expr = f"max({MAX_ZOOM}-on*0.0004, 1.0)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    elif m == "pan_left":
        zoom_expr = "1.12"
        x_expr = "(iw-iw/zoom)*(1-min(on/150, 1.0))"
        y_expr = "ih/2-(ih/zoom/2)"
    elif m == "pan_right":
        zoom_expr = "1.12"
        x_expr = "(iw-iw/zoom)*(min(on/150, 1.0))"
        y_expr = "ih/2-(ih/zoom/2)"
    elif m == "pan_up":
        zoom_expr = "1.12"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "(ih-ih/zoom)*(1-min(on/150, 1.0))"
    elif m == "zoom_burst":
        zoom_expr = "min(1.0+on*0.0015, 1.25)"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"
    else:  # zoom_in default
        zoom_expr = f"min(zoom+{ZOOM_SPEED},{MAX_ZOOM})"
        x_expr = "iw/2-(iw/zoom/2)"
        y_expr = "ih/2-(ih/zoom/2)"

    return zoom_expr, x_expr, y_expr


# ==========================================================
# GRAPHIC STAT CARD GENERATOR
# ==========================================================

def generate_graphic_stat_card(
    scene_number,
    emphasis_keyword,
    text=""
):
    """
    Generates a high-impact, Reel-styled graphic stat card for scenes
    requiring data visualization or kinetic card display.
    """
    output_file = (
        AI_SCENES_DIR
        / f"scene_{scene_number}.png"
    )

    width = 1080
    height = 1920

    image = Image.new("RGB", (width, height), color=(13, 15, 23))
    draw = ImageDraw.Draw(image)

    # Accent decorative box frame
    margin = 60
    draw.rectangle(
        [margin, margin, width - margin, height - margin],
        outline=(0, 229, 255),
        width=6
    )

    def load_font(size):
        lang_code = ""
        if user_intent and isinstance(user_intent, dict):
            lang_code = user_intent.get("language_code", "")
        
        font_paths = []
        if lang_code in ("te", "hi", "ta", "kn", "ml", "mr", "bn", "gu", "pa"):
            font_paths = [
                "C:\\Windows\\Fonts\\NirmalaB.ttf",
                "C:\\Windows\\Fonts\\Nirmala.ttf",
                "C:\\Windows\\Fonts\\gautami.ttf",
                "C:\\Windows\\Fonts\\mangal.ttf"
            ]
        else:
            font_paths = [
                "C:\\Windows\\Fonts\\segoeui.ttf",
                "C:\\Windows\\Fonts\\arial.ttf",
                "C:\\Windows\\Fonts\\Nirmala.ttf"
            ]

        for path in font_paths:
            if Path(path).exists():
                try:
                    return ImageFont.truetype(path, size)
                except Exception:
                    pass
        return ImageFont.load_default()

    font_tag = load_font(40)
    font_keyword = load_font(90)
    font_text = load_font(42)

    # Top tag
    draw.text((width // 2, 450), "[ KEY INSIGHT ]", fill=(0, 229, 255), font=font_tag, anchor="mm")

    # Emphasis keyword
    keyword_text = str(emphasis_keyword or "INFO").strip().upper()
    if len(keyword_text) > 25:
        keyword_text = keyword_text[:25]
    draw.text((width // 2, 750), keyword_text, fill=(255, 215, 0), font=font_keyword, anchor="mm")

    # Descriptive text
    if text:
        words = str(text).split()
        lines = []
        curr = []
        for w in words:
            curr.append(w)
            if len(" ".join(curr)) > 28:
                lines.append(" ".join(curr))
                curr = []
        if curr:
            lines.append(" ".join(curr))

        y = 1100
        for l in lines[:5]:
            draw.text((width // 2, y), l, fill=(240, 240, 240), font=font_text, anchor="mm")
            y += 65

    image.save(output_file)
    print(f"Generated graphic stat card for scene {scene_number}: {output_file}")
    return str(output_file.resolve())


# ==========================================================
# CREATE VIDEO FROM AI IMAGE OR GRAPHIC CARD
# ==========================================================

def create_visual_scene(
    output_path,
    duration,
    scene_number,
    visual_description="",
    motion_type="zoom_in",
    visual_type="cinematic_broll",
    emphasis_keyword="",
    text="",
    topic="",
    user_intent=None,
    use_avatar=False
):

    output_file = Path(
        output_path
    ).resolve()

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # ======================================================
    # DURATION
    # ======================================================

    try:

        duration = float(
            duration
        )

    except (
        TypeError,
        ValueError
    ):

        duration = 5.0

    duration = max(
        duration,
        1.0
    )

    # ======================================================
    # INFORMATION
    # ======================================================

    print()
    print("=" * 60)
    print("CREATING AI VISUAL SCENE")
    print("=" * 60)

    print("Scene:", scene_number)
    print("Duration:", duration)
    print("Visual Type:", visual_type)
    print("Motion Type:", motion_type)
    print("Emphasis Keyword:", emphasis_keyword)
    print("Description:", visual_description)

    # ======================================================
    # GENERATE AUTHENTIC VISUAL, STAT CARD, OR AI IMAGE
    # ======================================================

    retrieval_res = get_authentic_scene_visual(
        scene_number=scene_number,
        scene_text=text or visual_description,
        visual_description=visual_description,
        topic=topic,
        user_intent=user_intent
    )

    if retrieval_res and retrieval_res.get("is_authentic") and Path(retrieval_res["image_path"]).exists():

        image_file = retrieval_res["image_path"]
        print(f"AUTHENTIC PHOTOGRAPH LOADED for Scene {scene_number}: {retrieval_res.get('source_url')}")

    elif visual_type in ("data_stat", "kinetic_card"):

        image_file = generate_graphic_stat_card(
            scene_number=scene_number,
            emphasis_keyword=emphasis_keyword,
            text=text or visual_description
        )

    else:

        image_file = generate_ai_image(
            visual_description,
            scene_number
        )

    image_file = Path(
        image_file
    ).resolve()

    # Overlay Presenter Avatar if requested or if face is active
    should_avatar = use_avatar or (user_intent and user_intent.get("use_avatar"))
    if should_avatar:
        print(f"OVERLAYING DIGITAL AVATAR onto authentic background for Scene {scene_number}...")
        overlay_presenter_avatar(
            background_image_path=str(image_file),
            output_image_path=str(image_file),
            scene_number=scene_number,
            is_speaking=True
        )

    # ======================================================
    # FFMPEG
    # ======================================================

    ffmpeg = get_ffmpeg()

    # ======================================================
    # DYNAMIC MOTION FILTER
    # ======================================================

    zoom_expression, x_expression, y_expression = get_motion_filter(motion_type)

    # ======================================================
    # VIDEO FILTER
    # ======================================================

    filter_complex = (

        "[0:v]"

        # --------------------------------------------------
        # SCALE IMAGE
        # --------------------------------------------------

        "scale="
        f"{VIDEO_WIDTH}:"
        f"{VIDEO_HEIGHT}:"
        "force_original_aspect_ratio=increase,"

        # --------------------------------------------------
        # CENTER CROP
        # --------------------------------------------------

        "crop="
        f"{VIDEO_WIDTH}:"
        f"{VIDEO_HEIGHT},"

        # --------------------------------------------------
        # DYNAMIC MOTION (ZOOM / PAN)
        # --------------------------------------------------

        "zoompan="

        f"z='{zoom_expression}':"

        f"x='{x_expression}':"

        f"y='{y_expression}':"

        "d=1:"

        f"s={VIDEO_WIDTH}x{VIDEO_HEIGHT}:"

        f"fps={VIDEO_FPS}"

        "[v]"
    )

    # ======================================================
    # FFMPEG COMMAND
    # ======================================================

    command = [

        ffmpeg,

        "-y",

        "-hide_banner",

        "-loglevel",
        "error",

        # --------------------------------------------------
        # LOOP IMAGE
        # --------------------------------------------------

        "-loop",
        "1",

        "-i",
        str(image_file),

        # --------------------------------------------------
        # VIDEO FILTER
        # --------------------------------------------------

        "-filter_complex",
        filter_complex,

        # --------------------------------------------------
        # MAP VIDEO
        # --------------------------------------------------

        "-map",
        "[v]",

        # --------------------------------------------------
        # DURATION
        # --------------------------------------------------

        "-t",
        str(duration),

        # --------------------------------------------------
        # FPS
        # --------------------------------------------------

        "-r",
        str(VIDEO_FPS),

        # --------------------------------------------------
        # NO AUDIO
        # --------------------------------------------------

        "-an",

        # --------------------------------------------------
        # VIDEO CODEC
        # --------------------------------------------------

        "-c:v",
        "libx264",

        # --------------------------------------------------
        # ENCODING SPEED
        # --------------------------------------------------

        "-preset",
        "medium",

        # --------------------------------------------------
        # QUALITY
        # --------------------------------------------------

        "-crf",
        "23",

        # --------------------------------------------------
        # COMPATIBLE PIXEL FORMAT
        # --------------------------------------------------

        "-pix_fmt",
        "yuv420p",

        # --------------------------------------------------
        # STREAMING FRIENDLY
        # --------------------------------------------------

        "-movflags",
        "+faststart",

        # --------------------------------------------------
        # OUTPUT
        # --------------------------------------------------

        str(output_file),
    ]

    # ======================================================
    # INFORMATION
    # ======================================================

    print()
    print("Motion pattern:", motion_type)
    print("Rendering scene video...")

    # ======================================================
    # RUN FFMPEG
    # ======================================================

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    # ======================================================
    # ERROR
    # ======================================================

    if result.returncode != 0:

        print()
        print("=" * 60)
        print("FFMPEG AI SCENE ERROR")
        print("=" * 60)

        if result.stderr:

            print(
                result.stderr
            )

        raise RuntimeError(
            f"AI visual scene "
            f"{scene_number} failed."
        )

    # ======================================================
    # VERIFY OUTPUT
    # ======================================================

    if not output_file.exists():

        raise RuntimeError(
            "FFmpeg completed but AI "
            "scene video was not created."
        )

    file_size = (
        output_file.stat().st_size
    )

    if file_size == 0:

        raise RuntimeError(
            "Generated AI scene video "
            "is empty."
        )

    # ======================================================
    # GPU MEMORY CLEANUP
    # ======================================================

    if DEVICE == "cuda":

        torch.cuda.empty_cache()

    gc.collect()

    # ======================================================
    # SUCCESS
    # ======================================================

    print()
    print("=" * 60)
    print("AI VISUAL SCENE SUCCESS")
    print("=" * 60)

    print(
        "Video:",
        output_file
    )

    print(
        f"Video size: "
        f"{file_size / (1024 * 1024):.2f} MB"
    )

    return str(
        output_file
    )


# ==========================================================
# GENERATE ALL SCENE VIDEOS
# ==========================================================

def generate_all_scene_videos(
    scenes,
    output_directory=None
):

    if not scenes:

        raise ValueError(
            "No scenes were provided."
        )

    # ------------------------------------------------------
    # OUTPUT DIRECTORY
    # ------------------------------------------------------

    if output_directory is None:

        output_directory = (
            SCENES_DIR
        )

    output_directory = Path(
        output_directory
    ).resolve()

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    # ======================================================
    # INFORMATION
    # ======================================================

    print()
    print("=" * 60)
    print("VYRA AI SCENE GENERATION")
    print("=" * 60)

    print(
        "Total scenes:",
        len(scenes)
    )

    print(
        "Camera:",
        "SLOW CENTERED ZOOM"
    )

    # ======================================================
    # SCENE FILES
    # ======================================================

    scene_files = []

    # ======================================================
    # GENERATE EACH SCENE
    # ======================================================

    for index, scene in enumerate(
        scenes,
        start=1
    ):

        print()
        print("-" * 60)
        print(
            f"GENERATING SCENE {index}"
        )
        print("-" * 60)

        # --------------------------------------------------
        # DICTIONARY SCENE
        # --------------------------------------------------

        if isinstance(
            scene,
            dict
        ):

            duration = scene.get(
                "duration",
                5
            )

            description = scene.get(
                "visual_description",
                scene.get(
                    "visual",
                    scene.get(
                        "visual_prompt",
                        scene.get(
                            "description",
                            scene.get(
                                "text",
                                ""
                            )
                        )
                    )
                )
            )

        # --------------------------------------------------
        # STRING SCENE
        # --------------------------------------------------

        else:

            duration = 5

            description = str(
                scene
            )

        # --------------------------------------------------
        # OUTPUT FILE
        # --------------------------------------------------

        output_path = (
            output_directory
            / f"scene_{index}.mp4"
        )

        # --------------------------------------------------
        # REMOVE OLD FILE
        # --------------------------------------------------

        if output_path.exists():

            try:

                output_path.unlink()

            except PermissionError as error:

                raise RuntimeError(
                    f"Cannot replace scene file "
                    f"because it is being used "
                    f"by another program:\n"
                    f"{output_path}"
                ) from error

        # --------------------------------------------------
        # CREATE VIDEO
        # --------------------------------------------------

        scene_file = create_visual_scene(

            output_path=output_path,

            duration=duration,

            scene_number=index,

            visual_description=description

        )

        # --------------------------------------------------
        # STORE FILE
        # --------------------------------------------------

        scene_files.append(
            scene_file
        )

    # ======================================================
    # COMPLETE
    # ======================================================

    print()
    print("=" * 60)
    print("ALL AI SCENE VIDEOS GENERATED")
    print("=" * 60)

    print(
        "Total scenes:",
        len(scene_files)
    )

    for index, scene_file in enumerate(
        scene_files,
        start=1
    ):

        print(
            f"Scene {index}: {scene_file}"
        )

    return scene_files


# ==========================================================
# COMPATIBILITY ALIAS
# ==========================================================

generate_scene_videos = (
    generate_all_scene_videos
)