# main.py

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from chatbot_utils import bhashini_asr_gemini_tts
import base64
import os
import tempfile
import subprocess

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

RESPONSE_WAV_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../frontend/public/response.wav")
)

def convert_webm_to_wav(webm_path, wav_path):
    command = [
        "ffmpeg", "-y", "-i", webm_path,
        "-ac", "1", "-ar", "16000", wav_path
    ]
    subprocess.run(command, check=True)

@app.post("/speech-to-speech")
async def speech_to_speech(
    audio: UploadFile = File(...),
    source_lang: str = Form(...),
    gender: str = Form(default="female")
):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_in:
            webm_path = temp_in.name
            temp_in.write(await audio.read())

        wav_path = webm_path.replace(".webm", ".wav")
        convert_webm_to_wav(webm_path, wav_path)

        with open(wav_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode("utf-8")

        result = bhashini_asr_gemini_tts(audio_b64, source_lang, gender)

        audio_bytes = base64.b64decode(result["audio_base64"])
        if len(audio_bytes) < 1000:
            raise RuntimeError("TTS audio too short or empty")

        with open(RESPONSE_WAV_PATH, "wb") as f:
            f.write(audio_bytes)

        os.remove(webm_path)
        os.remove(wav_path)

        return JSONResponse(status_code=200, content={"message": "Audio saved"})
    except Exception as e:
        print("[ERROR]", e)
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/response-audio")
async def get_response_audio():
    return FileResponse(RESPONSE_WAV_PATH, media_type="audio/wav")
