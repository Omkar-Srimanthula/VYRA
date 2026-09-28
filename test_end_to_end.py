import os
import sys
import time
from pathlib import Path
from fastapi.testclient import TestClient

from main import app, STORAGE_DIR, get_ffmpeg

def print_header(title):
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

print_header("VYRA END-TO-END AUTOMATED TEST")

client = TestClient(app)

# 1. Health check
print("\n[TEST 1] Checking /api/health...")
res = client.get("/api/health")
assert res.status_code == 200, f"Health check failed: {res.text}"
data = res.json()
print("Health status:", data)
assert data["success"] is True

# 2. Voice status
print("\n[TEST 2] Checking /api/voice/status...")
res = client.get("/api/voice/status")
assert res.status_code == 200
voice_data = res.json()
print("Voice status:", voice_data)
assert voice_data["voice_available"] is True, "Voice sample not available!"

# 3. Generate script test
print("\n[TEST 3] Testing /api/generate-script...")
topic = "Artificial intelligence in modern medicine"
res = client.post("/api/generate-script", json={
    "topic": topic,
    "language": "english",
    "duration": 15
})
assert res.status_code == 200, f"Script generation failed: {res.text}"
script_data = res.json()
print("Generated script:", script_data.get("script"))
assert len(script_data.get("script", "")) > 10

# 4. End-to-end video creation
print("\n[TEST 4] Testing /api/create-video (Real End-to-End)...")
start_time = time.time()
res = client.post("/api/create-video", json={
    "topic": topic,
    "script": script_data.get("script"),
    "language": "english",
    "duration": 15,
    "style": "educational"
})
assert res.status_code == 200, f"Video creation failed: {res.text}"
video_res = res.json()
print("Video creation result:", video_res)
assert video_res["success"] is True

# 5. Verify final MP4 output
print("\n[TEST 5] Verifying output MP4 file...")
final_mp4 = STORAGE_DIR / "final_video.mp4"
assert final_mp4.exists(), "final_video.mp4 does not exist!"
size_bytes = final_mp4.stat().st_size
print(f"Final MP4 file: {final_mp4}")
print(f"Size: {size_bytes / (1024 * 1024):.2f} MB ({size_bytes:,} bytes)")
assert size_bytes > 100_000, "Final MP4 file is too small!"

# 6. Check FFprobe metadata for video and audio streams
import subprocess
ffmpeg = get_ffmpeg()
ffprobe = Path(ffmpeg).with_name("ffprobe.exe")

cmd = [
    str(ffprobe),
    "-v", "error",
    "-show_entries", "stream=codec_type,width,height,duration",
    "-of", "json",
    str(final_mp4)
]
probe_res = subprocess.run(cmd, capture_output=True, text=True)
print("FFprobe streams output:")
print(probe_res.stdout)
assert probe_res.returncode == 0

elapsed = time.time() - start_time
print_header(f"END-TO-END TEST COMPLETED SUCCESSFULLY IN {elapsed:.2f} SECONDS!")
