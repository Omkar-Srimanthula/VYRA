import json
import re
from typing import Any


# ==========================================================
# JSON EXTRACTION
# ==========================================================

def _extract_json(text: str) -> Any:
    if not text:
        return None

    text = str(text).strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass

    return None


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    text = str(text).replace("\r", " ").replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _split_sentences(script: str) -> list[str]:
    script = _normalize_text(script)
    if not script:
        return []
    parts = re.split(r"(?<=[.!?])\s+", script)
    return [part.strip() for part in parts if part.strip()]


def _split_long_sentence(text: str, max_words: int = 18) -> list[str]:
    words = text.split()
    if len(words) <= max_words:
        return [text.strip()]

    chunks = []
    current = []
    for word in words:
        current.append(word)
        if len(current) >= max_words:
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))

    return chunks


# ==========================================================
# VISUAL PROMPT GENERATOR Grounded in User Intent & Topic
# ==========================================================

def _create_visual_prompt(text: str, topic: str = "", user_intent: dict = None) -> str:
    """
    Dynamically generates scene visual descriptions grounded directly in the
    user's requested topic and scene narration text.
    """
    clean_text = _normalize_text(text)
    clean_topic = ""
    if user_intent and isinstance(user_intent, dict):
        clean_topic = user_intent.get("exact_topic") or user_intent.get("topic") or ""
    if not clean_topic and topic:
        clean_topic = str(topic).strip()

    if clean_topic:
        return (
            f"Cinematic vertical visual for topic '{clean_topic}' illustrating: {clean_text}. "
            f"Authentic subject imagery, 9:16 vertical video layout, professional media style."
        )

    return (
        f"Cinematic vertical visual illustrating: {clean_text}. "
        f"Authentic high-quality visual, 9:16 vertical format, professional documentary style."
    )


def _calculate_duration(text: str) -> float:
    words = len(text.split())
    duration = words / 2.5
    duration = max(duration, 3.0)
    duration = min(duration, 7.0)
    return round(duration, 1)


def _extract_emphasis_keyword(text: str) -> str:
    number_match = re.search(r'(\d+[\d,.]*\s*(?:%|lakh|crore|thousand|million|billion|years|min|sec|days|rupees|\$|₹|percent)?)', text, re.IGNORECASE)
    if number_match and len(number_match.group(1).strip()) >= 1:
        return number_match.group(1).strip().upper()

    words = text.split()
    clean_words = [re.sub(r'[^\w]', '', w) for w in words if len(re.sub(r'[^\w]', '', w)) > 3]
    if clean_words:
        return " ".join(clean_words[:2]).upper()

    return text[:20].upper() if text else "IMPORTANT"


def _determine_visual_type(text: str, scene_number: int) -> str:
    if scene_number == 1:
        return "hook"

    if re.search(r'\d+', text) or any(k in text.lower() for k in ["percent", "lakh", "crore", "dollar", "rupee", "number", "statistic", "%"]):
        return "data_stat"

    if len(text.split()) < 9 and any(k in text.lower() for k in ["important", "remember", "secret", "truth", "key", "fact", "never", "always", "why"]):
        return "kinetic_card"

    return "cinematic_broll"


def _determine_motion_type(scene_number: int, visual_type: str) -> str:
    if visual_type == "hook":
        return "zoom_burst"

    motions = ["zoom_in", "pan_left", "zoom_out", "pan_right", "pan_up"]
    return motions[(scene_number - 1) % len(motions)]


def _create_scene(
    scene_number: int,
    text: str,
    topic: str = "",
    user_intent: dict = None
) -> dict:

    text = _normalize_text(text)
    visual_type = _determine_visual_type(text, scene_number)
    motion_type = _determine_motion_type(scene_number, visual_type)
    emphasis_keyword = _extract_emphasis_keyword(text)
    visual_prompt = _create_visual_prompt(text, topic=topic, user_intent=user_intent)
    duration = _calculate_duration(text)

    return {
        "scene_number": scene_number,
        "text": text,
        "visual_type": visual_type,
        "motion_type": motion_type,
        "emphasis_keyword": emphasis_keyword,
        "visual": visual_prompt,
        "visual_prompt": visual_prompt,
        "visual_description": visual_prompt,
        "description": visual_prompt,
        "duration": duration,
    }


def generate_scene_breakdown(
    script: str,
    topic: str = "",
    user_intent: dict = None,
    *args,
    **kwargs
) -> list[dict]:
    """
    Converts a script into multiple visual scenes grounded in user intent and exact topic.
    """
    script = _normalize_text(script)
    if not script:
        return []

    sentences = _split_sentences(script)

    chunks = []
    for sentence in sentences:
        sentence_chunks = _split_long_sentence(sentence, max_words=18)
        chunks.extend(sentence_chunks)

    final_parts = []
    current = ""

    for chunk in chunks:
        chunk = chunk.strip()
        if not chunk:
            continue

        word_count = len(chunk.split())
        if word_count < 5:
            if current:
                current = current + " " + chunk
            else:
                current = chunk
            continue

        if current:
            final_parts.append(current)
            current = ""

        final_parts.append(chunk)

    if current:
        if final_parts:
            final_parts[-1] = final_parts[-1] + " " + current
        else:
            final_parts.append(current)

    scenes = []
    for index, text in enumerate(final_parts, start=1):
        scene = _create_scene(index, text, topic=topic, user_intent=user_intent)
        scenes.append(scene)

    if not scenes:
        scenes.append(_create_scene(1, script, topic=topic, user_intent=user_intent))

    if len(scenes) > 12:
        scenes = scenes[:12]

    for index, scene in enumerate(scenes, start=1):
        scene["scene_number"] = index

    print()
    print("========================================")
    print("SCENE BREAKDOWN (INTENT-GROUNDED)")
    print("========================================")
    print(f"Script length: {len(script.split())} words")
    print(f"Scenes created: {len(scenes)}")

    for scene in scenes:
        safe_text = str(scene['text']).encode('ascii', errors='replace').decode('ascii')
        safe_visual = str(scene['visual']).encode('ascii', errors='replace').decode('ascii')
        print(f"\nScene {scene['scene_number']} ({scene['duration']}s): {safe_text}")
        print(f"Visual: {safe_visual}")

    print("========================================")
    return scenes


def create_scene_breakdown(
    script: str,
    *args,
    **kwargs
) -> list[dict]:
    return generate_scene_breakdown(script, *args, **kwargs)