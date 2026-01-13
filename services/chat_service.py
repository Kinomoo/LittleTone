import os
import json
import re
import asyncio
from openai import AsyncOpenAI  
# 修正點 1：使用相對路徑引用 prompts
from .prompts import get_formatted_prompt 

class ChatService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = "gpt-4o"  # 支援視覺辨識

    async def get_response(self, user_input: str, history: list = None, rag_context: str = "", image_base64: str = None) -> dict:
        system_prompt = get_formatted_prompt(rag_context)
        messages = [{"role": "system", "content": system_prompt}]
        
        if history:
            messages.extend(history[-5:])
            
        user_content = []
        if user_input:
            user_content.append({"type": "text", "text": user_input})
        else:
            user_content.append({"type": "text", "text": "請幫我分析這張截圖的社交脈絡。"})

        if image_base64:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}",
                    "detail": "high"
                }
            })

        messages.append({"role": "user", "content": user_content})

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.7
            )
            return self._parse_json_content(response.choices[0].message.content)
        except Exception as e:
            print(f"ChatService Error: {e}")
            return self._get_error_response()

    def _parse_json_content(self, content: str) -> dict:
        try:
            clean_str = re.sub(r"```json\n?|\n?```", "", content).strip()
            return json.loads(clean_str)
        except:
            return self._get_error_response()

    def _get_error_response(self) -> dict:
        return {
            "reply": "不好意思，我剛剛稍微走神了...",
            "safety_alert": False,
            "options": [{"title": "系統提醒", "content": "連線稍微不穩，再試一次好嗎？"}],
            "key_change": "💡 核心洞察：連線暫時中斷。",
            "analysis": "Error",
            "tip": "再試一次看看。"
        }

# 修正點 2：新增這個函式，解決 ImportError
async def get_little_tone_final_response(user_input, image_b64=None, history=None, rag_context=""):
    """
    這是提供給 app.py 呼叫的快捷進入點
    """
    service = ChatService()
    return await service.get_response(
        user_input=user_input, 
        history=history, 
        rag_context=rag_context, 
        image_base64=image_b64
    )