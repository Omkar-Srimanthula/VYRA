from pathlib import Path
import subprocess
import shutil


BASE_DIR = Path(__file__).resolve().parent.parent


# ==========================================================
# FIND FFMPEG
# ==========================================================

def get_ffmpeg():

    ffmpeg = shutil.which("ffmpeg")

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
            base_path.rglob("ffmpeg.exe")
        )

        if matches:
            return str(matches[0])

    raise FileNotFoundError(
        "FFmpeg was not found. "
        "Make sure FFmpeg is installed and available."
    )


# ==========================================================
# DETECT CATEGORY
# ==========================================================

def detect_scene_category(description):

    text = str(description or "").lower()

    categories = {

        "space": [
            "space", "planet", "planets", "galaxy",
            "galaxies", "universe", "cosmic", "cosmos",
            "star", "stars", "sun", "moon", "mars",
            "earth", "saturn", "jupiter", "nebula",
            "asteroid", "astronaut", "rocket",
            "solar system"
        ],

        "sleep": [
            "sleep", "sleeping", "bed", "bedroom",
            "wake", "waking", "morning", "rest"
        ],

        "exercise": [
            "exercise", "exercising", "workout",
            "gym", "running", "jogging", "fitness",
            "training", "sport"
        ],

        "food": [
            "food", "eat", "eating", "healthy",
            "vegetable", "vegetables", "cooking",
            "meal", "kitchen", "nutrition"
        ],

        "reading": [
            "read", "reading", "book", "books",
            "study", "studying", "library", "learning"
        ],

        "gratitude": [
            "gratitude", "grateful", "thank",
            "thanks", "smiling", "positive", "happy"
        ],

        "technology": [
            "computer", "technology", "phone",
            "laptop", "software", "ai",
            "artificial intelligence", "robot", "digital"
        ],

        "money": [
            "money", "wealth", "finance", "stock",
            "stocks", "crypto", "bitcoin", "trading",
            "investment"
        ],
    }

    for category, keywords in categories.items():

        for keyword in keywords:

            if keyword in text:
                return category

    return "general"


# ==========================================================
# CATEGORY SETTINGS
# ==========================================================

def get_category_settings(category):

    settings = {

        "space": {
            "accent": "38BDF8",
            "bg1": "020617",
            "bg2": "172554",
        },

        "sleep": {
            "accent": "60A5FA",
            "bg1": "050816",
            "bg2": "172554",
        },

        "exercise": {
            "accent": "22C55E",
            "bg1": "03140C",
            "bg2": "14532D",
        },

        "food": {
            "accent": "F59E0B",
            "bg1": "1A1002",
            "bg2": "78350F",
        },

        "reading": {
            "accent": "A78BFA",
            "bg1": "10061F",
            "bg2": "4C1D95",
        },

        "gratitude": {
            "accent": "F472B6",
            "bg1": "1D0713",
            "bg2": "831843",
        },

        "technology": {
            "accent": "38BDF8",
            "bg1": "031016",
            "bg2": "164E63",
        },

        "money": {
            "accent": "FACC15",
            "bg1": "151000",
            "bg2": "713F12",
        },

        "general": {
            "accent": "60A5FA",
            "bg1": "080812",
            "bg2": "1E3A5F",
        },
    }

    return settings.get(
        category,
        settings["general"]
    )


# ==========================================================
# CREATE VISUAL SCENE
# ==========================================================

def create_visual_scene(
    output_path,
    duration,
    scene_number,
    visual_description=""
):

    output_file = Path(output_path)

    output_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    ffmpeg = get_ffmpeg()

    # ------------------------------------------------------
    # VALIDATE DURATION
    # ------------------------------------------------------

    try:

        duration = float(duration)

    except (TypeError, ValueError):

        duration = 5.0

    duration = max(duration, 1.0)

    # ------------------------------------------------------
    # INFORMATION
    # ------------------------------------------------------

    print()
    print("========================================")
    print("CREATING VISUAL SCENE")
    print("========================================")

    print(f"Scene: {scene_number}")
    print(f"Duration: {duration} seconds")
    print(f"Description: {visual_description}")
    print(f"Output: {output_file.resolve()}")

    # ------------------------------------------------------
    # CATEGORY
    # ------------------------------------------------------

    category = detect_scene_category(
        visual_description
    )

    settings = get_category_settings(
        category
    )

    accent = settings["accent"]
    bg1 = settings["bg1"]
    bg2 = settings["bg2"]

    print(f"Category: {category}")

    # ======================================================
    # VISUAL DESIGN
    # ======================================================

    # IMPORTANT:
    #
    # We intentionally do NOT use drawtext here.
    #
    # This keeps the renderer Windows-safe.
    #
    # Text/subtitles will be handled separately.
    #

    filter_text = (
        f"color=c=#{bg1}:"
        f"s=1080x1920:"
        f"r=30,"
        
        f"drawbox="
        f"x=0:"
        f"y=0:"
        f"w=1080:"
        f"h=1920:"
        f"color=#{bg2}@0.30:"
        f"t=fill,"
        
        f"drawbox="
        f"x=180:"
        f"y=300:"
        f"w=720:"
        f"h=720:"
        f"color=#{accent}@0.08:"
        f"t=fill,"
        
        f"drawbox="
        f"x=0:"
        f"y=0:"
        f"w=1080:"
        f"h=14:"
        f"color=#{accent}:"
        f"t=fill,"
        
        f"drawbox="
        f"x=45:"
        f"y=220:"
        f"w=6:"
        f"h=1420:"
        f"color=#{accent}@0.65:"
        f"t=fill,"
        
        f"drawbox="
        f"x=75:"
        f"y=790:"
        f"w=930:"
        f"h=420:"
        f"color=black@0.32:"
        f"t=fill,"
        
        f"drawbox="
        f"x=90:"
        f"y=1710:"
        f"w=900:"
        f"h=7:"
        f"color=white@0.15:"
        f"t=fill,"
        
        f"drawbox="
        f"x=90:"
        f"y=1710:"
        f"w=900:"
        f"h=7:"
        f"color=#{accent}:"
        f"t=fill"
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

        "-f",
        "lavfi",

        "-i",
        filter_text,

        "-t",
        str(duration),

        "-r",
        "30",

        "-an",

        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "23",

        "-pix_fmt",
        "yuv420p",

        "-movflags",
        "+faststart",

        str(output_file),
    ]

    # ======================================================
    # RUN FFMPEG
    # ======================================================

    print()
    print("Running FFmpeg...")
    print()

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    # ======================================================
    # ERROR HANDLING
    # ======================================================

    if result.returncode != 0:

        print()
        print("========================================")
        print("FFMPEG VISUAL ERROR")
        print("========================================")

        print(result.stderr)

        raise RuntimeError(
            f"Visual scene {scene_number} failed."
        )

    # ======================================================
    # VERIFY OUTPUT
    # ======================================================

    if not output_file.exists():

        raise RuntimeError(
            "FFmpeg completed but output video "
            "was not created."
        )

    file_size = output_file.stat().st_size

    if file_size == 0:

        raise RuntimeError(
            "Generated visual video is empty."
        )

    # ======================================================
    # SUCCESS
    # ======================================================

    print()
    print("========================================")
    print("VISUAL SCENE SUCCESS")
    print("========================================")

    print(
        f"Visual scene created: "
        f"{output_file.resolve()}"
    )

    print(
        f"File size: "
        f"{file_size / (1024 * 1024):.2f} MB"
    )

    return str(
        output_file.resolve()
    )


# ==========================================================
# GENERATE ALL SCENES
# ==========================================================

def generate_all_scene_videos(
    scenes,
    output_directory=None
):

    if not scenes:

        raise ValueError(
            "No scenes were provided."
        )

    if output_directory is None:

        output_directory = (
            BASE_DIR / "storage"
        )

    output_directory = Path(
        output_directory
    )

    output_directory.mkdir(
        parents=True,
        exist_ok=True
    )

    print()
    print("================================================")
    print("GENERATING ALL SCENE VIDEOS")
    print("================================================")

    scene_files = []

    for index, scene in enumerate(
        scenes,
        start=1
    ):

        # --------------------------------------------------
        # READ SCENE DATA
        # --------------------------------------------------

        if isinstance(scene, dict):

            duration = scene.get(
                "duration",
                5
            )

            description = scene.get(
                "visual_description",
                scene.get(
                    "visual",
                    scene.get(
                        "description",
                        ""
                    )
                )
            )

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

        print()
        print(f"Scene {index}")
        print(f"Duration: {duration} seconds")
        print(f"Visual: {description}")

        # --------------------------------------------------
        # CREATE SCENE
        # --------------------------------------------------

        scene_file = create_visual_scene(
            output_path=output_path,
            duration=duration,
            scene_number=index,
            visual_description=description
        )

        scene_files.append(
            scene_file
        )

    # ------------------------------------------------------
    # COMPLETE
    # ------------------------------------------------------

    print()
    print("================================================")
    print("ALL SCENE VIDEOS GENERATED")
    print("================================================")

    print(
        f"Total scenes: {len(scene_files)}"
    )

    return scene_files