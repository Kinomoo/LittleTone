from flask import Flask, render_template, request, jsonify, session
import ai_service # 匯入我們的大腦檔案
import os

app = Flask(__name__)

# 【關鍵修正】設定密鑰以啟用 session 儲存功能
# 您可以隨意更換這段字串，它負責加密儲存在瀏覽器的 session 資料
app.secret_key = os.urandom(24)

# 1. 首頁
@app.route('/')
def home():
    # 每次進入首頁時，可以選擇是否清空舊對話
    # session.clear() 

    # --- 新增的部分 ---
    # 建議將您的 LIFF ID 存放在這裡，或是之後放在 .env 環境變數中
    LIFF_ID = os.getenv('LINE_LIFF_ID')
    
    # render_template 除了回傳網頁，後面的參數 liff_id=LIFF_ID 
    # 會把變數傳給 HTML 裡的 {{ liff_id }}
    return render_template('index.html', liff_id=LIFF_ID)

# 2. API: 聊聊情緒
@app.route('/api/chat', methods=['POST'])
def chat_emotion():
    data = request.json
    user_input = data.get('message', '')
    
    if not user_input:
        return jsonify({"error": "No message provided"}), 400

    # --- 記憶邏輯開始 ---
    # 從 session 取得歷史紀錄，若無則初始化
    if 'history' not in session:
        session['history'] = []

    # 將使用者的話加入歷史 (符合 OpenAI 格式)
    session['history'].append({"role": "user", "content": user_input})

    # 限制歷史長度（只記住最近 10 則對話，避免處理時間過長或超出 Token 限制）
    context = session['history'][-10:]

    # 呼叫 ai_service，並傳入「完整的上下文 context」
    # 注意：待會我們也要同步修改 ai_service.py 的接收方式
    result = ai_service.get_emotion_response(context)
    
    # 將 AI 的回覆文字也存入歷史紀錄，讓下一次對話能延續
    if result and 'reply' in result:
        session['history'].append({"role": "assistant", "content": result['reply']})
    
    # 標記 session 已修改，確保資料寫入
    session.modified = True
    # --- 記憶邏輯結束 ---

    return jsonify(result)

# 3. API: 轉化語氣 (語氣轉化通常是單次執行，若不需要記憶可維持原樣)
@app.route('/api/tone', methods=['POST'])
def transform_tone():
    data = request.json
    text = data.get('text', '')
    tone = data.get('tone', '溫和')
    modifier = data.get('modifier', '')
    
    # 轉化語氣通常不需要對話記憶，因此維持現狀
    result_data = ai_service.get_tone_rewrite(text, tone, modifier)
    
    return jsonify(result_data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)