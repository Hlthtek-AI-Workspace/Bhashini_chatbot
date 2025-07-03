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
    print(f"[DEBUG] Making request to: {BHASHINI_PIPELINE_URL}")
    print(f"[DEBUG] Headers: {json.dumps(HEADERS, indent=2)}")
    print(f"[DEBUG] Payload: {json.dumps(payload, indent=2)}")
    
    try:
        rsp = requests.post(BHASHINI_PIPELINE_URL, headers=HEADERS, json=payload, timeout=60)
        print(f"[DEBUG] Response status: {rsp.status_code}")
        print(f"[DEBUG] Response headers: {dict(rsp.headers)}")
        
        if rsp.status_code != 200:
            print(f"[DEBUG] Error response body: {rsp.text}")
            rsp.raise_for_status()
            
        return rsp.json()
    except requests.exceptions.RequestException as e:
        print(f"[DEBUG] Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[DEBUG] Error response: {e.response.text}")
        raise

def bhashini_asr_gemini_tts(audio_b64: str, lang: str, gender: str = "female") -> dict:
    if gender.lower() not in {"female", "male"}:
        gender = "female"

    print(f"[DEBUG] Processing audio with lang={lang}, gender={gender}")
    print(f"[DEBUG] Audio base64 length: {len(audio_b64)}")

    # Choose serviceId based on language
    if lang == "en":
        asr_service_id = "ai4bharat/whisper-medium-en--gpu--t4"
    elif lang in ["hi", "bn"]:
        asr_service_id = "bhashini/ai4bharat/conformer-multilingual-asr"
    elif lang in ["mr", "ur", "or", "pa", "gu", "sa", "sd"]:
        asr_service_id = "ai4bharat/conformer-multilingual-indo_aryan-gpu--t4"
    elif lang in ["te", "kn", "ml", "ta"]:
        asr_service_id = "ai4bharat/conformer-multilingual-dravidian-gpu--t4"
    else:
        asr_service_id = "bhashini/ai4bharat/conformer-multilingual-asr"  # fallback

    # Step 1: ASR with WAV format
    asr_payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {
                    "language": {"sourceLanguage": lang},
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

    try:
        asr_response = _pipeline_request(asr_payload)
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
            
        print(f"[DEBUG] Transcription: {transcription}")
        
    except Exception as e:
        print(f"[ASR ERROR] {type(e).__name__}: {e}")
        raise RuntimeError(f"ASR failed: {str(e)}")

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
            
        print(f"[DEBUG] Gemini reply: {reply}")
        
    except Exception as e:
        print(f"[GEMINI ERROR] {type(e).__name__}: {e}")
        raise RuntimeError(f"Gemini AI failed to generate response: {str(e)}")

    # Step 3: TTS returning WAV
    if lang in ["en", "hi", "bn"]:
        tts_service_id = "Bhashini/IITM/TTS"
    else:
        tts_service_id = "ai4bharat/indic-tts-coqui-indo_aryan-gpu--t4"  # fallback for other languages
    tts_payload = {
        "pipelineTasks": [
            {
                "taskType": "tts",
                "config": {
                    "language": {
                        "sourceLanguage": lang
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
        print(f"[TTS ERROR] {type(e).__name__}: {e}")
        raise RuntimeError(f"TTS failed: {str(e)}")