import os
import json
import base64
from collections import defaultdict
from io import BytesIO

import requests
from dotenv import load_dotenv
from pydub import AudioSegment   # pip install pydub
# ──────────────────────────────────────────────────────────────────────────────
#  Environment & constants
# ──────────────────────────────────────────────────────────────────────────────
load_dotenv()

ULCA_USER_ID         = os.getenv("ULCA_USER_ID")
ULCA_API_KEY         = os.getenv("ULCA_API_KEY")
BHASHINI_AUTH_TOKEN  = os.getenv("BHASHINI_AUTH_TOKEN")
BHASHINI_PIPELINE_URL = os.getenv("BHASHINI_PIPELINE_URL")      # e.g.
# https://dhruva-api.bhashini.gov.in/services/inference/pipeline

if not all([ULCA_USER_ID, ULCA_API_KEY, BHASHINI_AUTH_TOKEN, BHASHINI_PIPELINE_URL]):
    raise EnvironmentError(
        "❌  Missing one or more env vars: "
        "ULCA_USER_ID, ULCA_API_KEY, BHASHINI_AUTH_TOKEN, BHASHINI_PIPELINE_URL"
    )

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "*/*",
    "user_id": ULCA_USER_ID,
    "api-key": ULCA_API_KEY,
    "Authorization": BHASHINI_AUTH_TOKEN,
}

# ──────────────────────────────────────────────────────────────────────────────
#  Dynamic language‑to‑script map (falls back to Latin)
# ──────────────────────────────────────────────────────────────────────────────
SCRIPT_MAP = defaultdict(lambda: "Latn")


def _fetch_supported_languages() -> dict:
    """Build {lang_code: script_code} from Bhashini registry."""
    url = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    try:
        rsp = requests.post(url, headers={"Authorization": BHASHINI_AUTH_TOKEN}, json={})
        rsp.raise_for_status()
        lang_map = {}
        for pipe in rsp.json().get("pipelineModels", []):
            for lang in pipe.get("languages", []):
                lang_code   = lang.get("sourceLanguage")
                script_code = lang.get("sourceScriptCode")
                if lang_code and script_code:
                    lang_map[lang_code] = script_code
        return lang_map
    except Exception as err:
        print(f"⚠️  Could not fetch language map: {err}")
        return {}


SCRIPT_MAP.update(_fetch_supported_languages())


def get_script_code(lang: str) -> str:
    """Return ISO‑15924 script code; defaults to Latin."""
    return SCRIPT_MAP[lang]


# ──────────────────────────────────────────────────────────────────────────────
#  Core wrapper
# ──────────────────────────────────────────────────────────────────────────────
def _pipeline_request(payload: dict) -> dict:
    rsp = requests.post(BHASHINI_PIPELINE_URL, headers=HEADERS, json=payload, timeout=60)
    rsp.raise_for_status()
    return rsp.json()
#  Composite helper: SPEECH ➜ TEXT ➜ TEXT ➜ SPEECH
# ──────────────────────────────────────────────────────────────────────────────
def bhashini_asr_nmt_tts(audio_b64: str, src_asr_lang: str,
                         tgt_lang: str, gender: str = "female") -> str:
    """Speech → Transcription → Translation → Speech (Base64 output)"""

    if src_asr_lang == tgt_lang:
        raise ValueError("Source and target languages must differ for ASR+NMT+TTS")

    if gender.lower() not in {"female", "male"}:
        gender = "female"

    payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {
                    "language": {
                        "sourceLanguage": src_asr_lang
                    },
                    "serviceId": "bhashini/ai4bharat/conformer-multilingual-asr",
                    "audioFormat": "flac",
                    "samplingRate": 16000
                }
            },
            {
                "taskType": "translation",
                "config": {
                    "language": {
                        "sourceLanguage": src_asr_lang,
                        "targetLanguage": tgt_lang
                    },
                    "serviceId": "ai4bharat/indictrans-v2-all-gpu--t4"
                }
            },
            {
                "taskType": "tts",
                "config": {
                    "language": {
                        "sourceLanguage": tgt_lang
                    },
                    "serviceId": "ai4bharat/indic-tts-coqui-indo_aryan-gpu--t4",
                    "gender": gender,
                    "samplingRate": 8000
                }
            }
        ],
        "inputData": {
            "audio": [{"audioContent": audio_b64}]
        }
    }

    rsp = _pipeline_request(payload)

    # Traverse the pipeline response
    for task in rsp.get("pipelineResponse", []):
        if task.get("taskType") == "tts":
            audio_list = task.get("audio", []) or []
            if not audio_list or not audio_list[0].get("audioContent"):
                raise RuntimeError("TTS failed: No audio content returned.")
            return audio_list[0]["audioContent"]

    raise RuntimeError("ASR+NMT+TTS failed: No audio content found in response.")


# ------------------------------------------------------------------------------
#  Utilities
# ------------------------------------------------------------------------------

def _save_mp3(b64_string: str, filename: str) -> None:
    """Helper to quickly drop MP3 files for debugging."""
    audio_bytes = base64.b64decode(b64_string)
    AudioSegment.from_file(BytesIO(audio_bytes), format="mp3").export(filename, format="mp3")
