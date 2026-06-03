import os
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS
import io

app = FastAPI()

# 🔑 Cấu hình API Key Gemini của nhóm UTC
GEMINI_API_KEY = "DÁN_MÃ_API_KEY_GEMINI_CỦA_NHÓM_VÀO_ĐÂY"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

r = sr.Recognizer()

@app.post("/api/iot/audio")
async def handle_audio_chat(file: UploadFile = File(...)):
    try:
        # 1. Đọc file âm thanh RAW từ ESP32-S3 gửi lên qua Internet
        audio_bytes = await file.read()
        
        # Tạo file tạm Wav để đưa vào bộ nhận diện
        audio_stream = io.BytesIO(audio_bytes)
        with sr.AudioFile(audio_stream) as source:
            audio_data = r.record(source)
            # 🎙️ Dịch giọng nói bất kỳ của nhóm thành Chữ (Hỗ trợ tiếng Việt)
            cau_hoi_text = r.recognize_google(audio_data, language="vi-VN")
        
        print(f"Sếp UTC hỏi: {cau_hoi_text}")
        
        # 2. Hỏi Gemini AI vạn năng (Trả lời bất kỳ câu hỏi nào)
        response = model.generate_content(cau_hoi_text)
        reply_text = response.text
        
        # 3. Chuyển chữ của Gemini thành file âm thanh Tiếng Việt công nghệ TTS
        tts = gTTS(text=reply_text, lang='vi')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        # 🚀 Phóng file âm thanh ngược từ đám mây Singapore về tận cái loa trên bàn của nhóm
        return StreamingResponse(mp3_fp, media_type="audio/mp3")
        
    except Exception as e:
        # Nếu không nghe rõ, trả về một file âm thanh thông báo mặc định
        print(f"Lỗi: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
