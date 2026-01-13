import os
import json
from openai import AsyncOpenAI
from .prompts import get_formatted_prompt
from .rag_service import retrieve_social_knowledge
from .image_service import ImageService

# 初始化 OpenAI 客戶端
client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ✨ 新增 ChatService 類別，解決 ImportError
class ChatService:
    @staticmethod
    async def get_little_tone_final_response(user_text, image_base64=None):
        """
        核心邏輯：結合 RAG 檢索、圖片判讀與 OpenAI 生成。
        """
        try:
            # 執行 RAG 檢索
            context_info = retrieve_social_knowledge(user_text)
            
            # 產生 System Prompt
            system_prompt = get_formatted_prompt(context_info)
            
            # 準備訊息內容
            user_content = []
            if user_text:
                user_content.append({"type": "text", "text": user_text})
                
            if image_base64:
                compressed_image = ImageService.process_and_compress_base64(image_base64)
                user_content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{compressed_image}"}
                })

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]

            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.3
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"[ChatService] 錯誤: {e}")
            return {"reply": "伺服器忙碌中...", "suggested_scenarios": []}

# ✨ 為了讓 app.py 的 from services import get_little_tone_final_response 能運作
# 我們將類別內的方法指派給一個同名變數
get_little_tone_final_response = ChatService.get_little_tone_final_response