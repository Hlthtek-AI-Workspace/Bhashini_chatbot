# test_api.py
import os
import base64
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def test_bhashini_connection():
    """Test basic connection to Bhashini API"""
    ULCA_USER_ID = os.getenv("ULCA_USER_ID")
    ULCA_API_KEY = os.getenv("ULCA_API_KEY")
    BHASHINI_AUTH_TOKEN = os.getenv("BHASHINI_AUTH_TOKEN")
    BHASHINI_PIPELINE_URL = os.getenv("BHASHINI_PIPELINE_URL")
    
    print("=== Environment Variables Check ===")
    print(f"ULCA_USER_ID: {'✓' if ULCA_USER_ID else '✗'}")
    print(f"ULCA_API_KEY: {'✓' if ULCA_API_KEY else '✗'}")
    print(f"BHASHINI_AUTH_TOKEN: {'✓' if BHASHINI_AUTH_TOKEN else '✗'}")
    print(f"BHASHINI_PIPELINE_URL: {'✓' if BHASHINI_PIPELINE_URL else '✗'}")
    
    if not all([ULCA_USER_ID, ULCA_API_KEY, BHASHINI_AUTH_TOKEN, BHASHINI_PIPELINE_URL]):
        print("❌ Missing environment variables!")
        return False
    
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "*/*",
        "user_id": ULCA_USER_ID,
        "api-key": ULCA_API_KEY,
        "Authorization": BHASHINI_AUTH_TOKEN,
    }
    
    print("\n=== Testing Bhashini API Connection ===")
    
    # Test with a simple payload
    test_payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {
                    "language": {"sourceLanguage": "en"},
                    "serviceId": "ai4bharat/indicwav2vec-hindi",
                    "audioFormat": "wav",
                    "samplingRate": 16000
                }
            }
        ],
        "inputData": {
            "audio": [{"audioContent": "dGVzdA=="}]  # base64 of "test"
        }
    }
    
    try:
        print(f"Making request to: {BHASHINI_PIPELINE_URL}")
        response = requests.post(BHASHINI_PIPELINE_URL, headers=HEADERS, json=test_payload, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("✅ Connection successful!")
            return True
        else:
            print(f"❌ Connection failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return False

def test_available_services():
    """Test what services are available"""
    print("\n=== Testing Available Services ===")
    
    url = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
    
    # Test ASR services
    asr_payload = {
        "pipelineTasks": [
            {
                "taskType": "asr",
                "config": {
                    "language": {"sourceLanguage": "en"}
                }
            }
        ]
    }
    
    try:
        response = requests.post(url, json=asr_payload, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            data = response.json()
            services = data.get("pipelineResponse", [])
            print(f"Available ASR services for English: {len(services)}")
            for service in services[:5]:  # Show first 5
                config = service.get("config", {})
                service_id = config.get("serviceId", "Unknown")
                print(f"  - {service_id}")
        else:
            print(f"Failed to get ASR services: {response.status_code}")
    except Exception as e:
        print(f"Error getting ASR services: {e}")

if __name__ == "__main__":
    test_bhashini_connection()
    test_available_services() 