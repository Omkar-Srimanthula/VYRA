from pathlib import Path
from .visual_service import create_visual_scene


BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"


def generate_all_scene_videos(scenes):
    """
    Generate a video file for every scene.

    scenes must contain:
        scene_number
        duration
        narration
        visual_description
    """

    if not scenes:
        raise ValueError("No scenes were provided.")

    STORAGE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    scene_files = []

    print()
    print("=" * 48)
    print("GENERATING ALL SCENE VIDEOS")
    print("=" * 48)

    for scene in scenes:

        scene_number = int(
            scene["scene_number"]
        )

        duration = float(
            scene["duration"]
        )

        visual_description = str(
            scene.get(
                "visual_description",
                ""
            )
        ).strip()

        output_file = (
            STORAGE_DIR
            / f"scene_{scene_number}.mp4"
        )

        print()
        print(f"Scene {scene_number}")
        print(f"Duration: {duration} seconds")
        print(
            f"Visual: {visual_description}"
        )

        create_visual_scene(
            str(output_file),
            duration,
            scene_number,
            visual_description
        )

        if not output_file.exists():
            raise RuntimeError(
                f"Scene {scene_number} was not created."
            )

        scene_files.append(
            str(output_file)
        )

        print(
            f"Scene {scene_number} completed."
        )

    print()
    print("=" * 48)
    print("ALL SCENE VIDEOS GENERATED")
    print("=" * 48)

    print(
        f"Total scenes: {len(scene_files)}"
    )

    return scene_files