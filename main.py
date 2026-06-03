import os
import io
import struct
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS

app = FastAPI()

# 🔑 DÁN CHÍNH XÁC MÃ API KEY BẮT ĐẦU BẰNG CHỮ AIza... VÀO ĐÂY NHA NHÓM
GEMINI_API_KEY = "AQ.Ab8RN6JIFZQFmC6xpcC3FrjWztzR0E3gD1LDOkFsxeTJdxGsPg"
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')
r = sr.Recognizer()

@app.get("/")
async def root():
    return {"status": "Ecosystem UTC AI vạn năng sẵn sàng!"}

@app.post("/api/iot/audio")
async def handle_audio_chat(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        print(f"Nhan duoc file am thanh: {len(audio_bytes)} bytes")
        
        if len(audio_bytes) < 1000:
            raise ValueError("File am thanh trong!")

        sample_rate = 16000
        bits_per_sample = 16
        channels = 1
        
        wav_buf = io.BytesIO()
        wav_buf.write(b'RIFF')
        wav_buf.write(struct.pack('<I', 36 + len(audio_bytes)))
        wav_buf.write(b'WAVEfmt ')
        wav_buf.write(struct.pack('<I', 16))
        wav_buf.write(struct.pack('<H', 1)) 
        wav_buf.write(struct.pack('<H', channels))
        wav_buf.write(struct.pack('<I', sample_rate))
        wav_buf.write(struct.pack('<I', sample_rate * channels * bits_per_sample // 8))
        wav_buf.write(struct.pack('<H', channels * bits_per_sample // 8))
        wav_buf.write(struct.pack('<H', bits_per_sample))
        wav_buf.write(b'data')
        wav_buf.write(struct.pack('<I', len(audio_bytes)))
        wav_buf.write(audio_bytes)
        wav_buf.seek(0)

        with sr.AudioFile(wav_buf) as source:
            audio_data = r.record(source)
            cau_hoi_text = r.recognize_google(audio_data, language="vi-VN")
        
        print(f"[UTC]: {cau_hoi_text}")
        
        response = model.generate_content(cau_hoi_text)
        reply_text = response.text
        print(f"[AI]: {reply_text}")
        
        tts = gTTS(text=reply_text, lang='vi')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        return StreamingResponse(mp3_fp, media_type="audio/mp3")
        
    except Exception as e:
        print(f"Loi: {e}")
        return StreamingResponse(io.BytesIO(b""), media_type="audio/mp3")
