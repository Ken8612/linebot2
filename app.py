from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import gspread
from google.oauth2.service_account import Credentials
import json
import os
import uvicorn

app = FastAPI()

# 讀取環境變數
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")

# 環境變數檢查
if not all([LINE_CHANNEL_ACCESS_TOKEN, LINE_CHANNEL_SECRET, GOOGLE_CREDENTIALS, SPREADSHEET_ID]):
    raise ValueError("請確認所有環境變數都已設定")

# 設定 LINE Bot
line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

# 設定 Google Sheets API
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
creds_json = json.loads(GOOGLE_CREDENTIALS)
creds = Credentials.from_service_account_info(creds_json, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# Google Sheets 寫入函式
def record_order(amount):
    try:
        sheet.append_row(["叫貨", amount])
        return True
    except Exception as e:
        print(f"寫入 Google Sheets 失敗: {e}")
        return False

def record_pending_order(item):
    try:
        sheet.append_row(["待訂", item])
        return True
    except Exception as e:
        print(f"寫入 Google Sheets 失敗: {e}")
        return False

# 處理 LINE 訊息
@app.post("/webhook")
async def webhook(request: Request):
    body = await request.text()
    signature = request.headers.get("X-Line-Signature")

    try:
        events = parser.parse(body, signature)
        for event in events:
            if isinstance(event, MessageEvent) and isinstance(event.message, TextMessage):
                user_message = event.message.text
                reply_token = event.reply_token

                if user_message.startswith("#叫貨"):
                    amount = user_message.replace("#叫貨", "").strip()
                    if record_order(amount):
                        response = f"✅ 已記錄叫貨金額: {amount} 元"
                    else:
                        response = "⚠️ 叫貨記錄失敗，請稍後再試"

                elif user_message.startswith("#待訂"):
                    item = user_message.replace("#待訂", "").strip()
                    if record_pending_order(item):
                        response = f"✅ 已記錄待訂貨品: {item}"
                    else:
                        response = "⚠️ 待訂記錄失敗，請稍後再試"

                else:
                    response = "請使用 #叫貨 或 #待訂 指令"

                line_bot_api.reply_message(reply_token, TextSendMessage(text=response))

    except Exception as e:
        print(f"Webhook 處理錯誤: {e}")

    return "OK"

# Render 啟動 FastAPI
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
