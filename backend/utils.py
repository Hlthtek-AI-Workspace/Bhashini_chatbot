# utils.py
import io
import base64
import sounddevice as sd
import soundfile as sf
from pydub import AudioSegment
import speech_recognition as sr

def play_audio_from_base64(audio_b64: str) -> None:
    """Play base64 MP3 or WAV through speakers."""
    if not audio_b64:
        print("No audio content to play.")
        return

    try:
        audio_bytes = base64.b64decode(audio_b64)

        if audio_bytes[:3] == b"ID3" or audio_bytes[0] & 0xFF == 0xFF:
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        else:
            audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="wav")

        raw_data = io.BytesIO(audio.raw_data)
        with sf.SoundFile(raw_data) as f:
            data = f.read(dtype="float32")
            sd.play(data, f.samplerate)
            sd.wait()

    except Exception as e:
        print(f"Error playing audio: {e}")

def recognize_speech_and_encode(language='en', duration=5):
    recognizer = sr.Recognizer()
    try:
        with sr.Microphone(sample_rate=16000) as source:
            recognizer.adjust_for_ambient_noise(source)
            print(f"Speak now for {duration} seconds...")
            audio = recognizer.listen(source, timeout=duration, phrase_time_limit=duration)
            wav_data = io.BytesIO(audio.get_wav_data(convert_rate=16000, convert_width=2))
            return base64.b64encode(wav_data.getvalue()).decode('utf-8')
    except sr.WaitTimeoutError:
        print("No speech detected.")
        return None
    except Exception as e:
        print(f"Error capturing speech: {e}")
        return None
