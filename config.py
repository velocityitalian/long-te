"""VELOCITY LONGFORM - 16:9 chapter lesson, brand and motion constants."""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

OUTPUT_DIR = BASE_DIR / "output"
LESSONS_DIR = OUTPUT_DIR / "lessons"
HISTORY_DIR = OUTPUT_DIR / "history"
SCENE_DIR = BASE_DIR / "scene"

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30

TARGET_CHAPTERS = 8
PHRASES_PER_CHAPTER = 7
TARGET_PHRASES = TARGET_CHAPTERS * PHRASES_PER_CHAPTER

# ---------------------------------------------------------------- brand

BRAND = "VELOCITY TELUGU"
BRAND_LOCKUP_TOP = "VELOCITY"
BRAND_LOCKUP_BOTTOM = "TELUGU"
HANDLE = "@velocitytelugu"
MASCOT_NAME = "Velo"

# ==== LANGUAGE PACK START ====
LANGUAGE = {'code': 'te',
 'name': 'Telugu',
 'native_name': 'తెలుగు',
 'history_key': 'telugu',
 'english_voice': 'en-US-AvaNeural',
 'english_fallback_voice': 'en-US-GuyNeural',
 'native_voice': 'te-IN-MohanNeural',
 'native_fallback_voice': 'te-IN-ShrutiNeural',
 'native_engine': 'edge',
 'native_lang_code': 'te',
 'english_rate': '-4%',
 'native_rate': '-10%',
 'english_pitch': '+0Hz',
 'native_pitch': '+0Hz',
 'native_label': 'తెలుగు',
 'translit_label': 'SAY IT LIKE',
 'flag': 'in',
 'greeting': 'నమస్కారం!',
 'encouragement': 'అద్భుతం!',
 'rtl': False,
 'char_tiles': False,
 'script_font': 'Script.ttf',
 'glyphs': 'అఆఇఈఉఊఎఏఐఒఓఔకఖగఘచఛజఝటఠడఢతథదధనపఫబభమయరలవశషసహ'}
# ==== LANGUAGE PACK END ====

# ==== CATEGORIES START ====
CATEGORIES = {'Motivation': 'ప్రేరణ',
 'Love': 'ప్రేమ',
 'Success': 'విజయం',
 'Wisdom': 'జ్ఞానం',
 'Happiness': 'ఆనందం',
 'Self Improvement': 'ఆత్మాభివృద్ధి',
 'Gratitude': 'కృతజ్ఞత',
 'Friendship': 'స్నేహం',
 'Hope': 'ఆశ',
 'Creativity': 'సృజనాత్మకత',
 'Inner Peace': 'అంతర్గత శాంతి',
 'Confidence': 'ఆత్మవిశ్వాసం',
 'Perseverance': 'పట్టుదల',
 'Inspiration': 'స్ఫూర్తి',
 'Positive Life': 'సానుకూల జీవితం',
 'Courage': 'ధైర్యం',
 'Kindness': 'దయ',
 'Patience': 'ఓర్పు',
 'Forgiveness': 'క్షమ',
 'Strength': 'బలం',
 'Joy': 'సంతోషం',
 'Balance': 'సమతుల్యత',
 'Growth': 'అభివృద్ధి',
 'Purpose': 'ఉద్దేశ్యం',
 'Mindfulness': 'సావధానం',
 'Travel & Airport': 'ప్రయాణం & విమానాశ్రయం',
 'Ordering Food & Dining': 'ఆహారం ఆర్డర్ చేయడం & భోజనం',
 'Shopping & Prices': 'షాపింగ్ & ధరలు',
 'Asking for Directions': 'మార్గం అడగడం',
 'Hotel & Accommodation': 'హోటల్ & వసతి',
 'Daily Routine': 'రోజువారీ దినచర్య',
 'Meeting People & Greetings': 'వ్యక్తులను కలవడం & శుభాకాంక్షలు',
 'Emergency & Health': 'అత్యవసర పరిస్థితి & ఆరోగ్యం',
 'Public Transportation': 'ప్రజా రవాణా',
 'Work & Office': 'పని & కార్యాలయం',
 'Weather & Small Talk': 'వాతావరణం & చిన్నపాటి సంభాషణ',
 'Coffee Shop & Bakery': 'కాఫీ షాప్ & బేకరీ',
 'Family & Home': 'కుటుంబం & ఇల్లు',
 'Hobbies & Free Time': 'అభిరుచులు & ఖాళీ సమయం',
 'Dating & Romance': 'డేటింగ్ & శృంగారం',
 'Phone Calls & Messages': 'ఫోన్ కాల్స్ & సందేశాలు',
 'Banking & Money': 'బ్యాంకింగ్ & డబ్బు',
 'Doctor & Pharmacy': 'డాక్టర్ & ఫార్మసీ',
 'Sports & Fitness': 'క్రీడలు & ఫిట్\u200cనెస్',
 'Celebrations & Parties': 'వేడుకలు & పార్టీలు',
 'Feelings & Emotions': 'భావాలు & భావోద్వేగాలు',
 'Agreeing & Disagreeing': 'అంగీకరించడం & విభేదించడం',
 'Making Plans': 'ప్రణాళికలు చేయడం',
 'Common Native Slang': 'సాధారణ స్థానిక యాస',
 'Cultural Traditions': 'సాంస్కృతిక సంప్రదాయాలు'}
# ==== CATEGORIES END ====

CATEGORY_NAMES = list(CATEGORIES.keys())

AI_MODEL = os.getenv("AI_MODEL", "openai/gpt-5.4-nano")
AI_FALLBACK_MODEL = os.getenv("AI_FALLBACK_MODEL", "gemini-fast")
POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY", "")

# ---------------------------------------------------------------- timing (seconds)

INTRO_DURATION = 7.2
CHAPTER_INTRO_DURATION = 4.4
OUTRO_DURATION = 13.0

EN_CARD_IN = 0.70
GAP_EN_NATIVE = 0.60
NATIVE_CARD_LEAD = 0.40
GAP_BEFORE_REPEAT = 1.00
TAIL_HOLD = 1.30

# ---------------------------------------------------------------- palette

INK = "#30303A"
MUTED = "#8A8A8A"
CREAM = "#FFF8E7"
GREEN = "#58CC02"
GREEN_DARK = "#46A302"
GREEN_DEEP = "#3D8F00"
BLUE = "#1CB0F6"
PURPLE = "#7C5CFF"
ORANGE = "#FF7A00"
RED = "#FF4B4B"
YELLOW = "#F5A700"
TEAL = "#00A889"
PINK = "#E056A0"

# ==== HASHTAGS START ====
HASHTAGS = ['#learntelugu',
 '#telugulessons',
 '#teluguforbeginners',
 '#languagelearning',
 '#teluguvocabulary',
 '#velocitytelugu',
 '#dailytelugu',
 '#telugu',
 '#learnlanguages',
 '#speaktelugu']
# ==== HASHTAGS END ====
