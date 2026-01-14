import os
import asyncio
import traceback
import time
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# 1. 載入環境變數
load_dotenv()

# 2. 從 services 模組導入核心函式
from services import get_little_tone_final_response

app = Flask(__name__)
CORS(app)

# 限制請求大小上限為 5MB
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 


user_requests = {}

def check_rate_limit():
    """
    檢查目前請求的 IP 是否發送過於頻繁
    """
    # 取得真實 IP (考慮到 Vercel/Cloudflare 轉發)
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]
    current_time = time.time()
    
    # 設定限制：同一 IP 必須間隔 5 秒才能發送下一次
    LIMIT_SECONDS = 5
    
    if ip in user_requests:
        last_request_time = user_requests[ip]
        if current_time - last_request_time < LIMIT_SECONDS:
            return False, LIMIT_SECONDS - (current_time - last_request_time)
            
    # 更新請求時間
    user_requests[ip] = current_time
    return True, 0

@app.route('/api/chat', methods=['POST'])
async def chat_endpoint():
    """
    接收前端 Payload 並回傳 AI 建議。
    整合了 Rate Limit、Base64 安全檢查與暖心安撫語。
    """
    try:
        # --- [第一道防線] Rate Limit 檢查 ---
        # 取得真實 IP (優先從 Cloudflare/Vercel 的 Header 抓取)
        ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(',')[0]
        current_time = time.time()
        
        # 設定限制：同一 IP 必須間隔 5 秒才能發送下一次
        LIMIT_SECONDS = 5
        if ip in user_requests:
            last_request_time = user_requests[ip]
            if current_time - last_request_time < LIMIT_SECONDS:
                wait_time = int(LIMIT_SECONDS - (current_time - last_request_time))
                print(f"[Security] Rate Limit 觸發: {ip} (需等待 {wait_time}s)")
                return jsonify({
                    "status": "error",
                    "message": f"哎呀，你點太快了啦！LittleTone 還在努力思考中... 🍵 請等 {wait_time} 秒後再試一次喔！",
                    "error_type": "rate_limit"
                }), 429
        
        # 更新該 IP 的請求時間
        user_requests[ip] = current_time

        # --- [第二道防線] 內容驗證 ---
        data = request.json
        if not data:
            return jsonify({"status": "error", "message": "無效的請求內容"}), 400

        user_text = data.get('message', '')
        image_base64 = data.get('image', None)  
        chat_history = data.get('history', []) 

        if not user_text and not image_base64:
            return jsonify({"status": "error", "message": "請提供文字訊息或圖片截圖"}), 400

        # --- [第三道防線] Base64 字串長度檢查 ---
        if image_base64 and len(image_base64) > 4 * 1024 * 1024:
            print(f"[Security] 攔截過大的 Base64 請求 (長度: {len(image_base64)})")
            return jsonify({"status": "error", "message": "圖片檔案過大，請選擇較小的截圖"}), 413

        # 紀錄 Log 方便 Debug
        has_image = "有" if image_base64 else "無"
        print(f"[App] 處理請求 IP: {ip} | 文字: {user_text[:10]}... | 歷史: {len(chat_history)} 則 | 圖片: {has_image}")
        
        # --- 3. 呼叫核心服務 ---
        ai_json_result = await get_little_tone_final_response(
            user_text, 
            image_base64, 
            history=chat_history
        )

        # 4. 回傳結果
        return jsonify({
            "status": "success",
            "data": ai_json_result
        })

    except Exception as e:
        traceback.print_exc()
        print(f"[App] 伺服器錯誤: {str(e)}")
        # 這裡也加入一點人情味，避免噴出冷冰冰的 500 錯誤
        return jsonify({
            "status": "error", 
            "message": "哎呀，LittleTone 的大腦稍微斷線了... 🔌 麻煩再試一次好嗎？"
        }), 500

@app.route('/', methods=['GET'])
def index():
    """ 渲染首頁並傳遞 LIFF ID 給前端 """
    liff_id = os.getenv('LINE_LIFF_ID', '')
    if not liff_id:
        print("[Warning] .env 中未設定 LINE_LIFF_ID")
    return render_template('index.html', liff_id=liff_id)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "alive", "service": "LittleTone", "version": "2.5"})

# 錯誤處理：檔案超過 5MB 時自動回傳 413
@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({"status": "error", "message": "上傳內容過大，已遭系統攔截"}), 413

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)