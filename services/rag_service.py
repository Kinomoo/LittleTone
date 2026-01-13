import json
import os

# --- 1. 路徑設定 ---
# 取得專案根目錄 (D:\LittleTone)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ✨ 修正點：確保路徑指向根目錄下的 data 資料夾
# 這樣才能正確讀取 D:\LittleTone\data\emotion_scenarios.json
DICT_PATH = os.path.join(BASE_DIR, 'data', 'localization_dictionary.json')
SCENARIO_PATH = os.path.join(BASE_DIR, 'data', 'emotion_scenarios.json')

def load_json_data(file_path):
    """通用的 JSON 載入工具，含編碼處理"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print(f"[RAG Service] 找不到檔案: {file_path}")
    except Exception as e:
        print(f"[RAG Service] 讀取 {file_path} 失敗: {e}")
    return []

def retrieve_social_knowledge(user_query):
    """
    核心檢索邏輯：同時搜尋在地詞彙與情緒場景。
    """
    # ✨ 新增防呆：如果是系統自動生成的指令 (如：轉化語氣要求)，則跳過檢索以節省效能
    if not user_query or "(指令：" in user_query:
        return ""

    # 載入資料
    dict_data = load_json_data(DICT_PATH)
    scenario_data = load_json_data(SCENARIO_PATH)
    
    knowledge_pieces = []

    # --- 第一部分：在地詞彙比對 ---
    for item in dict_data:
        term = item.get("term", "")
        if term and term in user_query:
            advice = item.get('tone_advice', '無')
            # 取得建議用法
            suggestion = item.get('suggestions', [item.get('local_context', '無')])[0]
            knowledge_pieces.append(
                f"【台灣在地術語：{term}】\n"
                f"- 定義：{item.get('definition')}\n"
                f"- 語氣建議：{advice}\n"
                f"- 推薦用法：{suggestion}"
            )

    # --- 第二部分：情緒場景比對 (對應你的 JSON 格式) ---
    for scene in scenario_data:
        context = scene.get("contextual_analysis", {})
        keywords = context.get("keywords", [])
        
        # 只要使用者輸入中命中關鍵字 (如：11 點、老地方、為了你好)
        if any(kw in user_query for kw in keywords):
            # 依照你提供的 JSON 結構精準抓取欄位
            category = scene.get('category', '未分類')
            clue = context.get('cultural_clue', '無')
            emotion = context.get('correct_emotion', '待判讀')
            risk = context.get('risk_level', '未知')
            action = scene.get('ai_action_guideline', '依一般程序處理')
            note = scene.get('localization_note', '無')

            knowledge_pieces.append(
                f"【情緒場景分析：{category}】\n"
                f"- 文化脈絡：{clue}\n"
                f"- 真實情緒判讀：{emotion} (社交風險：{risk})\n"
                f"- AI 應對方針：{action}\n"
                f"- 台灣文化備註：{note}"
            )

    # 2. 彙整結果
    if not knowledge_pieces:
        return ""

    # 使用清晰的分隔線，幫助 GPT 區分不同的知識點
    return "\n\n---\n\n".join(knowledge_pieces)

# 測試區塊
if __name__ == "__main__":
    print("=== LittleTone RAG 檢索測試 ===")
    # 測試命中你提供的 scenario_240
    test_input = "我們 11 點老地方見。"
    result = retrieve_social_knowledge(test_input)
    if result:
        print(result)
    else:
        print("未檢索到相關知識。")