import os
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage

# 讀取環境變數
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

# 驗證 Google Sheets API
credentials_dict = json.loads(GOOGLE_CREDENTIALS)
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
gc = gspread.authorize(credentials)

# 連接 Google 試算表
SPREADSHEET_NAME = "叫貨紀錄"
sheet = gc.open(SPREADSHEET_NAME).sheet1

# 初始化 Flask 應用
app = Flask(__name__)

# 初始化 LINE Bot
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text.strip()
    reply_text = ""
    
    if user_message.startswith("叫貨 "):
        try:
            data = user_message[3:].split()
            if len(data) != 2:
                reply_text = "格式錯誤！請使用: 叫貨 品名 金額"
            else:
                item, amount = data
                sheet.append_row([item, amount])
                reply_text = f"已記錄: {item} - {amount} 元"
        except Exception as e:
            reply_text = "記錄失敗，請稍後再試"
    else:
        reply_text = "請使用: 叫貨 品名 金額 來記錄訂單"
    
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply_text))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
