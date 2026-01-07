# ai_service.py
# 這裡負責跟 OpenAI 連線

from openai import OpenAI
import os
import json
from dotenv import load_dotenv
import prompts # 匯入 prompts.py

# 初始化
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_emotion_response(messages_history):
    """
    處理 LittleTone 的核心邏輯：
    接收包含對話歷史的列表，回傳包含 reply, options, key_change, analysis, tip 的 JSON 字典。
    """
    try:
        # 組合系統指令（名稱已統一為 EMOTION_SYSTEM_PROMPT）與對話歷史
        full_messages = [
            {"role": "system", "content": prompts.EMOTION_SYSTEM_PROMPT}
        ] + messages_history

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=full_messages,
            # 調整 temperature 至 0.75，讓回覆更口語且具備「靈魂」
            temperature=0.75, 
            presence_penalty=0.6, # 稍微增加懲罰，避免重複生硬的詞彙
            max_tokens=800
        )
        
        # 解析 AI 回傳的 JSON 字串
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"Error in ai_service: {e}")
        # 保底回傳，避免前端因為欄位缺失而崩潰
        return {
            "reply": "不好意思，我剛才稍微分神了，能請您再說一次剛才發生的狀況嗎？🌱", 
            "options": [
                {"title": "重新描述", "content": "（請重新輸入您想處理的訊息）"}
            ], 
            "key_change": "💡 核心洞察：目前連線稍微有點不穩定", 
            "analysis": "系統暫時無法處理您的訊息。", 
            "tip": "再麻煩您重新發送一次試試看！"
        }