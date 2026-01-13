import json
import os

# 設定檔案路徑
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DICT_PATH = os.path.join(BASE_DIR, 'localization_dictionary.json')
SCENARIO_PATH = os.path.join(BASE_DIR, 'emotion_scenarios.json')

def load_json_data(file_path):
    """通用的 JSON 載入工具"""
    try:
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"[RAG Service] 讀取 {file_path} 失敗: {e}")
    return []

def retrieve_social_knowledge(user_query):
    """
    核心檢索邏輯：同時搜尋「在地詞彙」與「情緒場景」。
    """
    # 1. 載入資料
    dict_data = load_json_data(DICT_PATH)
    scenario_data = load_json_data(SCENARIO_PATH)
    
    knowledge_pieces = []

    # --- 第一部分：在地詞彙比對 (奧步、神隱、放生...) ---
    for item in dict_data:
        term = item.get("term", "")
        if term and term in user_query:
            knowledge_pieces.append(
                f"【在地術語：{term}】\n"
                f"定義：{item.get('definition')}\n"
                f"建議語氣：{item.get('tone_advice')}\n"
                f"建議用法：{item.get('suggestions', [item.get('local_context')])[0]}"
            )

    # --- 第二部分：情緒場景與「反話」偵測 (情勒、情緒觀察...) ---
    for scene in scenario_data:
        context = scene.get("contextual_analysis", {})
        keywords = context.get("keywords", [])
        
        # 只要使用者輸入中命中場景中的關鍵字 (如：為了你好、習慣了)
        if any(kw in user_query for kw in keywords):
            knowledge_pieces.append(
                f"【情緒場景分析：{scene.get('category')}】\n"
                f"文化脈絡：{context.get('cultural_clue')}\n"
                f"真實情緒：{context.get('correct_emotion')} (風險等級：{context.get('risk_level')})\n"
                f"AI 應對方針：{scene.get('ai_action_guideline')}\n"
                f"台灣在地備註：{scene.get('localization_note')}"
            )

    # 2. 彙整結果
    if not knowledge_pieces:
        return ""

    # 用分隔線把多個知識點隔開，方便 AI 閱讀
    return "\n---\n".join(knowledge_pieces)

# 測試用邏輯
if __name__ == "__main__":
    # 測試情勒場景
    test_input = "我媽一直說她這樣是為了我好，但我壓力好大。"
    print("--- 檢索測試 ---")
    print(retrieve_social_knowledge(test_input))