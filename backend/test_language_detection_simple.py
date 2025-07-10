#!/usr/bin/env python3
"""
Minimal test script for language detection service
"""

import os
import json
import requests
import base64

def test_language_detection():
    user_id = "3a99840cd7d0497aa4ff7eb17fe3206d"
    api_key = "108325a30b-40bc-4aa5-9f94-52313290eea9"
    auth_token = "ao3lhRJ7z-7raEyKIBw2-xo52aQgYxwR6L34MwlPaCh5niTdxhwWeKVuvyF7e8m7"
    url = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    audio_file_path = "test_audio.wav"
    if not os.path.exists(audio_file_path):
        print("❌ No test_audio.wav file found in backend directory.")
        return
    with open(audio_file_path, "rb") as f:
        audio_data = f.read()
        sample_audio_b64 = base64.b64encode(audio_data).decode("utf-8")

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
                "taskType": "audio-lang-detection",
                "config": {
                    "serviceId": "bhashini/iitmandi/audio-lang-detection/gpu"
                }
            }
        ],
        "inputData": {
            "audio": [
                {"audioContent": sample_audio_b64}
            ]
        }
    }

    # 1. Print cURL request for debugging/sharing
    print("\n=== cURL Request for Language Detection ===")
    print(f"curl -X POST '{url}' \\")
    for k, v in headers.items():
        print(f"  -H '{k}: {v}' \\")
    print(f"  -d '{json.dumps(payload)}'\n")

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        # 2. Print HTTP status code
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            response_json = response.json()
            pipeline_response = response_json.get("pipelineResponse", [])
            if pipeline_response:
                output_data = pipeline_response[0].get("output", [])
                if output_data:
                    lang_pred = output_data[0].get("langPrediction", [])
                    if lang_pred and isinstance(lang_pred, list):
                        lang_code = lang_pred[0].get("langCode")
                        # 3. Print detected language code
                        print(f"Detected Language Code: {lang_code}")
                    else:
                        # 4. Print clear message if nothing detected
                        print("No language prediction found in response.")
                else:
                    print("No output data found in response.")
            else:
                print("No pipeline response found.")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_language_detection() 