import os
import io
import struct
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
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
    return {"status": "Xiaomi AI Open-Source Backend Online!"}

@app.post("/api/iot/audio")
async def handle_audio_chat(file: UploadFile = File(...)):
    try:
        audio_bytes = await file.read()
        if len(audio_bytes) < 1000:
            return StreamingResponse(io.BytesIO(b""), media_type="audio/pcm")

        # Đóng gói dữ liệu đầu vào chuẩn hóa
        wav_buf = io.BytesIO()
        wav_buf.write(b'RIFF')
        wav_buf.write(struct.pack('<I', 36 + len(audio_bytes)))
        wav_buf.write(b'WAVEfmt ')
        wav_buf.write(struct.pack('<I', 16))
        wav_buf.write(struct.pack('<H', 1)) 
        wav_buf.write(struct.pack('<H', 1))
        wav_buf.write(struct.pack('<I', 16000))
        wav_buf.write(struct.pack('<I', 16000 * 2))
        wav_buf.write(struct.pack('<H', 2))
        wav_buf.write(struct.pack('<H', 16))
        wav_buf.write(b'data')
        wav_buf.write(struct.pack('<I', len(audio_bytes)))
        wav_buf.write(audio_bytes)
        wav_buf.seek(0)

        try:
            with sr.AudioFile(wav_buf) as source:
                audio_data = r.record(source)
                cau_hoi_text = r.recognize_google(audio_data, language="vi-VN")
        except Exception:
            cau_hoi_text = "Xin chào" 

        # Trả lời siêu ngắn gọn để mạch ESP32 xử lý luồng âm thanh không bị giật lag
        response = model.generate_content(f"Trả lời cực kỳ ngắn gọn dưới 12 từ bằng tiếng Việt: {cau_hoi_text}")
        reply_text = response.text
        
        tts = gTTS(text=reply_text, lang='vi')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        # CHUẨN HÓA XIAOMI FUSION: Chuyển đổi tần số âm thanh về mức 22050Hz ổn định nhất cho I2S
        sound = AudioSegment.from_file(mp3_fp, format="mp3")
        sound = sound.set_frame_rate(22050).set_channels(1).set_sample_width(2)
        
        wav_output = io.BytesIO()
        sound.export(wav_output, format="wav")
        wav_output.seek(0)
        
        pcm_data = wav_output.read()[44:] # Cắt bỏ 44 byte tiêu đề wav để lấy ruột âm thanh thô
        
        headers = {
            "X-User-Text": cau_hoi_text.encode('utf-8').decode('latin1'),
            "X-Bot-Text": reply_text.encode('utf-8').decode('latin1')
        }
        return StreamingResponse(io.BytesIO(pcm_data), media_type="audio/pcm", headers=headers)
        
    except Exception as e:
        return StreamingResponse(io.BytesIO(b""), media_type="audio/pcm")
