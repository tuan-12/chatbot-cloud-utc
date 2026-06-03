import os
import io
import struct
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS

app = FastAPI()

# 🔑 GIỮ NGUYÊN MÃ API KEY ĐẦU AQ... THẬT CỦA NHÓM VÀO ĐÂY NHA
GEMINI_API_KEY = "AQ.Ab8RN6JIFZQFmC6xpcC3FrjWztzR0E3gD1LDOkFsxeTJdxGsPg"
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')
r = sr.Recognizer()

@app.get("/")
async def root():
    return {"status": "Ecosystem UTC AI van nang san sang!"}

@app.post("/api/iot/audio")
async def handle_audio_chat(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        print(f"[RENDER LOG]: Nhan duoc dung luong am thanh: {len(audio_bytes)} bytes")
        
        if len(audio_bytes) < 1000:
            print("[RENDER LOG]: File qua nho, bo qua.")
            return StreamingResponse(io.BytesIO(b""), media_type="audio/mp3")

        # Khởi tạo Header chuẩn hóa file WAV 16000Hz, Mono, 16bit chống sập ngầm
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

        # Nhận diện tiếng Việt dõng dạc
        try:
            with sr.AudioFile(wav_buf) as source:
                audio_data = r.record(source)
                cau_hoi_text = r.recognize_google(audio_data, language="vi-VN")
            print(f"[RENDER LOG]: Da nghe duoc text -> {cau_hoi_text}")
        except Exception as speech_err:
            print(f"[RENDER LOG]: Khong nghe ro từ ngu hoac tieng on: {speech_err}")
            cau_hoi_text = "Xin chào" # Dự phòng câu mặc định nếu môi trường quá ồn để tránh sập mạch

        # Gọi bộ não Gemini vạn năng phản hồi
        response = model.generate_content(cau_hoi_text)
        reply_text = response.text
        print(f"[RENDER LOG]: Gemini phan hoi -> {reply_text}")
        
        # Chuyển đổi văn bản thành giọng nói gTTS Tiếng Việt mượt mà
        tts = gTTS(text=reply_text, lang='vi')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        return StreamingResponse(mp3_fp, media_type="audio/mp3")
        
    except Exception as e:
        print(f"[RENDER LOG] Loi he thong tong the: {e}")
        # Tra ve file trong chu khong cho phep sap mang 500
        return StreamingResponse(io.BytesIO(b""), media_type="audio/mp3")
