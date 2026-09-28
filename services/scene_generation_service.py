from pathlib import Path

from .visual_service import create_visual_scene


# ==========================================================
# PROJECT PATHS
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

STORAGE_DIR = BASE_DIR / "storage"

SCENES_DIR = STORAGE_DIR / "scenes"


# ==========================================================
# FOLDER SETUP
# ==========================================================

STORAGE_DIR.mkdir(
    parents=True,
    exist_ok=True
)

SCENES_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ==========================================================
# GET SCENE VISUAL DESCRIPTION
# ==========================================================

def get_scene_visual(scene):
    """
    Get the best available visual description.

    VYRA scenes may contain:
        visual
        visual_prompt
        visual_description
        description

    This function supports all of them.
    """

    possible_fields = [
        "visual_description",
        "visual",
        "visual_prompt",
        "description"
    ]

    for field in possible_fields:

        value = scene.get(
            field,
            ""
        )

        if value:

            value = str(
                value
            ).strip()

            if value:
                return value

    # Final fallback

    text = str(
        scene.get(
            "text",
            ""
        )
    ).strip()

    if text:

        return (
            "Cinematic vertical motivational "
            "lifestyle scene representing: "
            + text
        )

    return (
        "Cinematic vertical motivational "
        "lifestyle scene showing positive "
        "personal development."
    )


# ==========================================================
# GET SCENE DURATION
# ==========================================================

def get_scene_duration(scene):
    """
    Safely retrieve scene duration.
    """

    try:

        duration = float(
            scene.get(
                "duration",
                5.0
            )
        )

    except (
        TypeError,
        ValueError
    ):

        duration = 5.0

    # Prevent extremely short scenes

    duration = max(
        duration,
        3.0
    )

    return round(
        duration,
        1
    )


# ==========================================================
# GENERATE ALL SCENE VIDEOS
# ==========================================================

def generate_all_scene_videos(scenes, topic="", user_intent=None, use_avatar=False):
    """
    Generate a separate MP4 video for every scene.
    """

    if not scenes:

        raise ValueError(
            "No scenes were provided."
        )

    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    SCENES_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    scene_files = []

    print()
    print("=" * 48)
    print("GENERATING ALL SCENE VIDEOS")
    print("=" * 48)

    print(
        f"Total scenes to generate: {len(scenes)}"
    )

    # ======================================================
    # GENERATE EACH SCENE
    # ======================================================

    for scene in scenes:

        # --------------------------------------------------
        # SCENE NUMBER
        # --------------------------------------------------

        try:

            scene_number = int(
                scene.get(
                    "scene_number",
                    len(scene_files) + 1
                )
            )

        except (
            TypeError,
            ValueError
        ):

            scene_number = (
                len(scene_files) + 1
            )

        # --------------------------------------------------
        # DURATION
        # --------------------------------------------------

        duration = get_scene_duration(
            scene
        )

        # --------------------------------------------------
        # VISUAL DESCRIPTION
        # --------------------------------------------------

        visual_description = (
            get_scene_visual(
                scene
            )
        )

        # --------------------------------------------------
        # OUTPUT
        # --------------------------------------------------

        output_file = (
            STORAGE_DIR
            / f"scene_{scene_number}.mp4"
        )

        # --------------------------------------------------
        # DISPLAY INFORMATION
        # --------------------------------------------------

        print()
        print("=" * 40)
        print(
            f"SCENE {scene_number}"
        )
        print("=" * 40)

        print(
            f"Duration: {duration} seconds"
        )

        print(
            f"Visual: {visual_description}"
        )

        # --------------------------------------------------
        # REMOVE OLD SCENE
        # --------------------------------------------------

        if output_file.exists():

            try:

                output_file.unlink()

                print(
                    "Removed previous scene file."
                )

            except Exception as error:

                raise RuntimeError(
                    f"Could not remove old scene "
                    f"{scene_number}: {error}"
                )

        # ==================================================
        # CREATE VISUAL SCENE
        # ==================================================

        motion_type = scene.get("motion_type", "zoom_in")
        visual_type = scene.get("visual_type", "cinematic_broll")
        emphasis_keyword = scene.get("emphasis_keyword", "")
        text = scene.get("text", "")

        create_visual_scene(
            str(output_file),
            duration,
            scene_number,
            visual_description,
            motion_type=motion_type,
            visual_type=visual_type,
            emphasis_keyword=emphasis_keyword,
            text=text,
            topic=topic,
            user_intent=user_intent,
            use_avatar=use_avatar
        )

        # ==================================================
        # VERIFY OUTPUT
        # ==================================================

        if not output_file.exists():

            raise RuntimeError(
                f"Scene {scene_number} "
                f"was not created."
            )

        if output_file.stat().st_size == 0:

            raise RuntimeError(
                f"Scene {scene_number} "
                f"is empty."
            )

        # --------------------------------------------------
        # SAVE
        # --------------------------------------------------

        scene_files.append(
            str(
                output_file.resolve()
            )
        )

        print(
            f"Scene {scene_number} completed."
        )

        print(
            f"File: {output_file.resolve()}"
        )

        print(
            f"Size: "
            f"{output_file.stat().st_size / (1024 * 1024):.2f} MB"
        )

    # ======================================================
    # COMPLETE
    # ======================================================

    print()
    print("=" * 48)
    print("ALL SCENE VIDEOS GENERATED")
    print("=" * 48)

    print(
        f"Total scenes: {len(scene_files)}"
    )

    total_size = 0

    for file in scene_files:

        path = Path(file)

        if path.exists():

            total_size += (
                path.stat().st_size
            )

    print(
        f"Total scene size: "
        f"{total_size / (1024 * 1024):.2f} MB"
    )

    return scene_files