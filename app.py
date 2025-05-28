# app.py - Email 通知版本
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

app = Flask(__name__)

# 從環境變數取得設定
CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN', 'dummy_token')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET', 'dummy_secret')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN) if CHANNEL_ACCESS_TOKEN != 'dummy_token' else None
handler = WebhookHandler(CHANNEL_SECRET)

# Email 設定（從環境變數取得）
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
EMAIL_USER = os.environ.get('EMAIL_USER')  # 發送者 Email
EMAIL_PASS = os.environ.get('EMAIL_PASS')  # 發送者 Email 密碼或應用程式密碼
NOTIFY_EMAIL = os.environ.get('NOTIFY_EMAIL')  # 接收通知的 Email

def send_email_notification(user_id, message_text, timestamp):
    """發送 Email 通知"""
    try:
        # 建立郵件內容
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = NOTIFY_EMAIL
        msg['Subject'] = f"🔔 LINE OA 收到新訊息！"
        
        # 格式化時間
        time_str = datetime.fromtimestamp(timestamp/1000).strftime('%Y-%m-%d %H:%M:%S')
        
        # 郵件內容
        body = f"""
您的 LINE 官方帳號收到新訊息！

👤 來源用戶：{user_id}
💬 訊息內容：{message_text}
⏰ 時間：{time_str}
📱 帳號：@077xhecx

---
來自 LINE OA 自動通知系統
"""
        
        msg.attach(MIMEText(body, 'plain', 'utf-8'))
        
        # 發送郵件
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, NOTIFY_EMAIL, text)
        server.quit()
        
        print(f"✅ Email 通知已發送到 {NOTIFY_EMAIL}")
        return True
        
    except Exception as e:
        print(f"❌ Email 發送失敗: {e}")
        return False

@app.route("/")
def hello():
    return "LINE OA Email 通知服務正在運行！"

@app.route("/webhook", methods=['POST'])
def callback():
    # 取得 signature
    signature = request.headers['X-Line-Signature']
    
    # 取得 request body
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    # 處理 webhook
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
        timestamp = event.timestamp
        
        # 詳細記錄
        print(f"=== 收到訊息 ===")
        print(f"用戶 ID: {user_id}")
        print(f"訊息內容: {user_message}")
        print(f"時間戳記: {timestamp}")
        print(f"==================")
        
        # 發送 Email 通知
        if EMAIL_USER and EMAIL_PASS and NOTIFY_EMAIL:
            email_sent = send_email_notification(user_id, user_message, timestamp)
            if email_sent:
                print("✅ Email 通知發送成功")
            else:
                print("❌ Email 通知發送失敗")
        else:
            print("⚠️ Email 設定不完整，無法發送通知")
            
        # 回覆用戶（可選）
        if line_bot_api:
            try:
                reply_text = "謝謝您的訊息！管理員已收到通知。"
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
            except Exception as reply_error:
                print(f"⚠️ 回覆訊息失敗: {reply_error}")
        else:
            print("⚠️ LINE Bot API 未設定，無法回覆訊息")
        
    except Exception as e:
        print(f"❌ 處理訊息時發生錯誤: {e}")
        import traceback
        traceback.print_exc()

# 處理其他類型的訊息
@handler.add(MessageEvent)
def handle_other_message(event):
    try:
        user_id = event.source.user_id if hasattr(event.source, 'user_id') else 'Unknown'
        message_type = event.message.type
        timestamp = event.timestamp
        
        print(f"=== 收到其他類型訊息 ===")
        print(f"用戶 ID: {user_id}")
        print(f"訊息類型: {message_type}")
        print(f"時間戳記: {timestamp}")
        print(f"========================")
        
        # 發送 Email 通知
        if EMAIL_USER and EMAIL_PASS and NOTIFY_EMAIL:
            send_email_notification(user_id, f"[{message_type}類型訊息]", timestamp)
            
    except Exception as e:
        print(f"❌ 處理其他訊息時發生錯誤: {e}")

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
