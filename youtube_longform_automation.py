"""
YouTube Long-Form Video Automation - Bilingual English/Telugu Content Generator
GENERATES 10-MINUTE VIDEOS with improved backgrounds for YouTube
"""

import os
import sys
import json
import random
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")

# Directories
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
IMAGES_DIR = OUTPUT_DIR / "images"
AUDIO_DIR = OUTPUT_DIR / "audio"
VIDEO_DIR = OUTPUT_DIR / "video"
HISTORY_DIR = OUTPUT_DIR / "history"
LONGFORM_DIR = OUTPUT_DIR / "longform_videos"

for d in [OUTPUT_DIR, IMAGES_DIR, AUDIO_DIR, VIDEO_DIR, HISTORY_DIR, LONGFORM_DIR]:
    d.mkdir(exist_ok=True)

# Video settings (16:9 horizontal for YouTube long-form)
VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080
FPS = 30
TARGET_DURATION_MINUTES = 5
TARGET_PHRASES = 120

# English category names
CATEGORIES_ENGLISH = [
    "Motivation", "Love", "Success", "Wisdom", "Happiness",
    "Self Improvement", "Gratitude", "Friendship", "Hope", "Creativity",
    "Inner Peace", "Confidence", "Perseverance", "Inspiration", "Positive Life",
    "Courage", "Kindness", "Patience", "Forgiveness", "Strength",
    "Joy", "Balance", "Growth", "Purpose", "Mindfulness",
]

# Telugu translations
CATEGORIES_TELUGU = {
    "Motivation": "ప్రేరణ",
    "Love": "ప్రేమ",
    "Success": "విజయం",
    "Wisdom": "జ్ఞానం",
    "Happiness": "ఆనందం",
    "Self Improvement": "ఆత్మాభివృద్ధి",
    "Gratitude": "కృతజ్ఞత",
    "Friendship": "స్నేహం",
    "Hope": "ఆశ",
    "Creativity": "సృజనాత్మకత",
    "Inner Peace": "అంతర్గత శాంతి",
    "Confidence": "ఆత్మవిశ్వాసం",
    "Perseverance": "పట్టుదల",
    "Inspiration": "స్ఫూర్తి",
    "Positive Life": "సానుకూల జీవితం",
    "Courage": "ధైర్యం",
    "Kindness": "దయ",
    "Patience": "ఓర్పు",
    "Forgiveness": "క్షమ",
    "Strength": "బలం",
    "Joy": "సంతోషం",
    "Balance": "సమతుల్యత",
    "Growth": "అభివృద్ధి",
    "Purpose": "ఉద్దేశ్యం",
    "Mindfulness": "సావధానం",
}

# Edge TTS voices
ENGLISH_VOICE = "en-US-GuyNeural"
LANG_VOICE = "te-IN-ShrutiNeural"

# Phrase history file
PHRASE_HISTORY_FILE = HISTORY_DIR / "all_generated_phrases.json"

# Viral hook styles for engagement
VIRAL_STYLES = [
    "surprising fact",
    "common mistake correction",
    "quick tip",
    "must-know phrase",
    "local secret",
    "travel hack",
    "flirty phrase",
    "funny expression",
    "cultural insight",
    "word origin story"
]

# AI Model
AI_MODEL = os.getenv("AI_MODEL")

if not AI_MODEL:
    raise ValueError(
        "AI_MODEL not set! Please add 'AI_MODEL=gemini-fast' to your .env file."
    )


# ============== PHRASE HISTORY MANAGEMENT ==============

def load_phrase_history():
    if PHRASE_HISTORY_FILE.exists():
        with open(PHRASE_HISTORY_FILE, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    return {"phrases": [], "last_updated": None}


def save_phrase_history(data):
    data["last_updated"] = datetime.now().isoformat()
    with open(PHRASE_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def is_phrase_used(english_phrase):
    history = load_phrase_history()
    english_lower = english_phrase.lower().strip()
    for p in history.get("phrases", []):
        if p.get("english", "").lower().strip() == english_lower:
            return True
    return False


def is_phrase_similar(new_phrase, used_phrases, similarity_threshold=0.6):
    new_words = set(new_phrase.lower().split())
    if len(new_words) < 3:
        for used in used_phrases:
            if new_phrase.lower() in used.lower() or used.lower() in new_phrase.lower():
                return True
        return False
    for used in used_phrases:
        used_words = set(used.lower().split())
        if len(new_words) == 0 or len(used_words) == 0:
            continue
        intersection = len(new_words.intersection(used_words))
        union = len(new_words.union(used_words))
        similarity = intersection / union if union > 0 else 0
        if similarity >= similarity_threshold:
            return True
    return False


def filter_similar_phrases(phrases, history, similarity_threshold=0.6):
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    unique_phrases = []
    for phrase in phrases:
        english_text = phrase.get("english", "")
        if not is_phrase_similar(english_text, used_phrases, similarity_threshold):
            unique_phrases.append(phrase)
        else:
            print(f"[filter] Skipping similar: {english_text[:50]}...")
    return unique_phrases


def add_phrases_to_history(phrases, category):
    history = load_phrase_history()
    for phrase in phrases:
        history["phrases"].append({
            "english": phrase["english"],
            "telugu": phrase["telugu"],
            "category": category,
            "generated_at": datetime.now().isoformat()
        })
    save_phrase_history(history)
    print(f"[history] Added {len(phrases)} phrases to history (total: {len(history['phrases'])})")


# ============== CONTENT GENERATION ==============

def calculate_phrases_needed(target_minutes: int) -> int:
    avg_phrase_duration = 5.0
    total_seconds = target_minutes * 60
    return int(total_seconds / avg_phrase_duration)


def generate_phrases_for_longform(category_english: str, num_phrases: int) -> list:
    category_telugu = CATEGORIES_TELUGU[category_english]
    history = load_phrase_history()
    used_phrases = [p.get("english", "") for p in history.get("phrases", [])]
    viral_style = random.choice(VIRAL_STYLES)
    all_phrases = []
    batch_size = 20
    max_attempts = 5

    for batch_num in range((num_phrases + batch_size - 1) // batch_size):
        remaining = num_phrases - len(all_phrases)
        current_batch_size = min(batch_size, remaining)
        if current_batch_size <= 0:
            break
        for attempt in range(max_attempts):
            try:
                import requests
                url = "https://gen.pollinations.ai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {POLLINATIONS_API_KEY}",
                    "Content-Type": "application/json"
                }
                exclusion_note = ""
                if used_phrases:
                    recent = used_phrases[-30:] if len(used_phrases) > 30 else used_phrases
                    exclusion_note = f"\n\nAVOID these phrases (already used): {recent}"

                prompt = f"""Create {current_batch_size * 2} unique {category_english} phrases for English speakers learning Telugu.

Style: Make each phrase feel like a {viral_style} - something people would want to share!

IMPORTANT RULES FOR NATURAL SPEECH:
1. Keep phrases SHORT (5-12 words max per language)
2. Add NATURAL PAUSES using commas (e.g., "Dream big, start small")
3. Use punctuation for breathing room in TTS
4. Avoid long run-on sentences
5. Each phrase should be speakable in 3-5 seconds
6. Use everyday vocabulary - avoid exotic or rare words
7. Avoid complex grammar - keep it simple and practical
8. Vary sentence structure for natural flow

For each phrase:
1. English phrase (with commas for natural pauses)
2. Telugu translation (Telugu script)
3. Pronunciation guide (phonetic spelling for English speakers)

Return as JSON array:
[{{"english": "...", "telugu": "...", "pronunciation": "..."}}]

IMPORTANT: Create FRESH, UNIQUE phrases that haven't been used before.{exclusion_note}"""

                payload = {
                    "model": AI_MODEL,
                    "messages": [
                        {"role": "system", "content": "You are a viral Telugu teacher creating engaging educational content for YouTube. Create short, natural phrases with pauses."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 1.0
                }

                response = requests.post(url, headers=headers, json=payload, timeout=90)
                response.raise_for_status()

                data = response.json()
                content = data["choices"][0]["message"]["content"].strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                phrases = json.loads(content)
                filtered_phrases = filter_similar_phrases(phrases, history)
                unique_phrases = []
                for phrase in filtered_phrases:
                    if len(phrase["english"].split()) > 15:
                        continue
                    if not is_phrase_used(phrase["english"]):
                        unique_phrases.append(phrase)
                for phrase in unique_phrases:
                    if len(all_phrases) < num_phrases:
                        all_phrases.append(phrase)
                if len(all_phrases) >= num_phrases:
                    break
            except Exception as e:
                print(f"[content] Batch {batch_num + 1}, Attempt {attempt + 1} failed: {e}")
        if len(all_phrases) < num_phrases:
            import time
            time.sleep(1)

    final_phrases = all_phrases[:num_phrases]
    if final_phrases:
        add_phrases_to_history(final_phrases, category_english)
    print(f"[content] Generated {len(final_phrases)} phrases for long-form video")
    return final_phrases


def get_fresh_fallback_phrases(category: str, num_phrases: int) -> list:
    all_fallbacks = {
        "Motivation": [
            {"english": "Believe in yourself.", "telugu": "నీలో నీకు నమ్మకం ఉంచుకో.", "pronunciation": "nee-lo nee-ku nam-ma-kam unchu-ko."},
            {"english": "You are capable of amazing things.", "telugu": "నీవు అద్భుతమైన పనులు చేయగలవు.", "pronunciation": "nee-vu ad-bhu-ta-mai-na pa-nu-lu che-ya-ga-la-vu."},
            {"english": "Dream big, start small.", "telugu": "పెద్ద కలలు కను, చిన్నగా మొదలుపెట్టు.", "pronunciation": "ped-da ka-la-lu ka-nu, chin-na-ga mo-da-lu-pet-tu."},
            {"english": "Your future is created by your actions.", "telugu": "నీ భవిష్యత్తు నీ చర్యలతో నిర్మించబడుతుంది.", "pronunciation": "nee bha-vi-shyat-tu nee char-ya-la-to nir-min-cha-ba-du-tun-di."},
            {"english": "Never give up on your dreams.", "telugu": "నీ కలలను ఎప్పుడూ వదులుకోకు.", "pronunciation": "nee ka-la-la-nu ep-pu-du va-du-lu-ko-ku."},
            {"english": "Small steps lead to big changes.", "telugu": "చిన్న అడుగులు పెద్ద మార్పులకు దారితీస్తాయి.", "pronunciation": "chin-na a-du-gu-lu ped-da maar-pu-la-ku daa-ri-tees-taa-yi."},
            {"english": "You are stronger than you think.", "telugu": "నీవు అనుకున్నదానికంటే బలంగా ఉన్నావు.", "pronunciation": "nee-vu a-nu-kun-na-daa-ni-kan-te ba-lam-ga un-naa-vu."},
        ],
        "Love": [
            {"english": "Love yourself first.", "telugu": "ముందు నిన్ను నీవు ప్రేమించుకో.", "pronunciation": "mun-du nin-nu nee-vu pre-min-chu-ko."},
            {"english": "Love makes everything possible.", "telugu": "ప్రేమ అంతా సాధ్యం చేస్తుంది.", "pronunciation": "pre-ma an-taa saadh-yam ches-tun-di."},
            {"english": "My heart beats for you.", "telugu": "నా గుండె నీ కోసం కొట్టుకుంటుంది.", "pronunciation": "naa gun-de nee ko-sam kot-tu-kun-tun-di."},
            {"english": "You are my everything.", "telugu": "నీవు నా సర్వస్వం.", "pronunciation": "nee-vu naa sar-va-svam."},
            {"english": "Together forever, hand in hand.", "telugu": "ఎప్పటికీ కలిసి, చేయి చేయి కలిపి.", "pronunciation": "ep-pa-ti-ee ka-li-si, che-yi che-yi ka-li-pi."},
        ],
        "Success": [
            {"english": "Success comes from hard work.", "telugu": "విజయం కష్టపడి పనిచేయడం వల్ల వస్తుంది.", "pronunciation": "vi-ja-yam kash-ta-pa-di pa-ni-che-ya-dam val-la vas-tun-di."},
            {"english": "Keep going, you're getting there.", "telugu": "కొనసాగించు, నీవు అక్కడికి చేరుకుంటున్నావు.", "pronunciation": "ko-na-saa-gin-chu, nee-vu ak-ka-di-ki che-ru-kun-tun-naa-vu."},
            {"english": "Winners never quit.", "telugu": "విజేతలు ఎప్పుడూ వదలరు.", "pronunciation": "vi-je-ta-lu ep-pu-du va-da-la-ru."},
            {"english": "Your effort will pay off.", "telugu": "నీ కృషి ఫలిస్తుంది.", "pronunciation": "nee kri-shi pha-lis-tun-di."},
        ],
        "Wisdom": [
            {"english": "Knowledge is power.", "telugu": "జ్ఞానమే శక్తి.", "pronunciation": "gnyaa-na-me shak-ti."},
            {"english": "Learn from yesterday, live for today.", "telugu": "నిన్న నుండి నేర్చుకో, ఈ రోజు కోసం జీవించు.", "pronunciation": "nin-na nun-di ner-chu-ko, ee ro-ju ko-sam jee-vin-chu."},
            {"english": "Think before you act.", "telugu": "చేసే ముందు ఆలోచించు.", "pronunciation": "che-se mun-du aa-lo-chin-chu."},
            {"english": "Experience is the best teacher.", "telugu": "అనుభవమే ఉత్తమ గురువు.", "pronunciation": "a-nu-bha-va-me ut-ta-ma gu-ru-vu."},
        ],
        "Happiness": [
            {"english": "Happiness is a choice.", "telugu": "ఆనందం ఒక ఎంపిక.", "pronunciation": "aa-nan-dam o-ka em-pi-ka."},
            {"english": "Find joy in the little things.", "telugu": "చిన్న విషయాలలో ఆనందాన్ని కనుగొను.", "pronunciation": "chin-na vi-shay-aa-la-lo aa-nan-daan-ni ka-nu-go-nu."},
            {"english": "Smile, it makes others happy.", "telugu": "చిరునవ్వు నవ్వు, ఇతరులను సంతోషపెడుతుంది.", "pronunciation": "chi-ru-na-vvu nav-vu, i-ta-ru-la-nu san-to-sha-pe-du-tun-di."},
            {"english": "Today is a gift.", "telugu": "ఈ రోజు ఒక బహుమానం.", "pronunciation": "ee ro-ju o-ka ba-hu-maa-nam."},
        ],
        "Self Improvement": [
            {"english": "Be better than yesterday.", "telugu": "నిన్నటి కంటే మెరుగుగా ఉండు.", "pronunciation": "nin-na-ti kan-te me-ru-gu-ga un-du."},
            {"english": "Grow through what you go through.", "telugu": "నీవు ఎదుర్కొనే దాని ద్వారా ఎదుగు.", "pronunciation": "nee-vu e-dur-ko-ne daa-ni dvaa-raa e-du-gu."},
            {"english": "Invest in yourself daily.", "telugu": "ప్రతి రోజు నీలో పెట్టుబడి పెట్టు.", "pronunciation": "pra-ti ro-ju nee-lo pet-tu-ba-di pet-tu."},
        ],
        "Gratitude": [
            {"english": "Thank you for everything.", "telugu": "ప్రతిదానికీ ధన్యవాదాలు.", "pronunciation": "pra-ti-daa-ni-kee dha-nya-vaa-daa-lu."},
            {"english": "I appreciate your help.", "telugu": "నీ సహాయాన్ని అభినందిస్తున్నాను.", "pronunciation": "nee sa-haa-yaan-ni a-bhi-nan-dis-tun-naa-nu."},
            {"english": "Grateful for this moment.", "telugu": "ఈ క్షణానికి కృతజ్ఞతలు.", "pronunciation": "ee ksha-naa-ni-ki kri-ta-jnya-ta-lu."},
        ],
        "Friendship": [
            {"english": "Friends forever, no matter what.", "telugu": "ఎప్పటికీ స్నేహితులు, ఏమైనా సరే.", "pronunciation": "ep-pa-ti-ee sne-hi-tu-lu, e-mai-naa sa-re."},
            {"english": "You are my best friend.", "telugu": "నీవు నా అత్యుత్తమ స్నేహితుడు.", "pronunciation": "nee-vu naa a-tyut-ta-ma sne-hi-tu-du."},
            {"english": "True friends stick together.", "telugu": "నిజమైన స్నేహితులు కలిసి ఉంటారు.", "pronunciation": "ni-ja-mai-na sne-hi-tu-lu ka-li-si un-taa-ru."},
        ],
        "Hope": [
            {"english": "There is always hope.", "telugu": "ఎల్లప్పుడూ ఆశ ఉంటుంది.", "pronunciation": "el-lap-pu-du aa-sha un-tun-di."},
            {"english": "Better days are coming.", "telugu": "మంచి రోజులు వస్తున్నాయి.", "pronunciation": "man-chi ro-ju-lu vas-tun-naa-yi."},
            {"english": "Keep faith, keep going.", "telugu": "నమ్మకం ఉంచు, కొనసాగించు.", "pronunciation": "nam-ma-kam unchu, ko-na-saa-gin-chu."},
        ],
        "Creativity": [
            {"english": "Create something beautiful today.", "telugu": "ఈ రోజు అందమైన దాన్ని సృష్టించు.", "pronunciation": "ee ro-ju an-da-mai-na daan-ni sri-sh-tin-chu."},
            {"english": "Your imagination is unlimited.", "telugu": "నీ ఊహకు అవధులు లేవు.", "pronunciation": "nee oo-ha-ku a-va-dhu-lu le-vu."},
            {"english": "Art comes from the heart.", "telugu": "కళ హృదయం నుండి వస్తుంది.", "pronunciation": "ka-la hri-da-yam nun-di vas-tun-di."},
            {"english": "Express yourself freely.", "telugu": "నీ అభిప్రాయాన్ని స్వేచ్ఛగా వ్యక్తపరచు.", "pronunciation": "nee a-bhi-praa-yaan-ni svech-chha-ga vyak-ta-pa-ra-chu."},
            {"english": "Innovation starts with curiosity.", "telugu": "ఆవిష్కరణ ఆసక్తితో మొదలవుతుంది.", "pronunciation": "aa-vish-ka-ra-na aa-sak-ti-to mo-da-la-vu-tun-di."},
        ],
        "Inner Peace": [
            {"english": "Find peace within yourself.", "telugu": "నీ లోపల శాంతిని కనుగొను.", "pronunciation": "nee lo-pa-la shaan-ti-ni ka-nu-go-nu."},
            {"english": "Breathe, relax, let go.", "telugu": "ఊపిరి పీల్చు, విశ్రాంతి తీసుకో, వదిలేయ్.", "pronunciation": "oo-pi-ri peel-chu, vi-shraan-ti tee-su-ko, va-di-le-y."},
            {"english": "Calm mind, happy heart.", "telugu": "ప్రశాంతమైన మనసు, సంతోషకరమైన హృదయం.", "pronunciation": "pra-shaan-ta-mai-na ma-na-su, san-to-sha-ka-ra-mai-na hri-da-yam."},
        ],
        "Confidence": [
            {"english": "You are enough, just as you are.", "telugu": "నీవు చాలు, ఎలా ఉన్నావో అలాగే.", "pronunciation": "nee-vu chaa-lu, e-laa un-naa-vo a-laa-ge."},
            {"english": "Stand tall, speak up.", "telugu": "గర్వంగా నిలబడు, బిగ్గరగా మాట్లాడు.", "pronunciation": "gar-vam-ga ni-la-ba-du, big-ga-ra-ga maat-laa-du."},
            {"english": "Believe in your abilities.", "telugu": "నీ సామర్థ్యాలను నమ్ముకో.", "pronunciation": "nee saa-mar-thyaa-la-nu nam-mu-ko."},
        ],
        "Perseverance": [
            {"english": "Never give up, keep pushing.", "telugu": "ఎప్పుడూ వదులుకోకు, ముందుకు సాగు.", "pronunciation": "ep-pu-du va-du-lu-ko-ku, mun-du-ku saa-gu."},
            {"english": "Storms make trees take deeper roots.", "telugu": "తుఫానులు చెట్ల వేర్లను లోతుగా చేస్తాయి.", "pronunciation": "tu-phaa-nu-lu chet-la ver-lu-nu lo-tu-ga ches-taa-yi."},
            {"english": "Patience and persistence win.", "telugu": "ఓర్పు మరియు పట్టుదల గెలుస్తాయి.", "pronunciation": "or-pu ma-ri-yu pat-tu-da-la ge-lus-taa-yi."},
        ],
        "Inspiration": [
            {"english": "Let your light shine bright.", "telugu": "నీ వెలుగును ప్రకాశవంతంగా వెలిగించు.", "pronunciation": "nee ve-lu-gu-nu pra-kaa-sha-van-tam-ga ve-li-gin-chu."},
            {"english": "Inspire others by your actions.", "telugu": "నీ చర్యలతో ఇతరులను ప్రేరేపించు.", "pronunciation": "nee char-ya-la-to i-ta-ru-la-nu pre-re-pin-chu."},
            {"english": "Be the change you want to see.", "telugu": "నీవు చూడాలనుకునే మార్పు నీవే అవ్వు.", "pronunciation": "nee-vu choo-daa-la-nu-ku-ne maar-pu nee-ve av-vu."},
        ],
        "Positive Life": [
            {"english": "Choose positivity every day.", "telugu": "ప్రతి రోజు సానుకూలతను ఎంచుకో.", "pronunciation": "pra-ti ro-ju saa-nu-koo-la-ta-nu en-chu-ko."},
            {"english": "Good vibes only.", "telugu": "మంచి ప్రకంపనలు మాత్రమే.", "pronunciation": "man-chi pra-kam-pa-na-lu maa-tra-me."},
            {"english": "Life is what you make it.", "telugu": "జీవితం నీవు తయారు చేసుకున్నట్లుగా ఉంటుంది.", "pronunciation": "jee-vi-tam nee-vu ta-yaa-ru che-su-kun-na-tlu-ga un-tun-di."},
        ],
        "Courage": [
            {"english": "Be brave, take the first step.", "telugu": "ధైర్యంగా ఉండు, మొదటి అడుగు వేయ్.", "pronunciation": "dhai-ryam-ga un-du, mo-da-ti a-du-gu ve-y."},
            {"english": "Courage is not the absence of fear.", "telugu": "ధైర్యం అంటే భయం లేకపోవడం కాదు.", "pronunciation": "dhai-ryam an-te bha-yam le-ka-pa-va-dam kaa-du."},
            {"english": "Face your fears head on.", "telugu": "నీ భయాలను ధైర్యంగా ఎదుర్కో.", "pronunciation": "nee bha-yaa-la-nu dhai-ryam-ga e-dur-ko."},
        ],
        "Kindness": [
            {"english": "Be kind to everyone you meet.", "telugu": "నీకు కలిసిన ప్రతి ఒక్కరికీ దయగా ఉండు.", "pronunciation": "nee-ku ka-li-si-na pra-ti ok-ka-ri-kee da-ya-ga un-du."},
            {"english": "Kindness costs nothing, means everything.", "telugu": "దయకు ఖర్చు లేదు, కానీ అది అన్నీ అర్థం.", "pronunciation": "da-ya-ku khar-chu le-du, kaa-nee a-di an-nee ar-tham."},
            {"english": "Spread kindness wherever you go.", "telugu": "నీవు ఎక్కడికి వెళ్ళినా దయను వ్యాపింపచేయ్.", "pronunciation": "nee-vu ek-ka-di-ki vel-li-na da-ya-nu vyaa-pim-pa-che-y."},
        ],
        "Patience": [
            {"english": "Good things take time.", "telugu": "మంచి విషయాలకు సమయం పడుతుంది.", "pronunciation": "man-chi vi-shay-aa-la-ku sa-ma-yam pa-du-tun-di."},
            {"english": "Wait patiently, trust the process.", "telugu": "ఓపికగా ఎదురుచూడు, ప్రక్రియను నమ్ముకో.", "pronunciation": "o-pi-ka-ga e-du-ru-choo-du, prak-riya-nu nam-mu-ko."},
            {"english": "Rome wasn't built in a day.", "telugu": "రోమ్ ఒక రోజులో నిర్మించబడలేదు.", "pronunciation": "rom o-ka ro-ju-lo nir-min-cha-ba-da-le-du."},
        ],
        "Forgiveness": [
            {"english": "Forgive and set yourself free.", "telugu": "క్షమించు మరియు నిన్ను విడిపించుకో.", "pronunciation": "ksha-min-chu ma-ri-yu nin-nu vi-di-pin-chu-ko."},
            {"english": "Let go of grudges, find peace.", "telugu": "ఆగ్రహాలను వదిలేయ్, శాంతిని కనుగొను.", "pronunciation": "aag-ra-haa-la-nu va-di-le-y, shaan-ti-ni ka-nu-go-nu."},
            {"english": "Forgiveness is a gift to yourself.", "telugu": "క్షమ అనేది నీకు నీవు ఇచ్చుకున్న బహుమానం.", "pronunciation": "ksha-ma a-ne-di nee-ku nee-vu ich-chu-kun-na ba-hu-maa-nam."},
        ],
        "Strength": [
            {"english": "You are stronger than you know.", "telugu": "నీకు తెలిసిన దానికంటే నీవు బలంగా ఉన్నావు.", "pronunciation": "nee-ku te-li-si-na daa-ni-kan-te nee-vu ba-lam-ga un-naa-vu."},
            {"english": "Inner strength comes from within.", "telugu": "లోపలి బలం లోపల నుండి వస్తుంది.", "pronunciation": "lo-pa-li ba-lam lo-pa-la nun-di vas-tun-di."},
            {"english": "Challenges make you stronger.", "telugu": "సవాళ్ళు నిన్ను బలంగా చేస్తాయి.", "pronunciation": "sa-vaal-lu nin-nu ba-lam-ga ches-taa-yi."},
        ],
        "Joy": [
            {"english": "Find joy in every moment.", "telugu": "ప్రతి క్షణంలో సంతోషాన్ని కనుగొను.", "pronunciation": "pra-ti ksha-nam-lo san-to-shaan-ni ka-nu-go-nu."},
            {"english": "Joy is contagious, spread it.", "telugu": "సంతోషం అంటువ్యాధి లాంటిది, దాన్ని వ్యాపింపచేయ్.", "pronunciation": "san-to-sham an-tu-vyaa-dhi laan-ti-di, daan-ni vyaa-pim-pa-che-y."},
            {"english": "Dance like nobody's watching.", "telugu": "ఎవరూ చూడట్లేదు అన్నట్లు నృత్యం చేయ్.", "pronunciation": "e-va-ru choo-da-tle-du an-na-tlu nri-tyam che-y."},
        ],
        "Balance": [
            {"english": "Find balance in your life.", "telugu": "నీ జీవితంలో సమతుల్యతను కనుగొను.", "pronunciation": "nee jee-vi-tam-lo sa-ma-tu-lya-ta-nu ka-nu-go-nu."},
            {"english": "Work hard, rest well.", "telugu": "కష్టపడి పనిచేయ్, బాగా విశ్రాంతి తీసుకో.", "pronunciation": "kash-ta-pa-di pa-ni-che-y, baa-gaa vi-shraan-ti tee-su-ko."},
            {"english": "Too much of anything is not good.", "telugu": "ఏదైనా అతిగా ఉంటే మంచిది కాదు.", "pronunciation": "e-dai-naa a-ti-ga un-te man-chi-di kaa-du."},
        ],
        "Growth": [
            {"english": "Growth happens outside your comfort zone.", "telugu": "ఎదుగుదల నీ సౌకర్య వలయం వెలుపల జరుగుతుంది.", "pronunciation": "e-du-gu-da-la nee sau-kar-ya va-la-yam ve-lu-pa-la ja-ru-gu-tun-di."},
            {"english": "Embrace change, grow stronger.", "telugu": "మార్పును స్వీకరించు, బలంగా ఎదుగు.", "pronunciation": "maar-pu-nu svee-ka-rin-chu, ba-lam-ga e-du-gu."},
            {"english": "Every challenge is a chance to grow.", "telugu": "ప్రతి సవాలు ఎదగడానికి ఒక అవకాశం.", "pronunciation": "pra-ti sa-vaa-lu e-da-ga-daa-ni-ki o-ka a-va-kaa-sham."},
        ],
        "Purpose": [
            {"english": "Find your purpose, follow it.", "telugu": "నీ ఉద్దేశ్యాన్ని కనుగొను, దాన్ని అనుసరించు.", "pronunciation": "nee ud-de-shyaan-ni ka-nu-go-nu, daan-ni a-nu-sa-rin-chu."},
            {"english": "Your life has meaning.", "telugu": "నీ జీవితానికి అర్థం ఉంది.", "pronunciation": "nee jee-vi-taa-ni-ki ar-tham un-di."},
            {"english": "Live with intention, not accident.", "telugu": "ఉద్దేశ్యంతో జీవించు, ప్రమాదవశాత్తు కాదు.", "pronunciation": "ud-de-shyam-to jee-vin-chu, pra-maa-da-va-shaat-tu kaa-du."},
        ],
        "Mindfulness": [
            {"english": "Be present in this moment.", "telugu": "ఈ క్షణంలో ఉన్నట్లు ఉండు.", "pronunciation": "ee ksha-nam-lo un-na-tlu un-du."},
            {"english": "Breathe deeply, stay grounded.", "telugu": "లోతుగా శ్వాసించు, నేలమీద నిలబడి ఉండు.", "pronunciation": "lo-tu-ga shvaa-sin-chu, ne-la-mee-da ni-la-ba-di un-du."},
            {"english": "Notice the little things around you.", "telugu": "నీ చుట్టూ ఉన్న చిన్న విషయాలను గమనించు.", "pronunciation": "nee chut-tu un-na chin-na vi-shay-aa-la-nu ga-ma-nin-chu."},
        ],
    }

    fallbacks = all_fallbacks.get(category, all_fallbacks["Motivation"])
    history = load_phrase_history()
    fresh_phrases = []
    for p in fallbacks:
        if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
            fresh_phrases.append(p)

    if len(fresh_phrases) < num_phrases:
        for cat, cat_fallbacks in all_fallbacks.items():
            if cat != category:
                for p in cat_fallbacks:
                    if not is_phrase_used(p["english"]) and not is_phrase_similar(p["english"], [h.get("english", "") for h in history.get("phrases", [])]):
                        fresh_phrases.append(p)
                    if len(fresh_phrases) >= num_phrases:
                        break
            if len(fresh_phrases) >= num_phrases:
                break

    return fresh_phrases[:num_phrases]


# ============== AUDIO GENERATION ==============

async def generate_single_audio(text: str, voice: str, output_path: str):
    try:
        import edge_tts
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"  TTS error: {e}")
        return False


def generate_all_audio(phrases: list, output_dir: str):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    audio_files = []

    for i, phrase in enumerate(phrases):
        english_file = output_dir / f"english_{i}.mp3"
        lang_file = output_dir / f"lang_{i}.mp3"
        combined_file = output_dir / f"combined_{i}.mp3"

        if (i + 1) % 20 == 0:
            print(f"  Generating audio {i+1}/{len(phrases)}...")

        en_success = asyncio.run(generate_single_audio(phrase["english"], ENGLISH_VOICE, str(english_file)))
        if not en_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(english_file)]
            subprocess.run(cmd, capture_output=True)

        lang_success = asyncio.run(generate_single_audio(phrase["telugu"], LANG_VOICE, str(lang_file)))
        if not lang_success:
            cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", "2", str(lang_file)]
            subprocess.run(cmd, capture_output=True)

        en_duration = get_audio_duration(str(english_file))
        lang_duration = get_audio_duration(str(lang_file))

        pause_between = 0.5
        total_duration = en_duration + pause_between + lang_duration

        cmd = [
            "ffmpeg", "-y",
            "-i", str(english_file),
            "-i", str(lang_file),
            "-filter_complex", f"[0:a][1:a]concat=n=2:v=0:a=1[out]",
            "-map", "[out]",
            str(combined_file)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            concat_file = output_dir / f"concat_{i}.txt"
            with open(concat_file, "w", encoding="utf-8") as f:
                f.write(f"file '{english_file.as_posix()}'\n")
                f.write(f"file '{lang_file.as_posix()}'\n")
            cmd = [
                "ffmpeg", "-y",
                "-f", "concat", "-safe", "0",
                "-i", str(concat_file),
                "-c:a", "aac",
                str(combined_file)
            ]
            subprocess.run(cmd, capture_output=True)
            if concat_file.exists():
                concat_file.unlink()

        actual_duration = get_audio_duration(str(combined_file))

        audio_files.append({
            "index": i,
            "english": str(english_file),
            "lang": str(lang_file),
            "combined": str(combined_file),
            "duration": actual_duration,
            "en_duration": en_duration,
            "lang_duration": lang_duration
        })

    print(f"\n[audio] Generated {len(audio_files)} phrase audios")
    return audio_files


def get_audio_duration(audio_file: str) -> float:
    if not Path(audio_file).exists():
        return 2.0
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_file]
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return float(result.stdout.strip())
    except:
        return 2.0


def create_final_narration(audio_files: list, output_file: str):
    n = len(audio_files)
    print(f"[audio] Combining {n} audio files...")
    concat_file = Path(output_file).parent / "narration_list.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for audio_info in audio_files:
            combined_path = Path(audio_info["combined"])
            if combined_path.exists():
                path_str = str(combined_path.resolve()).replace("\\", "/").replace("'", "'\\''")
                f.write(f"file '{path_str}'\n")
    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c:a", "copy", str(output_file)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if concat_file.exists():
        concat_file.unlink()
    if result.returncode == 0 and Path(output_file).exists() and Path(output_file).stat().st_size > 0:
        size = Path(output_file).stat().st_size
        print(f"\n[audio] Final narration: {Path(output_file).name} ({size/1024:.1f} KB)")
        return True
    return False


# ============== BACKGROUND GENERATION ==============

def create_premium_background(category_english: str):
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (VIDEO_WIDTH, VIDEO_HEIGHT))
    draw = ImageDraw.Draw(img)
    for y in range(VIDEO_HEIGHT):
        ratio = y / VIDEO_HEIGHT
        if ratio < 0.5:
            r, g, b = 255, 252, 245
        else:
            r = int(255 + (245 - 255) * ((ratio - 0.5) * 2))
            g = int(252 + (240 - 252) * ((ratio - 0.5) * 2))
            b = int(245 + (230 - 245) * ((ratio - 0.5) * 2))
        draw.rectangle([(0, y), (VIDEO_WIDTH, y + 1)], fill=(r, g, b))
    return img


def generate_complete_image(phrase_data: dict, category_english: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont, ImageFilter
    except ImportError:
        print("PIL not available. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    # Font paths - check fonts/ directory first
    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        str(BASE_DIR / "fonts" / "NotoSansTelugu-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    lang_font_paths = [
        str(BASE_DIR / "fonts" / "NotoSansTelugu-Bold.ttf"),
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
        return ImageFont.load_default()

    font_category = load_font(english_font_paths, 42)
    font_english = load_font(english_font_paths, 68)
    font_lang = load_font(lang_font_paths, 82)
    font_pronunciation = load_font(lang_font_paths, 48)
    font_branding = load_font(english_font_paths, 38)

    english = phrase_data.get("english", "")
    telugu = phrase_data.get("telugu", "")
    pronunciation = phrase_data.get("pronunciation", "")

    def wrap_text(text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] <= max_width:
                current_line.append(word)
            else:
                if current_line: lines.append(' '.join(current_line))
                current_line = [word]
        if current_line: lines.append(' '.join(current_line))
        return lines

    # Header Bar
    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_category)
    cat_w = cat_bbox[2] - cat_bbox[0]
    badge_h = 75
    badge_pad_x = 40
    container_w = cat_w + (badge_pad_x * 2)
    container_x = 60
    container_y = 60
    draw.rounded_rectangle(
        [(container_x, container_y), (container_x + container_w, container_y + badge_h)],
        radius=15, fill=(45, 35, 65, 255)
    )
    draw.text(
        (container_x + container_w // 2, container_y + badge_h // 2 + 2),
        cat_text,
        fill=(255, 255, 255, 255),
        font=font_category,
        anchor="mm"
    )

    CONTENT_Y_CENTER = VIDEO_HEIGHT // 2
    GAP = 60

    en_lines = wrap_text(english, font_english, VIDEO_WIDTH - 300)
    en_line_h = 80
    en_total_h = len(en_lines) * en_line_h

    lang_lines = wrap_text(telugu, font_lang, VIDEO_WIDTH - 300)
    lang_line_h = 100
    lang_total_h = len(lang_lines) * lang_line_h

    pron_text = f"[{pronunciation}]"
    pron_lines = wrap_text(pron_text, font_pronunciation, VIDEO_WIDTH - 400)
    pron_line_h = 60
    pron_total_h = len(pron_lines) * pron_line_h

    total_content_h = en_total_h + lang_total_h + pron_total_h + (GAP * 2)
    y_start = CONTENT_Y_CENTER - (total_content_h // 2)

    box_w = VIDEO_WIDTH - 200
    box_x = (VIDEO_WIDTH - box_w) // 2

    # English Box
    en_box_h = en_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_start), (box_x + box_w, y_start + en_box_h)],
        radius=25, fill=(65, 50, 95, 255)
    )
    for i, line in enumerate(en_lines):
        draw.text((VIDEO_WIDTH // 2, y_start + 30 + (i * en_line_h) + en_line_h // 2),
                  line, fill=(255, 255, 255), font=font_english, anchor="mm")

    y_cursor = y_start + en_box_h + GAP

    # Telugu Section
    lang_box_h = lang_total_h + 60
    draw.rounded_rectangle(
        [(box_x, y_cursor), (box_x + box_w, y_cursor + lang_box_h)],
        radius=25, fill=(95, 80, 125, 255)
    )
    for i, line in enumerate(lang_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 30 + (i * lang_line_h) + lang_line_h // 2),
                  line, fill=(255, 255, 255), font=font_lang, anchor="mm")

    y_cursor += lang_box_h + (GAP // 2)

    # Pronunciation Section
    pron_box_h = pron_total_h + 40
    pron_box_w = box_w - 200
    pron_box_x = (VIDEO_WIDTH - pron_box_w) // 2
    draw.rounded_rectangle(
        [(pron_box_x, y_cursor), (pron_box_x + pron_box_w, y_cursor + pron_box_h)],
        radius=20, fill=(255, 210, 160, 255)
    )
    for i, line in enumerate(pron_lines):
        draw.text((VIDEO_WIDTH // 2, y_cursor + 20 + (i * pron_line_h) + pron_line_h // 2),
                  line, fill=(70, 45, 25), font=font_pronunciation, anchor="mm")

    # Branding
    brand_text = "VELOCITY TELUGU"
    brand_bbox = draw.textbbox((0, 0), brand_text, font=font_branding)
    brand_w = brand_bbox[2] - brand_bbox[0]
    draw.text((VIDEO_WIDTH - brand_w - 60, VIDEO_HEIGHT - 80), brand_text,
              fill=(45, 35, 65, 255), font=font_branding)

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


# ============== THUMBNAIL GENERATION ==============

def generate_thumbnail(category_english: str, category_telugu: str, output_path: str):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("PIL not available for thumbnail. Install: pip install Pillow")
        return None

    img = create_premium_background(category_english)
    img = img.convert('RGBA')
    draw = ImageDraw.Draw(img)

    english_font_paths = [
        str(BASE_DIR / "fonts" / "DejaVuSans-Bold.ttf"),
        "C:/Windows/Fonts/segoeuib.ttf",
        "C:/Windows/Fonts/arialbd.ttf",
    ]
    lang_font_paths = [
        str(BASE_DIR / "fonts" / "NotoSansTelugu-Bold.ttf"),
        "C:/Windows/Fonts/arialbd.ttf",
    ]

    def load_font(font_paths, size):
        for font_path in font_paths:
            try: return ImageFont.truetype(font_path, size)
            except: continue
        return ImageFont.load_default()

    font_huge = load_font(english_font_paths, 130)
    font_main = load_font(lang_font_paths, 110)
    font_sub = load_font(english_font_paths, 60)
    font_badge = load_font(english_font_paths, 45)

    draw.text((VIDEO_WIDTH // 2, 220), "MASTER TELUGU", fill=(45, 35, 65), font=font_huge, anchor="mm")

    cat_text = category_english.upper()
    cat_bbox = draw.textbbox((0, 0), cat_text, font=font_sub)
    cat_w = cat_bbox[2] - cat_bbox[0]
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - cat_w // 2 - 40, 320), (VIDEO_WIDTH // 2 + cat_w // 2 + 40, 410)],
        radius=20, fill=(65, 50, 95, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 365), cat_text, fill=(255, 255, 255), font=font_sub, anchor="mm")

    draw.text((VIDEO_WIDTH // 2, 530), category_telugu, fill=(45, 35, 65), font=font_main, anchor="mm")

    cta_text = "60 ESSENTIAL PHRASES"
    draw.rounded_rectangle(
        [(VIDEO_WIDTH // 2 - 300, 650), (VIDEO_WIDTH // 2 + 300, 730)],
        radius=15, fill=(255, 210, 160, 255)
    )
    draw.text((VIDEO_WIDTH // 2, 690), cta_text, fill=(70, 45, 25), font=font_badge, anchor="mm")

    draw.rectangle([(0, VIDEO_HEIGHT - 100), (VIDEO_WIDTH, VIDEO_HEIGHT)], fill=(45, 35, 65, 255))
    draw.text((VIDEO_WIDTH // 2, VIDEO_HEIGHT - 50), "VELOCITY TELUGU", fill=(255, 255, 255), font=font_badge, anchor="mm")

    img = img.convert('RGB')
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(output_path, quality=95, optimize=True)
    return output_path


def extract_video_thumbnail(video_path: str, output_path: str, timestamp_seconds: int = 5):
    try:
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(timestamp_seconds),
            "-i", str(video_path),
            "-vframes", "1",
            "-q:v", "2",
            str(output_path)
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and Path(output_path).exists():
            print(f"  Video thumbnail extracted: {Path(output_path).name}")
            return str(output_path)
        else:
            print(f"  Could not extract video thumbnail")
            return None
    except Exception as e:
        print(f"  Thumbnail extraction error: {e}")
        return None


# ============== TITLE & DESCRIPTION GENERATION ==============

def generate_title_description(category_english: str, category_telugu: str, phrases: list, duration_minutes: float, output_dir: str):
    titles = [
        f"Learn Telugu in 10 Minutes | {category_english} Phrases Every Beginner NEEDS to Know! ({category_telugu})",
        f"60 Telugu Phrases for {category_english} | Speak Telugu Like a Native! ({category_telugu})",
        f"Master Telugu {category_english} | 60 Essential Telugu Phrases with Pronunciation | Velocity Telugu",
        f"Telugu Learning Made Easy | {category_english} Vocabulary | 10 Minute Lesson",
        f"Speak Telugu Fluently | {category_english} Phrases | English + Telugu + Pronunciation",
    ]

    description = f"""🇮🇳 Learn Telugu with Velocity Telugu! 🇮🇳

In this video, you'll learn 60 essential Telugu phrases about {category_english} ({category_telugu}).
Perfect for beginners and intermediate learners!

📚 WHAT YOU'LL LEARN:
• 60 practical {category_english} phrases in Telugu
• Correct pronunciation guide
• Natural pauses for speaking practice
• Common expressions used by native speakers

⏱️ VIDEO TIMESTAMPS:
"""

    avg_phrase_duration = duration_minutes * 60 / len(phrases)
    for i in range(0, len(phrases), 10):
        timestamp = int(i * avg_phrase_duration / 60)
        minute = timestamp
        second = int((i * avg_phrase_duration) % 60)
        end_phrase = min(i + 10, len(phrases))
        description += f"{minute:02d}:{second:02d} Phrases {i+1}-{end_phrase}\n"

    description += """
📝 ALL PHRASES IN THIS VIDEO:
"""

    for i, phrase in enumerate(phrases, 1):
        description += f"""
{i}. {phrase['english']}
   Telugu: {phrase['telugu']}
   Pronunciation: {phrase['pronunciation']}
"""

    description += """
🎯 PERFECT FOR:
• Telugu beginners wanting to expand vocabulary
• Intermediate learners practicing pronunciation
• Anyone interested in Telugu language and culture
• Language enthusiasts and polyglots
• Students preparing for exams

💡 TIPS FOR LEARNING:
1. Repeat each phrase out loud
2. Practice daily for best results
3. Use the pauses to speak along
4. Write down phrases you find difficult
5. Review this video multiple times

🔔 SUBSCRIBE for more Telugu learning content!
👍 LIKE this video if you found it helpful!
💬 COMMENT which phrases you want to learn next!

📱 FOLLOW VELOCITY TELUGU:
[Add your social media links here]

🎵 MUSIC:
[Add music credits if applicable]

📖 RELATED VIDEOS:
• Telugu Motivation Phrases
• Telugu Love Expressions
• Basic Telugu Greetings

#LearnTelugu #TeluguPhrases #TeluguLanguage #{category_english.replace(' ', '')} #VelocityTelugu #TeluguForBeginners #SpeakTelugu #TeluguVocabulary #Pronunciation #LanguageLearning #Telugu101 #TeluguLesson

---
© Velocity Telugu - Making Telugu learning accessible to everyone!
"""

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "youtube_upload_info.txt", "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("YOUTUBE VIDEO UPLOAD INFORMATION\n")
        f.write("=" * 80 + "\n\n")
        f.write("RECOMMENDED TITLES (Choose one):\n")
        f.write("-" * 80 + "\n")
        for i, title in enumerate(titles, 1):
            f.write(f"\n{i}. {title}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("SELECTED TITLE (Recommended):\n")
        f.write("-" * 80 + "\n")
        f.write(f"\n{titles[0]}\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO DESCRIPTION:\n")
        f.write("-" * 80 + "\n\n")
        f.write(description)
        f.write("\n" + "=" * 80 + "\n")
        f.write("VIDEO TAGS (for YouTube):\n")
        f.write("-" * 80 + "\n")
        tags = [
            "Learn Telugu",
            "Telugu Phrases",
            "Telugu Language",
            category_english,
            "Velocity Telugu",
            "Telugu for Beginners",
            "Speak Telugu",
            "Telugu Vocabulary",
            "Pronunciation",
            "Language Learning",
            "Telugu 101",
            "Telugu Lesson"
        ]
        f.write(", ".join(tags) + "\n")

    metadata = {
        "recommended_titles": titles,
        "selected_title": titles[0],
        "description": description,
        "category_english": category_english,
        "category_telugu": category_telugu,
        "phrases_count": len(phrases),
        "duration_minutes": round(duration_minutes, 2),
        "tags": tags
    }

    with open(output_dir / "video_metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"\n[metadata] Generated YouTube upload files")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  video_metadata.json")

    return metadata


# ============== VIDEO CREATION ==============

def create_video_from_images_audio(image_files: list, audio_files: list, combined_audio: str, output_file: str):
    print(f"\n[video] Creating long-form video from {len(image_files)} images...")

    temp_clips = []

    for i, (img_path, audio_info) in enumerate(zip(image_files, audio_files)):
        duration = audio_info['duration']
        print(f"  Image {i+1}/{len(image_files)}: {duration:.2f}s")

        temp_clip = Path(output_file).parent / f"temp_clip_{i:02d}.mp4"
        temp_clips.append(temp_clip)

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(img_path),
            "-i", audio_info['combined'],
            "-vf", f"scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:force_original_aspect_ratio=decrease,pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,fps={FPS}",
            "-c:v", "libx264",
            "-c:a", "aac",
            "-b:a", "128k",
            "-pix_fmt", "yuv420p",
            "-preset", "medium",
            "-shortest",
            "-vsync", "cfr",
            str(temp_clip)
        ]

        subprocess.run(cmd, check=True, capture_output=True)

    print("[video] Concatenating clips...")
    concat_file = Path(output_file).parent / "concat_list.txt"

    with open(concat_file, "w", encoding="utf-8") as f:
        for clip in temp_clips:
            f.write(f"file '{clip.resolve().as_posix()}'\n")

    cmd = ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file), "-c", "copy", str(output_file)]
    subprocess.run(cmd, check=True, capture_output=True)

    if concat_file.exists():
        concat_file.unlink()

    video_duration = get_audio_duration(str(output_file))
    print(f"[video] Video created: {Path(output_file).name} ({video_duration:.2f}s)")

    for clip in temp_clips:
        if clip.exists():
            clip.unlink()


# ============== MAIN WORKFLOW ==============

def generate_longform_video(category_english: str = None, target_phrases: int = None):
    if not category_english:
        category_english = random.choice(CATEGORIES_ENGLISH)

    phrases_count = target_phrases if target_phrases else TARGET_PHRASES

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO - Category: {category_english} ({CATEGORIES_TELUGU[category_english]})")
    print(f"Target Phrases: {phrases_count}")
    print(f"{'='*80}\n")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    video_dir = LONGFORM_DIR / f"{category_english}_longform_{timestamp}"
    video_dir.mkdir(exist_ok=True)

    print(f"[1/6] Generating {phrases_count} unique phrases (checking history)...")
    phrases = generate_phrases_for_longform(category_english, phrases_count)

    for i, phrase in enumerate(phrases, 1):
        print(f"  {i}. {phrase['english']} -> {phrase['telugu']}")

    print(f"\n[info] Total phrases: {len(phrases)}")

    print(f"\n[2/6] Generating {len(phrases)} images with premium backgrounds...")
    for i, phrase in enumerate(phrases):
        output_path = video_dir / f"phrase_{i:04d}.jpg"
        generate_complete_image(phrase, category_english, str(output_path))
        if (i + 1) % 10 == 0:
            print(f"  Progress: {i+1}/{len(phrases)} images...")

    print(f"\n[3/6] Generating thumbnail...")
    thumbnail_path = video_dir / "thumbnail.jpg"
    try:
        from generate_thumbnail import generate_scenic_image
        result = generate_scenic_image(category_english, category_english, str(thumbnail_path))
        if result and Path(result).exists():
            print(f"  gpt-image-2 thumbnail saved")
        else:
            print(f"  gpt-image-2 failed, using built-in")
            generate_thumbnail(category_english, CATEGORIES_TELUGU[category_english], str(thumbnail_path))
    except Exception as e:
        print(f"  Thumbnail error: {e}, using built-in")
        generate_thumbnail(category_english, CATEGORIES_TELUGU[category_english], str(thumbnail_path))

    video_thumbnail_path = video_dir / "video_thumbnail_frame.jpg"

    print(f"\n[4/6] Generating audio for {len(phrases)} phrases...")
    audio_files = generate_all_audio(phrases, str(video_dir))

    final_audio = video_dir / "narration.mp3"
    create_final_narration(audio_files, str(final_audio))

    total_duration = sum(a['duration'] for a in audio_files)
    print(f"\n[info] Total audio duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")

    print(f"\n[5/6] Creating long-form video with transitions...")
    output_video = video_dir / "final_video.mp4"

    image_files = sorted([str(p) for p in video_dir.glob("phrase_*.jpg")])

    create_video_from_images_audio(
        image_files,
        audio_files,
        str(final_audio),
        str(output_video)
    )

    print(f"\n[5.5/6] Extracting video frame for thumbnail...")
    extract_video_thumbnail(str(output_video), str(video_thumbnail_path), timestamp_seconds=5)

    print(f"\n[6/6] Generating YouTube title, description, and metadata...")
    title_meta = generate_title_description(
        category_english,
        CATEGORIES_TELUGU[category_english],
        phrases,
        total_duration / 60,
        str(video_dir)
    )

    import json as _json
    from pathlib import Path as _Path
    meta_out = {
        "title": title_meta.get("selected_title", f"Learn Telugu: {category_english}"),
        "description": title_meta.get("description", ""),
        "tags": ["Learn Telugu", "Telugu Phrases", "Telugu", category_english, "Velocity Telugu"],
        "category_english": category_english,
        "category_telugu": CATEGORIES_TELUGU[category_english],
        "phrases_count": len(phrases),
        "duration_seconds": total_duration,
        "duration_minutes": total_duration / 60,
        "video_path": str(output_video),
        "thumbnail_path": str(thumbnail_path),
        "phrases": phrases,
        "generated_at": datetime.now().isoformat(),
    }
    _Path("output").mkdir(exist_ok=True)
    with open(_Path("output") / "latest_video.json", "w", encoding="utf-8") as f:
        _json.dump(meta_out, f, indent=2, ensure_ascii=False)
    with open(_Path("output") / "latest_upload_info.json", "w", encoding="utf-8") as f:
        _json.dump({"title": meta_out["title"], "description": meta_out["description"],
                     "category": category_english, "phrases_count": len(phrases)}, f, indent=2)

    print(f"\n{'='*80}")
    print(f"LONG-FORM VIDEO COMPLETE!")
    print(f"  {video_dir}")
    print(f"  {output_video.name}")
    print(f"  thumbnail.jpg (generated)")
    print(f"  {video_thumbnail_path.name} (from video)")
    print(f"  youtube_upload_info.txt (title + description + tags)")
    print(f"  Duration: {total_duration/60:.2f} minutes")
    print(f"  Phrases: {len(phrases)}")
    print(f"  Branding: Velocity Telugu")
    print(f"  Format: 16:9 (1920x1080)")
    print(f"{'='*80}\n")

    return meta_out


def generate_multiple_longform(count: int = 1, target_phrases: int = None):
    print(f"\nGenerating {count} long-form video(s)...")
    print("="*80)
    for i in range(count):
        print(f"\n{'='*80}")
        print(f"VIDEO {i+1}/{count}")
        print("="*80)
        generate_longform_video(target_phrases=target_phrases)
    print("\n" + "="*80)
    print(f"ALL {count} LONG-FORM VIDEOS COMPLETE!")
    print("="*80)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Velocity Telugu YouTube Long-form Video Generator")
    parser.add_argument("--phrases", type=int, default=TARGET_PHRASES, help="Number of phrases to generate")
    parser.add_argument("--category", type=str, default=None, help="Specific category to generate")
    args = parser.parse_args()

    print("\n" + "="*80)
    print("VELOCITY TELUGU - YOUTUBE LONG-FORM AUTOMATION")
    print("="*80)
    print("\nFEATURES:")
    print("  16:9 format (1920x1080) for YouTube long-form")
    print(f"  Target {args.phrases} phrases (~{args.phrases * 5.5 / 60:.1f} minute video)")
    print("  Light Theme (Cream background, dark/light purple + peach containers)")
    print("  Natural pauses with commas (non-robotic TTS)")
    print("  Perfect audio-video synchronization")
    print("  NEVER repeats phrases (permanent history tracking)")
    print(f"\nAVAILABLE CATEGORIES ({len(CATEGORIES_ENGLISH)} total):")
    for i, cat in enumerate(CATEGORIES_ENGLISH, 1):
        print(f"   {i:2d}. {cat} ({CATEGORIES_TELUGU[cat]})")
    print(f"\nVIDEO SPECIFICATIONS:")
    print(f"  Resolution: {VIDEO_WIDTH}x{VIDEO_HEIGHT} (16:9)")
    print(f"  Frame Rate: {FPS} FPS")
    print(f"  Target Phrases: {args.phrases}")
    print(f"  Estimated Duration: ~{args.phrases * 5.5 / 60:.1f} minutes")
    print(f"  Phrase History: PERMANENT (never deletes)")
    print("="*80)

    generate_longform_video(category_english=args.category, target_phrases=args.phrases)
