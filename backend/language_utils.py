import requests
from functools import lru_cache

# Language code to name mapping
LANG_CODE_TO_NAME = {
    "as": "Assamese",
    "bn": "Bengali",
    "brx": "Bodo",
    "doi": "Dogri",
    "en": "English",
    "gu": "Gujarati",
    "hi": "Hindi",
    "kn": "Kannada",
    "ks": "Kashmiri",
    "kok": "Konkani",
    "mai": "Maithili",
    "ml": "Malayalam",
    "mni": "Manipuri",
    "mr": "Marathi",
    "ne": "Nepali",
    "or": "Odia",
    "pa": "Punjabi",
    "sa": "Sanskrit",
    "sat": "Santali",
    "sd": "Sindhi",
    "ta": "Tamil",
    "te": "Telugu",
    "ur": "Urdu"
}

# Reverse map: name to code
NAME_TO_LANG_CODE = {v: k for k, v in LANG_CODE_TO_NAME.items()}

# ISO 15924 script codes
SCRIPT_CODES = {
    "as": "Beng", "bn": "Beng", "brx": "Deva", "doi": "Deva",
    "en": "Latn", "gu": "Gujr", "hi": "Deva", "kn": "Knda",
    "ks": "Arab", "kok": "Deva", "mai": "Deva", "ml": "Mlym",
    "mni": "Beng", "mr": "Deva", "ne": "Deva", "or": "Orya",
    "pa": "Guru", "sa": "Deva", "sat": "Olck", "sd": "Arab",
    "ta": "Taml", "te": "Telu", "ur": "Arab"
}

def get_script_code(lang_code):
    """Return ISO 15924 script code for a language code."""
    return SCRIPT_CODES.get(lang_code, "Deva")  # default to Devanagari

def get_lang_name(code):
    """Return human-readable name from language code."""
    return LANG_CODE_TO_NAME.get(code, f"Unknown({code})")

def get_lang_code(name):
    """Return language code from human-readable name."""
    return NAME_TO_LANG_CODE.get(name.strip().capitalize(), "en")

@lru_cache(maxsize=1)
def fetch_available_translation_pairs():
    """Fetch all supported source-target translation pairs from ULCA."""
    url = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    payload = {
        "pipelineTasks": [
            {
                "taskType": "translation",
                "config": {
                    "language": {
                        "sourceLanguage": "",
                        "targetLanguage": ""
                    }
                }
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        data = response.json()
        available_languages = {
            (item["config"]["language"]["sourceLanguage"],
             item["config"]["language"]["targetLanguage"])
            for item in data.get("pipelineResponse", [])
            if item.get("config", {}).get("language", {}).get("sourceLanguage") and
               item.get("config", {}).get("language", {}).get("targetLanguage")
        }
        return sorted(available_languages)
    except Exception as e:
        print(f"[Translation] Failed to fetch language pairs: {e}")
        return []

@lru_cache(maxsize=1)
def fetch_available_tts_languages():
    """Fetch all languages supported for Text-to-Speech (TTS)."""
    url = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    payload = {
        "pipelineTasks": [
            {
                "taskType": "tts",
                "config": {
                    "language": {
                        "sourceLanguage": ""
                    }
                }
            }
        ]
    }

    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        data = response.json()
        languages = {
            item["config"]["language"]["sourceLanguage"]
            for item in data.get("pipelineResponse", [])
            if item.get("config", {}).get("language", {}).get("sourceLanguage")
        }
        return sorted(languages)
    except Exception as e:
        print(f"[TTS] Failed to fetch TTS languages: {e}")
        return []