# chatbot_utils.py

import os
import json
import base64
import requests
from dotenv import load_dotenv
from language_utils import get_script_code

load_dotenv()

ULCA_USER_ID = os.getenv("ULCA_USER_ID")
ULCA_API_KEY = os.getenv("ULCA_API_KEY")
BHASHINI_AUTH_TOKEN = os.getenv("BHASHINI_AUTH_TOKEN")
BHASHINI_PIPELINE_URL = os.getenv("BHASHINI_PIPELINE_URL")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not all([ULCA_USER_ID, ULCA_API_KEY, BHASHINI_AUTH_TOKEN, BHASHINI_PIPELINE_URL, GEMINI_API_KEY]):
    raise EnvironmentError("❌ Missing one or more environment variables.")

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "*/*",
    "user_id": ULCA_USER_ID,
    "api-key": ULCA_API_KEY,
    "Authorization": BHASHINI_AUTH_TOKEN,
}

def _pipeline_request(payload: dict) -> dict:
    rsp = requests.post(BHASHINI_PIPELINE_URL, headers=HEADERS, json=payload, timeout=60)
    rsp.raise_for_status()
    return rsp.json()

def bhashini_asr_gemini_tts(audio_b64: str, lang: str, gender: str = "female") -> dict:
    if gender.lower() not in {"female", "male"}:
        gender = "female"

    # Step 1: ASR with WAV format
    asr_payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {
                    "language": {"sourceLanguage": lang},
                    "serviceId": "bhashini/ai4bharat/conformer-multilingual-asr",
                    "audioFormat": "wav",
                    "samplingRate": 16000
                }
            }
        ],
        "inputData": {
            "audio": [{"audioContent": audio_b64}]
        }
    }

    try:
        asr_response = _pipeline_request(asr_payload)
        print("[DEBUG] ASR Response:", json.dumps(asr_response, indent=2))
        output_data = asr_response.get("pipelineResponse", [])[0].get("output", [])
        if not output_data:
            raise ValueError("ASR output is missing")
        transcription = output_data[0].get("source")
        if not transcription:
            raise ValueError("Transcription is empty")
    except Exception as e:
        print("[ASR ERROR]", e)
        raise RuntimeError("ASR failed")

    # Step 2: Gemini
    gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    gemini_payload = {
        "contents": [{"parts": [{"text": transcription}]}]
    }
    reply = ""
    try:
        gemini_rsp = requests.post(
            f"{gemini_url}?key={GEMINI_API_KEY}",
            headers={"Content-Type": "application/json"},
            json=gemini_payload
        )
        gemini_rsp.raise_for_status()
        gemini_json = gemini_rsp.json()
        print("[DEBUG] Gemini response:", json.dumps(gemini_json, indent=2))

        candidates = gemini_json.get("candidates", [])
        if candidates:
            parts = candidates[0].get("content", {}).get("parts", [])
            if parts:
                reply = parts[0].get("text", "").strip()

        if not reply:
            raise RuntimeError("Gemini AI returned no valid reply.")
    except Exception as e:
        print("[GEMINI ERROR]", e)
        raise RuntimeError("Gemini AI failed to generate response")

    # Step 3: TTS returning WAV
    tts_payload = {
        "pipelineTasks": [
            {
                "taskType": "tts",
                "config": {
                    "language": {
                        "sourceLanguage": lang
                    },
                    "serviceId": "Bhashini/IITM/TTS",
                    "gender": gender,
                    "samplingRate": 16000
                }
            }
        ],
        "inputData": {
            "input": [
                {"source": reply}
            ]
        }
    }

    try:
        tts_response = _pipeline_request(tts_payload)
        print("[DEBUG] TTS Response:", json.dumps(tts_response, indent=2))

        for task in tts_response.get("pipelineResponse", []):
            if task.get("taskType") == "tts":
                audio_list = task.get("audio")
                if audio_list and isinstance(audio_list, list):
                    audio_b64 = audio_list[0].get("audioContent")
                    if audio_b64:
                        return {
                            "text": reply,
                            "audio_base64": audio_b64
                        }

        raise RuntimeError("TTS failed: No audioContent returned.")
    except Exception as e:
        print("[TTS ERROR]", e)
        raise RuntimeError("TTS failed")