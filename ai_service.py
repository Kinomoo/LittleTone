# ai_service.py
# 這裡負責跟 OpenAI 連線，並處理在地化知識庫的檢索

from openai import OpenAI
import os
import json
from dotenv import load_dotenv
import prompts # 匯入 prompts.py

# 初始化
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- 新增：在地化字典處理邏輯 ---

def load_localization_data():
    """從 data 資料夾載入在地化術語 JSON"""
    try:
        # 使用相對路徑確保在不同環境下都能讀到
        json_path = os.path.join(os.path.dirname(__file__), 'data', 'localization_dictionary.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"無法載入字典: {e}")
        return []

def get_relevant_context(user_text):
    """
    比對使用者輸入的文字，找出 JSON 中對應的術語資訊。
    這是一個簡單的 RAG 檢索邏輯（Keyword-based Retrieval）。
    """
    dictionary = load_localization_data()
    relevant_context = ""
    
    for item in dictionary:
        # 如果使用者訊息包含術語 (例如：穩聊、很解)
        if item['term'] in user_text:
            relevant_context += (
                f"\n[偵測到在地化術語：{item['term']}]\n"
                f"正確定義：{item['definition']}\n"
                f"語氣建議：{item['tone_advice']}\n"
                f"推薦回覆示範：{item['suggestions'][0]}\n"
            )
    
    return relevant_context

# --- 核心邏輯修改 ---

def get_emotion_response(messages_history):
    """
    處理 LittleTone 的核心邏輯：
    接收包含對話歷史的列表，回傳包含 reply, options, key_change, analysis, tip 的 JSON 字典。
    """
    try:
        # 1. 取得使用者最後一句話，用來檢索知識庫
        last_user_message = ""
        for msg in reversed(messages_history):
            if msg["role"] == "user":
                last_user_message = msg["content"]
                break
        
        # 2. 獲取相關背景知識
        context = get_relevant_context(last_user_message)
        
        # 3. 組合系統指令
        # 我們將 context 傳遞給 prompts 模組（下一段我們會去修改 prompts.py 來接收這個變數）
        system_content = prompts.get_formatted_prompt(context)

        full_messages = [
            {"role": "system", "content": system_content}
        ] + messages_history

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=full_messages,
            temperature=0.75, 
            presence_penalty=0.6,
            max_tokens=800
        )
        
        return json.loads(response.choices[0].message.content)
        
    except Exception as e:
        print(f"Error in ai_service: {e}")
        return {
            "reply": "不好意思，我剛才稍微分神了，能請您再說一次剛才發生的狀況嗎？🌱", 
            "options": [
                {"title": "重新描述", "content": "（請重新輸入您想處理的訊息）"}
            ], 
            "key_change": "💡 核心洞察：目前連線稍微有點不穩定", 
            "analysis": "系統暫時無法處理您的訊息。", 
            "tip": "再麻煩您重新發送一次試試看！"
        }