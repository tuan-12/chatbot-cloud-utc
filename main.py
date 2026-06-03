import os
import io
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS

app = FastAPI()

# 🔑 DÁN MÃ API KEY GEMINI THẬT CỦA NHÓM VÀO ĐÂY
GEMINI_API_KEY = "AQ.Ab8RN6IM2ruaUoozboSbIG-vHBQgl_UOr5y6e6O-S1n2uSJgWg"
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-2.5-flash')
r = sr.Recognizer()

@app.get("/")
async def root():
    return {"status": "Ecosystem UTC AI vạn năng sẵn sàng!"}

@app.post("/api/iot/audio")
async def handle_audio_chat(file: UploadFile = File(...)):
    try:
        # Đọc dữ liệu âm thanh thô từ mạch gửi lên
        audio_bytes = await file.read()
        print(f"Nhận được file âm thanh dung lượng: {len(audio_bytes)} bytes")
        
        if len(audio_bytes) < 1000:
            raise ValueError("File âm thanh quá nhỏ hoặc trống rỗng!")

        # Tự động tạo tiêu đề WAV chuẩn (Header) cho dữ liệu thô từ ESP32
        sample_rate = 16000
        bits_per_sample = 16
        channels = 1
        
        wav_buf = io.BytesIO()
        # Ghi Header cho file WAV để SpeechRecognition đọc được
        import struct
        wav_buf.write(b'RIFF')
        wav_buf.write(struct.pack('<I', 36 + len(audio_bytes)))
        wav_buf.write(b'WAVEfmt ')
        wav_buf.write(struct.pack('<I', 16))
        wav_buf.write(struct.pack('<H', 1)) # PCM
        wav_buf.write(struct.pack('<H', channels))
        wav_buf.write(struct.pack('<I', sample_rate))
        wav_buf.write(struct.pack('<I', sample_rate * channels * bits_per_sample // 8))
        wav_buf.write(struct.pack('<H', channels * bits_per_sample // 8))
        wav_buf.write(struct.pack('<H', bits_per_sample))
        wav_buf.write(b'data')
        wav_buf.write(struct.pack('<I', len(audio_bytes)))
        wav_buf.write(audio_bytes)
        wav_buf.seek(0)

        # Tiến hành nhận diện giọng nói tiếng Việt
        with sr.AudioFile(wav_buf) as source:
            audio_data = r.record(source)
            cau_hoi_text = r.recognize_google(audio_data, language="vi-VN")
        
        print(f"[UTC CHATBOT]: Đã nghe được -> {cau_hoi_text}")
        
        # Hỏi não bộ Gemini vạn năng
        response = model.generate_content(cau_hoi_text)
        reply_text = response.text
        print(f"[AI PHẢN HỒI]: {reply_text}")
        
        # Chuyển chữ thành tiếng nói phát ra loa
        tts = gTTS(text=reply_text, lang='vi')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        return StreamingResponse(mp3_fp, media_type="audio/mp3")
        
    except sr.UnknownValueError:
        print("Lỗi: Google không nhận diện được từ ngữ.")
        return StreamingResponse(io.BytesIO(b""), media_type="audio/mp3")
    except Exception as e:
        print(f"Lỗi hệ thống: {e}")
        return StreamingResponse(io.BytesIO(b""), media_type="audio/mp3")
