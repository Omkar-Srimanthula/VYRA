from pathlib import Path
import json
import requests
import re
from PIL import Image
import io

BASE_DIR = Path(__file__).resolve().parent.parent
STORAGE_DIR = BASE_DIR / "storage"
AI_SCENES_DIR = STORAGE_DIR / "ai_scenes"

STORAGE_DIR.mkdir(parents=True, exist_ok=True)
AI_SCENES_DIR.mkdir(parents=True, exist_ok=True)

REAL_SUBJECT_KEYWORDS = {
    "location": [
        "charminar", "everest", "mountain", "hyderabad", "taj mahal", "delhi", "mumbai",
        "india", "paris", "london", "new york", "moon", "mars", "earth", "sun", "jupiter",
        "saturn", "space station", "iss", "river", "ocean", "city", "building", "temple", "monument", "france"
    ],
    "person": [
        "musk", "elon", "modi", "kalam", "einstein", "jobs", "gates", "gandhi", "nehru",
        "president", "prime minister", "doctor", "scientist", "king", "queen", "author", "founder", "ceo", "napoleon"
    ],
    "event_mission": [
        "chandrayaan", "apollo", "mission", "launch", "landing", "war", "revolution",
        "independence", "olympics", "world cup", "speech", "ceremony", "discovery", "voyager", "french revolution"
    ],
    "organization_brand": [
        "isro", "nasa", "apple", "tesla", "google", "microsoft", "spacex", "un",
        "who", "railways", "army", "navy", "air force", "company", "university", "hospital"
    ],
    "science_nature": [
        "dna", "cell", "atom", "molecule", "telescope", "microscope", "virus", "galaxy",
        "nebula", "black hole", "volcano", "tsunami", "eclipse", "brain", "heart", "robotics", "quantum", "biryani"
    ]
}


def classify_scene_subject(scene_text: str, visual_description: str = "", topic: str = "", user_intent: dict = None) -> dict:
    """
    Determines if a scene refers to a real-world entity or an abstract concept / statistics,
    incorporating the user's primary topic and intent.
    """
    clean_topic = ""
    if user_intent and isinstance(user_intent, dict):
        clean_topic = user_intent.get("exact_topic", "")
    if not clean_topic and topic:
        clean_topic = str(topic).strip()

    combined = f"{scene_text} {visual_description} {clean_topic}".lower()

    # Quantitative stats check
    has_stat = bool(re.search(r'\b\d+(?:[\.,]\d+)?\b|percent|%|\$\d+|million|billion', scene_text))
    if has_stat and ("percent" in scene_text.lower() or "%" in scene_text or "$" in scene_text or "million" in scene_text or "lakh" in scene_text or "crore" in scene_text):
        return {
            "subject_category": "DATA_STATISTICS",
            "is_real_subject": False,
            "visual_strategy": "STAT_CARD",
            "reason": "Scene contains quantitative statistics/data."
        }

    # Match real-world keywords
    matched_categories = []
    for cat_name, keywords in REAL_SUBJECT_KEYWORDS.items():
        for kw in keywords:
            if kw in combined:
                matched_categories.append(cat_name)
                break

    if matched_categories:
        primary_cat = matched_categories[0].upper()
        return {
            "subject_category": f"REAL_{primary_cat}",
            "is_real_subject": True,
            "visual_strategy": "AUTHENTIC_RETRIEVAL",
            "reason": f"Scene/Topic matches real-world subject keyword in category '{primary_cat}'."
        }

    # Proper nouns check
    words = scene_text.split()
    proper_nouns = [w for i, w in enumerate(words) if i > 0 and w[0].isupper() and len(w) > 3]
    if len(proper_nouns) >= 1 or (clean_topic and len(clean_topic) > 3):
        return {
            "subject_category": "REAL_ENTITY",
            "is_real_subject": True,
            "visual_strategy": "AUTHENTIC_RETRIEVAL",
            "reason": f"Scene references real entity context for '{clean_topic or proper_nouns[0]}'."
        }

    return {
        "subject_category": "ABSTRACT_CONCEPT",
        "is_real_subject": False,
        "visual_strategy": "AI_GENERATION",
        "reason": "Scene depicts abstract concepts or general explanations."
    }


def search_wikimedia_commons_image(query: str) -> dict:
    clean_query = str(query or "").strip()
    if not clean_query:
        return {}

    url = "https://commons.wikimedia.org/w/api.php"
    params = {
        "action": "query",
        "generator": "search",
        "gsrsearch": f"{clean_query} filetype:bitmap",
        "gsrnamespace": 6,
        "gsrlimit": 5,
        "prop": "imageinfo",
        "iiprop": "url|extmetadata|mime",
        "format": "json"
    }
    headers = {"User-Agent": "VYRA-VisualEngine/2.5 (https://vyra.ai; vyra@example.com)"}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            pages = response.json().get("query", {}).get("pages", {})
            for page_id, page in pages.items():
                imageinfo = page.get("imageinfo", [{}])[0]
                img_url = imageinfo.get("url")
                extmetadata = imageinfo.get("extmetadata", {})

                if img_url and any(img_url.lower().endswith(ext) for ext in [".jpg", ".jpeg", ".png", ".webp"]):
                    license_name = extmetadata.get("LicenseShortName", {}).get("value", "Creative Commons / Public Domain")
                    artist = extmetadata.get("Artist", {}).get("value", "Wikimedia Contributor")
                    artist_clean = re.sub(r'<[^>]+>', '', artist).strip() or "Wikimedia Commons"

                    return {
                        "title": page.get("title", clean_query),
                        "url": img_url,
                        "license": license_name,
                        "artist": artist_clean,
                        "source_domain": "Wikimedia Commons",
                        "is_authentic": True
                    }
    except Exception as e:
        print(f"[Visual Retrieval Error] Wikimedia Commons search failed for '{clean_query}': {e}")

    return {}


def download_and_format_image(image_url: str, output_file: Path) -> bool:
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        r = requests.get(image_url, headers=headers, timeout=15)
        if r.status_code == 200 and len(r.content) > 5000:
            img = Image.open(io.BytesIO(r.content)).convert("RGB")
            img.save(output_file, "PNG")
            return True
    except Exception as e:
        print(f"[Image Download Error] Failed to download {image_url}: {e}")
    return False


def fetch_wikipedia_entity_image(entity_name: str) -> dict:
    clean_name = str(entity_name or "").strip()
    if not clean_name:
        return {}
    
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(clean_name)}"
    headers = {"User-Agent": "VYRA-VisualEngine/2.5 (https://vyra.ai)"}

    try:
        r = requests.get(url, headers=headers, timeout=8)
        if r.status_code == 200:
            data = r.json()
            img_url = data.get("originalimage", {}).get("source") or data.get("thumbnail", {}).get("source")
            if img_url:
                return {
                    "title": data.get("title", clean_name),
                    "url": img_url,
                    "license": "Wikipedia / Public Domain / CC",
                    "artist": "Wikipedia / Official Source",
                    "source_domain": "Wikipedia / Wikimedia",
                    "is_authentic": True
                }
    except Exception as e:
        print(f"[Wikipedia Image Error] Failed for '{clean_name}': {e}")
    return {}


def get_authentic_scene_visual(scene_number: int, scene_text: str, visual_description: str = "", topic: str = "", user_intent: dict = None) -> dict:
    """
    Main entry point for scene visual decision grounded in user intent & topic.
    """
    classification = classify_scene_subject(scene_text, visual_description, topic=topic, user_intent=user_intent)
    output_file = AI_SCENES_DIR / f"scene_{scene_number}.png"

    print()
    print("-" * 50)
    print(f"VISUAL SELECTION — SCENE {scene_number}")
    print("-" * 50)
    print(f"Category: {classification['subject_category']}")
    print(f"Strategy: {classification['visual_strategy']}")
    print(f"Reason:   {classification['reason']}")

    # Build search entities from scene text AND topic/user_intent
    combined_text = f"{scene_text} {visual_description}"
    entity_terms = []

    if user_intent and isinstance(user_intent, dict):
        if user_intent.get("exact_topic"):
            entity_terms.append(user_intent["exact_topic"])
        if user_intent.get("entities"):
            entity_terms.extend(user_intent["entities"])
    elif topic:
        entity_terms.append(str(topic).strip())

    # Extract scene-specific keywords
    for cat_name, keywords in REAL_SUBJECT_KEYWORDS.items():
        for kw in keywords:
            if kw in combined_text.lower():
                entity_terms.append(kw.capitalize())

    words = re.findall(r'\b[A-Z][a-z0-9]+\b', scene_text)
    if words:
        entity_terms.extend(words[:2])

    clean_entities = list(dict.fromkeys([e for e in entity_terms if len(str(e).strip()) > 2]))

    if classification["is_real_subject"] or clean_entities:
        # 1. Try direct Wikipedia Entity Image
        for entity in clean_entities:
            print(f"Checking official Wikipedia image for entity: '{entity}'...")
            wiki_media = fetch_wikipedia_entity_image(entity)
            if wiki_media and wiki_media.get("url"):
                success = download_and_format_image(wiki_media["url"], output_file)
                if success:
                    print(f"SUCCESS: Retrieved authentic photograph for '{entity}'!")
                    return {
                        "visual_strategy": "AUTHENTIC_PHOTO",
                        "image_path": str(output_file.resolve()),
                        "is_authentic": True,
                        "source_url": wiki_media["url"],
                        "artist": wiki_media["artist"],
                        "license": wiki_media["license"]
                    }

        # 2. Try Wikimedia Commons Search
        for entity in clean_entities:
            print(f"Searching Commons search for: '{entity}'...")
            commons_media = search_wikimedia_commons_image(entity)
            if commons_media and commons_media.get("url"):
                success = download_and_format_image(commons_media["url"], output_file)
                if success:
                    print(f"SUCCESS: Retrieved Commons photograph for '{entity}'!")
                    return {
                        "visual_strategy": "AUTHENTIC_PHOTO",
                        "image_path": str(output_file.resolve()),
                        "is_authentic": True,
                        "source_url": commons_media["url"],
                        "artist": commons_media["artist"],
                        "license": commons_media["license"]
                    }

    return {
        "visual_strategy": classification["visual_strategy"],
        "image_path": str(output_file.resolve()),
        "is_authentic": False,
        "source_url": "Internal Generator",
        "license": "VYRA Internal Asset"
    }
