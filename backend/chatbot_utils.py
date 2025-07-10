# chatbot_utils.py

import os
import json
import base64
import requests
from dotenv import load_dotenv
from language_utils import get_script_code
import time

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
    try:
        rsp = requests.post(BHASHINI_PIPELINE_URL, headers=HEADERS, json=payload, timeout=60)
        if rsp.status_code != 200:
            rsp.raise_for_status()
        return rsp.json()
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        raise

def detect_language(audio_b64: str) -> str:
    """Detect the language of the audio input using Bhashini's audio-lang-detection service."""
    print(f"[LANGUAGE DETECTION] Processing audio...")

    url = os.getenv("BHASHINI_PIPELINE_URL", "https://dhruva-api.bhashini.gov.in/services/inference/pipeline")
    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "user_id": ULCA_USER_ID,
        "api-key": ULCA_API_KEY,
        "Authorization": BHASHINI_AUTH_TOKEN,
    }
    payload = {
        "pipelineTasks": [
            {
                "taskType": "audio-lang-detection",
                "config": {
                    "serviceId": "bhashini/iitmandi/audio-lang-detection/gpu"
                }
            }
        ],
        "inputData": {
            "audio": [
                {"audioContent": audio_b64}
            ]
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            response_json = response.json()
            pipeline_response = response_json.get("pipelineResponse", [])
            if pipeline_response:
                output_data = pipeline_response[0].get("output", [])
                if output_data:
                    lang_pred = output_data[0].get("langPrediction", [])
                    if lang_pred and isinstance(lang_pred, list):
                        lang_code = lang_pred[0].get("langCode")
                        print(f"[LANGUAGE DETECTION] Detected: {lang_code}")
                        return lang_code
                    else:
                        print("[LANGUAGE DETECTION] No language prediction found in response.")
                else:
                    print("[LANGUAGE DETECTION] No output data found in response.")
            else:
                print("[LANGUAGE DETECTION] No pipeline response found.")
        else:
            print(f"[LANGUAGE DETECTION] Error: {response.text}")
    except Exception as e:
        print(f"[LANGUAGE DETECTION ERROR] {e}")
    print("[LANGUAGE DETECTION] Falling back to English")
    return "en"

def bhashini_asr_gemini_tts(audio_b64: str, gender: str = "female") -> dict:
    """Process audio with automatic language detection, ASR, Gemini AI, and TTS."""
    if gender.lower() not in {"female", "male"}:
        gender = "female"

    print(f"[PROCESSING] Starting pipeline with gender={gender}")
    print(f"[DEBUG] Audio base64 length: {len(audio_b64)}")

    # Step 0: Language Detection
    detected_lang = detect_language(audio_b64)
    print(f"[DEBUG] Using detected language: {detected_lang}")

    # Choose serviceId based on detected language
    if detected_lang == "en":
        asr_service_id = "ai4bharat/whisper-medium-en--gpu--t4"
    elif detected_lang in ["hi", "bn"]:
        asr_service_id = "bhashini/ai4bharat/conformer-multilingual-asr"
    elif detected_lang in ["mr", "ur", "or", "pa", "gu", "sa", "sd"]:
        asr_service_id = "ai4bharat/conformer-multilingual-indo_aryan-gpu--t4"
    elif detected_lang in ["te", "kn", "ml", "ta"]:
        asr_service_id = "ai4bharat/conformer-multilingual-dravidian-gpu--t4"
    else:
        asr_service_id = "bhashini/ai4bharat/conformer-multilingual-asr"  # fallback
    print(f"[ASR] Using language: {detected_lang} (service: {asr_service_id})")

    # Step 1: ASR with WAV format
    asr_payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {
                    "language": {"sourceLanguage": detected_lang},
                    "serviceId": asr_service_id,
                    "audioFormat": "wav",
                    "samplingRate": 16000
                }
            }
        ],
        "inputData": {
            "audio": [{"audioContent": audio_b64}]
        }
    }
    print(f"[DEBUG] ASR Payload: {asr_payload}")

    start = time.time()
    asr_response = _pipeline_request(asr_payload)
    elapsed = int((time.time() - start) * 1000)
    print(f"[ASR] Status: 200, Time: {elapsed}ms")
    print("[DEBUG] ASR Response:", json.dumps(asr_response, indent=2))
    pipeline_response = asr_response.get("pipelineResponse", [])
    if not pipeline_response:
        raise ValueError("ASR pipeline response is empty")
    output_data = pipeline_response[0].get("output", [])
    if not output_data:
        raise ValueError("ASR output is missing")
    transcription = output_data[0].get("source")
    if not transcription:
        raise ValueError("Transcription is empty")
    print(f"[ASR] Transcription: {transcription}")

    # Step 2: Gemini
    gemini_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    gemini_payload = {
        "contents": [{"parts": [{"text": transcription}]}]
    }
    print(f"[DEBUG] Gemini Payload: {gemini_payload}")
    reply = ""
    start = time.time()
    gemini_rsp = requests.post(
        f"{gemini_url}?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json=gemini_payload
    )
    elapsed = int((time.time() - start) * 1000)
    print(f"[GEMINI] Status: {gemini_rsp.status_code}, Time: {elapsed}ms")
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
    print(f"[GEMINI] Response: {reply}")

    # Step 3: TTS returning WAV
    if detected_lang in ["en", "hi", "bn"]:
        tts_service_id = "Bhashini/IITM/TTS"
    else:
        tts_service_id = "ai4bharat/indic-tts-coqui-indo_aryan-gpu--t4"  # fallback for other languages
    print(f"[TTS] Using language: {detected_lang} (service: {tts_service_id})")
    tts_payload = {
        "pipelineTasks": [
            {
                "taskType": "tts",
                "config": {
                    "language": {
                        "sourceLanguage": detected_lang
                    },
                    "serviceId": tts_service_id,
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
    print(f"[DEBUG] TTS Payload: {tts_payload}")
    start = time.time()
    tts_response = _pipeline_request(tts_payload)
    elapsed = int((time.time() - start) * 1000)
    print(f"[TTS] Status: 200, Time: {elapsed}ms")
    print("[DEBUG] TTS Response:", json.dumps(tts_response, indent=2))
    for task in tts_response.get("pipelineResponse", []):
        if task.get("taskType") == "tts":
            audio_list = task.get("audio")
            if audio_list and isinstance(audio_list, list):
                audio_b64 = audio_list[0].get("audioContent")
                if audio_b64:
                    print(f"[TTS] Audio generated successfully")
                    return {
                        "text": reply,
                        "audio_base64": audio_b64,
                        "detected_language": detected_lang
                    }
    raise RuntimeError("TTS failed: No audioContent returned.")