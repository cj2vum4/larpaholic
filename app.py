# app.py
import os
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 從環境變數取得 LINE Bot 設定（部署時會設定）
line_bot_api = LineBotApi(os.environ.get('CHANNEL_ACCESS_TOKEN'))
handler = WebhookHandler(os.environ.get('CHANNEL_SECRET'))

# 你的個人 LINE User ID（需要稍後設定）
YOUR_USER_ID = os.environ.get('YOUR_USER_ID', 'YOUR_USER_ID_HERE')

@app.route("/")
def hello():
    return "LINE OA Webhook Server is running!"

@app.route("/webhook", methods=['POST'])
def callback():
    # 取得 X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    
    # 取得 request body
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)
    
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    try:
        # 取得訊息內容
        user_message = event.message.text
        user_id = event.source.user_id if hasattr(event.source, 'user_id') else 'Unknown'
        
        # 詳細記錄收到的訊息
        print(f"=== 收到訊息 ===")
        print(f"用戶 ID: {user_id}")
        print(f"訊息內容: {user_message}")
        print(f"設定的 YOUR_USER_ID: {YOUR_USER_ID}")
        print(f"==================")
        
        # 建立轉發訊息
        forward_text = f"""🔔 OA 收到新訊息！

👤 來源用戶：{user_id}
💬 訊息內容：{user_message}
⏰ 時間：{event.timestamp}

---
來自 LINE OA 自動轉發"""
        
        # 轉發訊息到你的個人 LINE
        if YOUR_USER_ID and YOUR_USER_ID != 'YOUR_USER_ID_HERE':
            try:
                line_bot_api.push_message(
                    YOUR_USER_ID,
                    TextSendMessage(text=forward_text)
                )
                print(f"✅ 訊息已轉發給 {YOUR_USER_ID}")
            except Exception as push_error:
                print(f"❌ 轉發失敗: {push_error}")
        else:
            print("⚠️ 警告：YOUR_USER_ID 尚未正確設定")
            
        # 可選：回覆原始用戶
        reply_text = f"謝謝您的訊息！[Debug: 你的ID是 {user_id}]"
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_text)
        )
        
    except Exception as e:
        print(f"❌ 處理訊息時發生錯誤: {e}")
        import traceback
        traceback.print_exc()

# 處理其他類型的事件（加入好友、取消關注等）
@handler.add(MessageEvent)
def handle_other_message(event):
    try:
        if hasattr(event.source, 'user_id'):
            user_id = event.source.user_id
        else:
            user_id = 'Unknown'
            
        # 通知有其他類型的互動
        notification_text = f"""📢 OA 有新的互動！

👤 用戶：{user_id}
📝 事件類型：{event.message.type}
⏰ 時間：{event.timestamp}

---
來自 LINE OA 自動轉發"""
        
        if YOUR_USER_ID and YOUR_USER_ID != 'YOUR_USER_ID_HERE':
            line_bot_api.push_message(
                YOUR_USER_ID,
                TextSendMessage(text=notification_text)
            )
            
    except Exception as e:
        print(f"處理其他訊息時發生錯誤: {e}")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
