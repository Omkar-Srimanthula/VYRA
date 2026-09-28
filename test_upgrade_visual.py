import os
import sys
import time
from pathlib import Path

# Ensure UTF-8 output encoding for Windows terminal
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Ensure Windows FFmpeg DLL directory is set before loading torch/TTS modules
ffmpeg_shared_dir = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
for p in ffmpeg_shared_dir.rglob("avcodec-*.dll"):
    os.add_dll_directory(str(p.parent))
    break

from services.scene_service import generate_scene_breakdown
from services.scene_generation_service import generate_all_scene_videos

print("=" * 60)
print("TESTING UPGRADED VISUAL PIPELINE")
print("=" * 60)

test_script = (
    "In 2026, artificial intelligence transformed global healthcare. "
    "Surgeons use AI-guided robotics for 99% precision during procedures. "
    "Over 50 million patient lives were saved this year alone."
)

print("\n1. Generating Content-Aware Scene Breakdown...")
scenes = generate_scene_breakdown(test_script)
print(f"Generated {len(scenes)} scenes:")
for i, scene in enumerate(scenes, 1):
    print(f"  Scene {i}: visual_type={scene.get('visual_type')}, motion_type={scene.get('motion_type')}, keyword={scene.get('emphasis_keyword')}")

print("\n2. Generating Scene Videos (Multi-motion + Graphic Cards)...")
start_time = time.time()
scene_files = generate_all_scene_videos(scenes)

print(f"\nCompleted in {time.time() - start_time:.2f} seconds.")
print("Generated files:")
for sf in scene_files:
    p = Path(sf)
    print(f"  - {p.name}: {p.stat().st_size / 1024:.1f} KB")

print("\nVISUAL PIPELINE TEST COMPLETED SUCCESSFULLY!")
