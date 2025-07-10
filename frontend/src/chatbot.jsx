import React, { useState, useRef } from "react";
import "./index.css";

export default function Chatbot() {
  const [open, setOpen] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isResponding, setIsResponding] = useState(false);
  const [detectedLanguage, setDetectedLanguage] = useState(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const toggleChat = () => setOpen(!open);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => chunksRef.current.push(e.data);
      mediaRecorder.onstop = async () => {
        setIsRecording(false);
        setIsResponding(true);

        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        const formData = new FormData();
        formData.append("audio", blob, "input.webm");
        formData.append("gender", "female");

        try {
          const response = await fetch("http://localhost:8000/speech-to-speech", {
            method: "POST",
            body: formData,
          });

          if (!response.ok) throw new Error("Failed to get response");
          
          const responseData = await response.json();
          setDetectedLanguage(responseData.detected_language);
          
          // Now fetch the actual WAV audio
          const audioResp = await fetch("http://localhost:8000/response-audio");
          if (!audioResp.ok) throw new Error("Failed to fetch audio");
          const audioBlob = await audioResp.blob();
          const audioUrl = URL.createObjectURL(audioBlob);
          const audio = new Audio(audioUrl);
          audio.onended = () => setIsResponding(false);
          audio.play();
        } catch (err) {
          console.error("Backend error:", err);
          alert("Backend error: " + err.message);
          setIsResponding(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setTimeout(() => mediaRecorder.stop(), 5000);
    } catch (err) {
      console.error("Microphone error:", err);
      alert("Microphone access error. Please check your permissions.");
    }
  };

  return (
    <>
      <div className="chat-icon" onClick={toggleChat}>
        <img src="/robot.gif" alt="Chatbot" className="robot" />
      </div>

      {open && (
        <div className="chat-container">
          <h2>Voice Chatbot</h2>
          <p className="chat-description">
            Speak in any language and I'll respond automatically!
          </p>
          
          {detectedLanguage && (
            <div className="detected-language">
              Detected Language: <strong>{detectedLanguage.toUpperCase()}</strong>
            </div>
          )}

          <button
            className={`record-btn ${isRecording ? "recording" : ""}`}
            onClick={startRecording}
            disabled={isRecording || isResponding}
          >
            {isRecording ? "🎤 Recording..." : "🎤 Speak Now"}
          </button>
          
          {isResponding && <div className="bot-response">🤖 Processing...</div>}
        </div>
      )}
    </>
  );
}
