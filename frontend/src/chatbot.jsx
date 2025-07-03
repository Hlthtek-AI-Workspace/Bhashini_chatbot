import React, { useState, useRef } from "react";
import "./index.css";

export default function Chatbot() {
  const [open, setOpen] = useState(false);
  const [selectedLang, setSelectedLang] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isResponding, setIsResponding] = useState(false);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const LANGUAGES = [
    { code: "hi", label: "ए" },
    { code: "bn", label: "ক" },
    { code: "en", label: "A" },
  ];

  const toggleChat = () => setOpen(!open);
  const handleLanguageSelect = (code) => setSelectedLang(code);

  const startRecording = async () => {
    if (!selectedLang) {
      alert("Please select a language first.");
      return;
    }

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
        formData.append("source_lang", selectedLang);
        formData.append("gender", "female");

        try {
          const response = await fetch("http://localhost:8000/speech-to-speech", {
            method: "POST",
            body: formData,
          });

          if (!response.ok) throw new Error("Failed to get response");
          
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
          <h2>Select Language</h2>
          <div className="lang-buttons">
            {LANGUAGES.map((lang) => (
              <button
                key={lang.code}
                className={`lang-btn ${selectedLang === lang.code ? "selected" : ""}`}
                onClick={() => handleLanguageSelect(lang.code)}
              >
                {lang.label}
              </button>
            ))}
          </div>

          {selectedLang && (
            <>
              <button
                className={`record-btn ${isRecording ? "recording" : ""}`}
                onClick={startRecording}
                disabled={isRecording || isResponding}
              >
                {isRecording ? "🎤 Recording..." : "🎤 Speak"}
              </button>
              {isResponding && <div className="bot-response">🤖 Responding...</div>}
            </>
          )}
        </div>
      )}
    </>
  );
}
