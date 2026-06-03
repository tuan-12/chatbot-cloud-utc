import os
import io
import struct
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 🔑 GIỮ NGUYÊN MÃ API KEY ĐẦU AQ... THẬT CỦA NHÓM VÀO ĐÂY NHA
GEMINI_API_KEY = "AQ.Ab8RN6JIFZQFmC6xpC3FrJWztzR0E3gD1LDOkFsxeTJdxGsPg"
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')
r = sr.Recognizer()

@app.get("/")
async def root():
    return {"status": "Ecosystem UTC AI hoạt động hoàn hảo!"}

@app.post("/api/iot/audio")
async def handle_audio_chat(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        print(f"[RENDER LOG]: Đã nhận file dung lượng: {len(audio_bytes)} bytes")
        
        if len(audio_bytes) < 1000:
            return StreamingResponse(io.BytesIO(b""), media_type="audio/mp3")

        # Khởi tạo tiêu đề WAV chuẩn 16000Hz từ dữ liệu mạch gửi lên
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

        # Tiến hành dịch giọng nói tiếng Việt
        try:
            with sr.AudioFile(wav_buf) as source:
                audio_data = r.record(source)
                cau_hoi_text = r.recognize_google(audio_data, language="vi-VN")
            print(f"[RENDER LOG]: Đã nghe được -> {cau_hoi_text}")
        except Exception as e:
            print("[RENDER LOG]: Không nhận dạng được từ ngữ, dùng câu dự phòng.")
            cau_hoi_text = "Xin chào" 

        # Hỏi não bộ Gemini
        response = model.generate_content(cau_hoi_text)
        reply_text = response.text
        print(f"[RENDER LOG]: Gemini phản hồi -> {reply_text}")
        
        # Chuyển chữ thành tiếng nói phát ra loa
        tts = gTTS(text=reply_text, lang='vi')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        return StreamingResponse(mp3_fp, media_type="audio/mp3")
        
    except Exception as general_err:
        print(f"[RENDER LOG] Lỗi hệ thống: {general_err}")
        return StreamingResponse(io.BytesIO(b""), media_type="audio/mp3")
