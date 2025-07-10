import os
import json
import requests
import base64
import time

def test_asr_english():
    user_id = "3a99840cd7d0497aa4ff7eb17fe3206d"
    api_key = "108325a30b-40bc-4aa5-9f94-52313290eea9"
    auth_token = "ao3lhRJ7z-7raEyKIBw2-xo52aQgYxwR6L34MwlPaCh5niTdxhwWeKVuvyF7e8m7"
    url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
    audio_file_path = "test_audio_en.wav"

    if not os.path.exists(audio_file_path):
        print("❌ No test_audio_en.wav file found in backend directory.")
        return
    with open(audio_file_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "user_id": user_id,
        "api-key": api_key,
        "Authorization": auth_token,
    }
    payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {
                    "language": {"sourceLanguage": "en"},
                    "serviceId": "ai4bharat/whisper-medium-en--gpu--t4",
                    "audioFormat": "wav",
                    "samplingRate": 16000
                }
            }
        ],
        "inputData": {
            "audio": [{"audioContent": audio_b64}]
        }
    }
    start = time.time()
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    elapsed = int((time.time() - start) * 1000)
    print(f"ASR English: Status {response.status_code}, Time {elapsed}ms")
    if response.status_code == 200:
        try:
            out = response.json()
            pipeline = out.get("pipelineResponse", [])
            if pipeline and "output" in pipeline[0]:
                outputs = pipeline[0]["output"]
                if outputs and "source" in outputs[0]:
                    print("  Transcription:", outputs[0]["source"])
        except Exception:
            pass

def test_asr_multilingual():
    user_id = "3a99840cd7d0497aa4ff7eb17fe3206d"
    api_key = "108325a30b-40bc-4aa5-9f94-52313290eea9"
    auth_token = "ao3lhRJ7z-7raEyKIBw2-xo52aQgYxwR6L34MwlPaCh5niTdxhwWeKVuvyF7e8m7"
    url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
    audio_file_path = "test_audio_hi.wav"

    if not os.path.exists(audio_file_path):
        print("❌ No test_audio_hi.wav file found in backend directory.")
        return
    with open(audio_file_path, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "user_id": user_id,
        "api-key": api_key,
        "Authorization": auth_token,
    }
    payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {
                    "language": {"sourceLanguage": "hi"},
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
    start = time.time()
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    elapsed = int((time.time() - start) * 1000)
    print(f"ASR Multilingual: Status {response.status_code}, Time {elapsed}ms")
    if response.status_code == 200:
        try:
            out = response.json()
            pipeline = out.get("pipelineResponse", [])
            if pipeline and "output" in pipeline[0]:
                outputs = pipeline[0]["output"]
                if outputs and "source" in outputs[0]:
                    print("  Transcription:", outputs[0]["source"])
        except Exception:
            pass

def test_tts():
    user_id = "3a99840cd7d0497aa4ff7eb17fe3206d"
    api_key = "108325a30b-40bc-4aa5-9f94-52313290eea9"
    auth_token = "ao3lhRJ7z-7raEyKIBw2-xo52aQgYxwR6L34MwlPaCh5niTdxhwWeKVuvyF7e8m7"
    url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"
    text = "नमस्ते, आप कैसे हैं?"

    headers = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "user_id": user_id,
        "api-key": api_key,
        "Authorization": auth_token,
    }
    payload = {
        "pipelineTasks": [
            {
                "taskType": "tts",
                "config": {
                    "language": {"sourceLanguage": "hi"},
                    "serviceId": "Bhashini/IITM/TTS",
                    "gender": "female",
                    "samplingRate": 16000
                }
            }
        ],
        "inputData": {
            "input": [{"source": text}]
        }
    }
    start = time.time()
    response = requests.post(url, headers=headers, json=payload, timeout=60)
    elapsed = int((time.time() - start) * 1000)
    print(f"TTS: Status {response.status_code}, Time {elapsed}ms")
    if response.status_code == 200:
        try:
            out = response.json()
            pipeline = out.get("pipelineResponse", [])
            if pipeline and "audio" in pipeline[0]:
                audio = pipeline[0]["audio"]
                if audio and "audioContent" in audio[0]:
                    print("  Audio length (base64):", len(audio[0]["audioContent"]))
        except Exception:
            pass

if __name__ == "__main__":
    print("\n--- ASR English Test ---")
    test_asr_english()
    print("\n--- ASR Multilingual Test ---")
    test_asr_multilingual()
    print("\n--- TTS Test ---")
    test_tts()