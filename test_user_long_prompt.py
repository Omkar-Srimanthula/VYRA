import os
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')

# Set FFmpeg DLL path
ffmpeg_shared_dir = Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Packages"
for p in ffmpeg_shared_dir.rglob("avcodec-*.dll"):
    try:
        os.add_dll_directory(str(p.parent))
        os.environ["PATH"] = str(p.parent) + os.pathsep + os.environ.get("PATH", "")
        break
    except Exception:
        pass

from fastapi.testclient import TestClient
from main import app, STORAGE_DIR

print("=" * 60)
print("TESTING USER PROMPT FOR CHANDRAYAAN-3")
print("=" * 60)

client = TestClient(app)

user_prompt = (
    "Create a 60-sec Telugu video about Chandrayaan-3. Research and verify facts from reliable sources. "
    "Use authentic ISRO/official real photos and footage wherever possible—never generate fake realistic images "
    "of the spacecraft, Moon landing, people, or events. Use AI graphics only for explanations. "
    "Match visuals to narration, add English subtitles, and include sources/credits."
)

start_time = time.time()
print("\nSubmitting request to /api/create-video...")
res = client.post("/api/create-video", json={
    "topic": user_prompt,
    "language": "english",
    "duration": 20
})

print(f"Response status: {res.status_code}")
assert res.status_code == 200, f"Failed: {res.text}"
data = res.json()
print("\nResponse payload:")
print(f"  - Success: {data.get('success')}")
print(f"  - Topic Extracted: {data.get('topic')}")
print(f"  - Research Sources Count: {len(data.get('research_sources', []))}")
for s in data.get('research_sources', []):
    print(f"      * {s.get('title')}: {s.get('url')}")
print(f"  - Fact-Check Accuracy: {data.get('fact_check_accuracy')}")
print(f"  - Quality Control Passed: {data.get('quality_control_passed')}")

final_mp4 = STORAGE_DIR / "final_video.mp4"
assert final_mp4.exists(), "Final video file missing!"
size_mb = final_mp4.stat().st_size / (1024 * 1024)
print(f"\nFinal Video File: {final_mp4.resolve()}")
print(f"Size: {size_mb:.2f} MB")
assert size_mb > 0.5, "Video file is empty!"

print(f"\nCOMPLETED IN {time.time() - start_time:.2f} SECONDS WITH 100% SUCCESS!")
