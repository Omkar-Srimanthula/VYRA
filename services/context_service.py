from typing import Any
import re

# ==========================================================
# VYRA CONTEXT SERVICE
# ==========================================================

SUPPORTED_LANGUAGES = {
    "english": "en",
    "telugu": "te",
    "తెలుగు": "te",
    "hindi": "hi",
    "हिंदी": "hi",
    "tamil": "ta",
    "kannada": "kn",
    "malayalam": "ml",
    "marathi": "mr",
    "bengali": "bn",
    "gujarati": "gu",
    "punjabi": "pa",
    "urdu": "ur",
    "spanish": "es",
    "español": "es",
    "espanol": "es",
    "french": "fr",
    "français": "fr",
    "francais": "fr",
    "german": "de",
    "deutsch": "de",
    "italian": "it",
    "italiano": "it",
    "portuguese": "pt",
    "português": "pt",
    "polish": "pl",
    "turkish": "tr",
    "russian": "ru",
    "dutch": "nl",
    "czech": "cs",
    "arabic": "ar",
    "chinese": "zh-cn",
    "japanese": "ja",
    "korean": "ko",
    "hungarian": "hu",
}

DEFAULT_CONTEXT = {
    "audience": "general",
    "purpose": "education",
    "tone": "engaging",
    "difficulty": "beginner",
    "duration": 45,
    "style": "educational",
    "language": "english",
    "language_code": "en",
}


def normalize_language(language: str) -> tuple[str, str]:
    if not language:
        return ("english", "en")

    normalized = str(language).strip().lower()

    # Direct match in dict
    code = SUPPORTED_LANGUAGES.get(normalized)
    if code:
        if code == "es": return ("spanish", "es")
        if code == "fr": return ("french", "fr")
        if code == "de": return ("german", "de")
        if code == "it": return ("italian", "it")
        if code == "pt": return ("portuguese", "pt")
        if code == "te": return ("telugu", "te")
        if code == "hi": return ("hindi", "hi")
        return (normalized, code)

    # Match by language code
    if normalized in SUPPORTED_LANGUAGES.values():
        for name, value in SUPPORTED_LANGUAGES.items():
            if value == normalized and name in ["english", "spanish", "french", "german", "telugu", "hindi", "italian", "portuguese"]:
                return (name, value)

    # Substring search in language names
    for name, value in SUPPORTED_LANGUAGES.items():
        if name in normalized or normalized in name:
            if value == "es": return ("spanish", "es")
            if value == "fr": return ("french", "fr")
            if value == "de": return ("german", "de")
            if value == "te": return ("telugu", "te")
            return (name, value)

    return ("english", "en")


def extract_user_intent(topic_or_prompt: str, request_params: dict = None) -> dict[str, Any]:
    """
    Extracts and preserves user intent from the raw input prompt:
    - Exact topic
    - Requested language & language_code
    - Target duration (in seconds)
    - Requested tone, style, audience
    - Key entities (people, places, events, spacecraft, brands)
    - Requested visual preferences (real photos, diagrams, etc.)
    """
    raw_prompt = str(topic_or_prompt or "").strip()
    params = request_params or {}

    if not raw_prompt:
        raw_prompt = str(params.get("topic", "")).strip() or "General Knowledge"

    # 1. Detect requested language in prompt text
    detected_lang = params.get("language")
    prompt_lower = raw_prompt.lower()

    for lang_name in SUPPORTED_LANGUAGES.keys():
        if re.search(r'\b' + re.escape(lang_name) + r'\b', prompt_lower):
            detected_lang = lang_name
            break

    lang_name, lang_code = normalize_language(detected_lang or "english")

    # 2. Detect target duration in prompt (e.g. 60-sec, 30s, 2 minutes, 45 seconds, 45s)
    duration = params.get("duration")
    duration_match = re.search(r'\b(\d+)\s*(?:-| )*(?:sec|second|s|min|minute)s?\b', prompt_lower)
    if duration_match:
        val = int(duration_match.group(1))
        if "min" in duration_match.group(0):
            val = val * 60
        duration = max(15, min(val, 300))

    try:
        duration = int(duration) if duration else 45
    except (TypeError, ValueError):
        duration = 45

    # 3. Detect tone
    tone = params.get("tone")
    tones = ["dramatic", "cinematic", "humorous", "serious", "formal", "inspiring", "educational", "urgent", "mysterious", "engaging"]
    for t in tones:
        if t in prompt_lower:
            tone = t
            break
    tone = tone or DEFAULT_CONTEXT["tone"]

    # 4. Detect audience
    audience = params.get("audience")
    audiences = ["kids", "children", "experts", "students", "beginners", "general", "adults"]
    for a in audiences:
        if a in prompt_lower:
            audience = a
            break
    audience = audience or DEFAULT_CONTEXT["audience"]

    # 5. Detect style
    style = params.get("style")
    if any(k in prompt_lower for k in ["documentary", "documentaire", "documental"]):
        style = "documentary"
    elif any(k in prompt_lower for k in ["explainer", "explicativo", "explicatif"]):
        style = "explainer"
    elif any(k in prompt_lower for k in ["storytelling", "cuento", "histoire"]):
        style = "storytelling"
    elif any(k in prompt_lower for k in ["news", "noticias", "nouvelles"]):
        style = "news"
    elif any(k in prompt_lower for k in ["tutorial", "tuto"]):
        style = "tutorial"
    elif any(k in prompt_lower for k in ["reel", "shorts", "short", "court"]):
        style = style or "reel"
    
    style = style or DEFAULT_CONTEXT["style"]

    # 6. Detect requested visual style / preference
    requested_visuals = "authentic_photos"
    if any(k in prompt_lower for k in ["diagram", "infographic", "chart", "illustration", "3d"]):
        requested_visuals = "diagrams_infographics"
    elif any(k in prompt_lower for k in ["real photo", "authentic photo", "historical photo", "real photos", "isro photo", "nasa photo", "photos historiques"]):
        requested_visuals = "authentic_real_photos"

    use_avatar = bool(params.get("use_avatar") or any(k in prompt_lower for k in ["avatar", "presenter avatar", "ai presenter", "my face"]))

    # 7. Extract Exact Topic & Key Entities
    about_match = re.search(r'\b(?:about|on|regarding|topic of|history of|sobre|sobre la historia del|sobre la historia de|sur|sur la|d\'|de)\s+([^.\n,!]+)', raw_prompt, re.IGNORECASE)

    cleaned_topic = ""
    if about_match:
        target_subject = about_match.group(1).strip()
        target_subject = re.sub(
            r'\s+\b(?:with|in|using|for|and|by|en|avec|sobre)\b\s+(?:dramatic|cinematic|educational|real photos|historical photos|isro|nasa|photos|subtitles|duration|beginners|tone|style|language|telugu|english|hindi|spanish|french|dramatic tone|clear diagrams|authentic photos|ai presenter avatar|presenter avatar|avatar).*',
            '',
            target_subject,
            flags=re.IGNORECASE
        ).strip()
        if len(target_subject) > 2:
            cleaned_topic = target_subject

    if not cleaned_topic:
        cleaned_topic = re.sub(
            r'^(?:create|make|generate|produce|write|explain|un video|un documentaire|how to prepare|how to make)\s+(?:a\s+)?(?:\d+[- ](?:sec|second|min|minute|s)\s+)?(?:[a-z]+\s+)?(?:documentary|video|script|explainer|reel|short|court)?\s+(?:about|on|regarding|history of|sobre|sur)?\s*',
            '',
            raw_prompt,
            flags=re.IGNORECASE
        ).strip()
        cleaned_topic = re.sub(
            r'\s+\b(?:with|in|using|for|and|by|en|avec|sobre)\b\s+(?:dramatic|cinematic|educational|real photos|historical photos|isro|nasa|photos|subtitles|duration|beginners|tone|style|language|telugu|english|hindi|spanish|french|dramatic tone|clear diagrams|authentic photos|ai presenter avatar|presenter avatar|avatar).*',
            '',
            cleaned_topic,
            flags=re.IGNORECASE
        ).strip()

    if not cleaned_topic:
        cleaned_topic = raw_prompt[:60]

    entities = re.findall(r'\b[A-Z][a-zA-Z0-9\'-]+(?:\s+[A-Z][a-zA-Z0-9\'-]+)*\b', raw_prompt)
    stop_words = {"Create", "Make", "Generate", "Write", "Explain", "Telugu", "English", "Hindi", "Spanish", "French", "Video", "Script", "Documentary", "Un", "En", "Sur", "Avec", "Sobre", "How", "ISRO", "NASA", "AI"}
    clean_entities = [e for e in entities if e not in stop_words and len(e) > 2]
    if cleaned_topic and cleaned_topic not in clean_entities and len(cleaned_topic) > 2:
        clean_entities.insert(0, cleaned_topic)

    return {
        "raw_prompt": raw_prompt,
        "exact_topic": cleaned_topic,
        "topic": cleaned_topic,
        "requested_language": lang_name,
        "language": lang_name,
        "language_code": lang_code,
        "duration": duration,
        "tone": tone,
        "audience": audience,
        "style": style,
        "requested_visuals": requested_visuals,
        "use_avatar": use_avatar,
        "entities": list(dict.fromkeys(clean_entities)),
        "user_context": params.get("context", "") or params.get("user_context", "") or ""
    }


def build_video_context(
    topic: str,
    context: str = "",
    language: str = "english",
    audience: str = "general",
    purpose: str = "education",
    tone: str = "engaging",
    difficulty: str = "beginner",
    duration: int = 45,
    style: str = "educational",
) -> dict[str, Any]:

    intent = extract_user_intent(topic, {
        "context": context,
        "language": language,
        "audience": audience,
        "purpose": purpose,
        "tone": tone,
        "difficulty": difficulty,
        "duration": duration,
        "style": style
    })

    return {
        "raw_prompt": intent["raw_prompt"],
        "topic": intent["exact_topic"],
        "exact_topic": intent["exact_topic"],
        "user_context": intent["user_context"],
        "audience": intent["audience"],
        "purpose": purpose or DEFAULT_CONTEXT["purpose"],
        "tone": intent["tone"],
        "difficulty": difficulty or DEFAULT_CONTEXT["difficulty"],
        "duration": intent["duration"],
        "style": intent["style"],
        "language": intent["requested_language"],
        "language_code": intent["language_code"],
        "requested_visuals": intent["requested_visuals"],
        "use_avatar": intent["use_avatar"],
        "entities": intent["entities"]
    }


def create_context_prompt(video_context: dict[str, Any]) -> str:
    entities_str = ", ".join(video_context.get("entities", [])) or video_context.get("topic", "")
    return f"""
You are the user-intent intelligence engine for VYRA.

STRICT INSTRUCTION:
The user's prompt is your PRIMARY instruction. Preserve the exact topic, angle, entities, and language.

EXACT TOPIC / SUBJECT:
{video_context["topic"]}

KEY ENTITIES & SUBJECTS:
{entities_str}

ORIGINAL USER PROMPT:
{video_context.get("raw_prompt", video_context["topic"])}

TARGET LANGUAGE:
{video_context["language"].upper()} (ISO code: {video_context["language_code"]})

VIDEO DURATION:
{video_context["duration"]} seconds

REQUESTED TONE:
{video_context["tone"]}

REQUESTED STYLE:
{video_context["style"]}

TARGET AUDIENCE:
{video_context["audience"]}

USER CONTEXT:
{video_context["user_context"] or "No additional context provided."}

STRICT RULE:
- Generate the script narration ENTIRELY in the requested language ({video_context["language"].upper()}).
- Keep every line 100% focused on {video_context["topic"]}.
- Do NOT drift to generic lifestyle advice unless explicitly requested.
"""