import os
import uuid
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI(title="Hệ sinh thái Chatbot IoT Độc Lập - UTC")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cấu hình API Key cố định trực tiếp để chạy trên đám mây
GEMINI_API_KEY = "AIzaSyD3eNNWGPuKhwYgfs9c7VW7vCtUKuP4SEU"
genai.configure(api_key=GEMINI_API_KEY)

class IoTChatRequest(BaseModel):
    message: str
    session_id: str = "default_iot_session"

last_gemini_reply = "Chao sep, he sinh thai doc lap da kich hoat. Toi san sang giup gi cho sep!"

@app.post("/api/iot/chat")
def iot_chat_endpoint(payload: IoTChatRequest):
    global last_gemini_reply
    try:
        # Lệnh chào mừng khi vừa cắm nguồn ngoài
        if payload.message == "boot_welcome":
            last_gemini_reply = "Chao sep, toi co the giup gi cho sep!"
            return {"status": "success", "reply": last_gemini_reply}

        if payload.message == "get_last":
            return {"status": "success", "reply": last_gemini_reply}

        # Truy vấn trực tiếp kho tri thức khổng lồ của Google qua Gemini 2.5 Flash
        system_instruction = (
            "Bạn là trợ lý AI thông minh toàn năng, kết nối không gian mạng toàn cầu. "
            "Hãy đóng vai là trợ lý thân thiết của sếp. Trả lời bằng tiếng Việt cực kỳ ngắn gọn, "
            "không quá 2 câu, đi thẳng vào bản chất vấn đề, không dùng ký tự markdown."
        )
        
        model = genai.GenerativeModel(model_name='gemini-2.5-flash', system_instruction=system_instruction)
        response = model.generate_content(contents=payload.message)
        
        # Làm sạch văn bản để vi điều khiển không bị lỗi hiển thị
        clean_text = response.text.replace("**", "").replace("*", "").replace("`", "").strip()
        last_gemini_reply = clean_text
        
        return {"status": "success", "reply": clean_text}

    except Exception as e:
        return {"status": "error", "reply": f"Loi ket noi Cloud: {str(e)}"}