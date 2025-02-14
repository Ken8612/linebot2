import os
import json
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# LINE API 設定
LINE_CHANNEL_ACCESS_TOKEN = "你的 Channel Access Token"
LINE_CHANNEL_SECRET = "你的 Channel Secret"
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# Google Sheets 設定
SPREADSHEET_ID = "17kJHc0aJp7K3Gsxrjes9ZCSVwadD9tPm-enQBs25tg4"
SHEET_NAME = "叫貨紀錄"

# 從環境變數加載 credentials.json
credentials_json = os.getenv("GOOGLE_CREDENTIALS")
if credentials_json is None:
    raise ValueError("GOOGLE_CREDENTIALS 環境變數未設定")

credentials_dict = json.loads(credentials_json)
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(credentials_dict, scopes=scope)

# 啟用 Google Sheets API
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)

# 設定關鍵字篩選
KEYWORDS = ["記錄", "存檔", "備忘"]

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running."

@app.route("/callback", methods=["POST"])
def callback():
    body = request.get_data(as_text=True)
    handler.handle(body, request.headers["X-Line-Signature"])
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # 檢查是否包含關鍵字
    if any(keyword in user_message for keyword in KEYWORDS):
        user_id = event.source.user_id
        timestamp = event.timestamp

        # 寫入 Google Sheets
        try:
            sheet.append_row([user_id, user_message, timestamp])
        except Exception as e:
            print(f"Error appending row to Google Sheets: {e}")
            line_bot_api.reply_message(event.reply_token, TextMessage(text="儲存失敗，請稍後再試！"))
            return
        
        # 回覆使用者
        line_bot_api.reply_message(event.reply_token, TextMessage(text="訊息已記錄！"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)