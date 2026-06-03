import os
import io
import struct
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
# Sử dụng pydub để chuyển đổi MP3 sang WAV thô chuẩn cho chip ESP32
from pydub import AudioSegment

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
    return {"status": "Ecosystem UTC AI sẵn sàng!"}

@app.post("/api/iot/audio")
async def handle_audio_chat(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        print(f"[RENDER LOG]: Nhan {len(audio_bytes)} bytes")
        
        if len(audio_bytes) < 1000:
            return StreamingResponse(io.BytesIO(b""), media_type="audio/wav")

        # Đóng gói dữ liệu đầu vào
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

        # Dịch giọng nói
        try:
            with sr.AudioFile(wav_buf) as source:
                audio_data = r.record(source)
                cau_hoi_text = r.recognize_google(audio_data, language="vi-VN")
            print(f"[RENDER LOG]: Đã nghe -> {cau_hoi_text}")
        except Exception as e:
            cau_hoi_text = "Xin chào" 

        # Gọi Gemini phản hồi câu ngắn gọn cho mạch xử lý nhanh
        response = model.generate_content(f"Trả lời ngắn gọn dưới 20 từ bằng tiếng Việt: {cau_hoi_text}")
        reply_text = response.text
        print(f"[RENDER LOG]: Gemini đáp -> {reply_text}")
        
        # Tạo âm thanh MP3 từ gTTS
        tts = gTTS(text=reply_text, lang='vi')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        # 🛠️ GIẢI PHÁP ĐỘC QUYỀN: Ép xung chuyển MP3 sang WAV thô tần số 16000Hz cứu loa hết rè
        sound = AudioSegment.from_file(mp3_fp, format="mp3")
        sound = sound.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        wav_output = io.BytesIO()
        sound.export(wav_output, format="wav")
        wav_output.seek(0)
        
        # Trích xuất dữ liệu thô (bỏ qua 44 byte tiêu đề wav để đưa luồng PCM nguyên bản)
        pcm_data = wav_output.read()[44:]
        
        # Gửi kèm đoạn chữ sếp nói vào tiêu đề Custom Header (X-User-Text) để mạch Arduino đọc được
        headers = {
            "X-User-Text": cau_hoi_text.encode('utf-8').decode('latin1'),
            "X-Bot-Text": reply_text.encode('utf-8').decode('latin1')
        }
        
        return StreamingResponse(io.BytesIO(pcm_data), media_type="audio/pcm", headers=headers)
        
    except Exception as general_err:
        print(f"[RENDER LOG] Lỗi: {general_err}")
        return StreamingResponse(io.BytesIO(b""), media_type="audio/pcm")
