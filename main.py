import os
import io
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
import google.generativeai as genai
import speech_recognition as sr
from gtts import gTTS

app = FastAPI()

# 🔑 DÁN MÃ API KEY GEMINI CỦA NHÓM UTC VÀO ĐÂY
GEMINI_API_KEY = "DÁN_MÃ_API_KEY_GEMINI_CỦA_NHÓM_VÀO_ĐÂY"
genai.configure(api_key=GEMINI_API_KEY)

# Sử dụng mô hình vạn năng để trả lời chính xác mọi câu hỏi
model = genai.GenerativeModel('gemini-2.5-flash')
r = sr.Recognizer()

@app.get("/")
async def root():
    return {"status": "Ecosystem UTC AI is Live and Ready!"}

@app.post("/api/iot/audio")
async def handle_audio_chat(file: UploadFile = File(...)):
    try:
        # 1. Đọc file âm thanh từ mạch ESP32 gửi lên
        audio_bytes = await file.read()
        audio_stream = io.BytesIO(audio_bytes)
        
        # 2. Dịch từ giọng nói sang văn bản dạng chữ
        with sr.AudioFile(audio_stream) as source:
            audio_data = r.record(source)
            cau_hoi_text = r.recognize_google(audio_data, language="vi-VN")
        
        print(f"[UTC]: {cau_hoi_text}")
        
        # 3. Gửi câu hỏi vào bộ não AI Gemini để xử lý (Hỏi bất kỳ điều gì)
        response = model.generate_content(cau_hoi_text)
        reply_text = response.text
        print(f"[AI]: {reply_text}")
        
        # 4. Chuyển đổi văn bản câu trả lời của Gemini thành giọng nói Tiếng Việt
        tts = gTTS(text=reply_text, lang='vi')
        mp3_fp = io.BytesIO()
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        
        # 5. Trả file âm thanh về cho mạch phát ra Loa
        return StreamingResponse(mp3_fp, media_type="audio/mp3")
        
    except Exception as e:
        print(f"Lỗi hệ thống: {e}")
        # Nếu có lỗi (Ví dụ không nghe rõ), AI vẫn phản hồi bằng tiếng để loa phát ra thông báo lỗi
        try:
            error_tts = gTTS(text="Hệ thống chưa nghe rõ, nhóm xin mời nói lại ạ!", lang='vi')
            err_fp = io.BytesIO()
            error_tts.write_to_fp(err_fp)
            err_fp.seek(0)
            return StreamingResponse(err_fp, media_type="audio/mp3")
        except:
            return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
