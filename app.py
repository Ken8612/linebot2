from fastapi import FastAPI, Request
from linebot import LineBotApi, WebhookParser
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import gspread
from google.oauth2.service_account import Credentials
import os

app = FastAPI()

# LINE Bot 設定
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(LINE_CHANNEL_SECRET)

# Google Sheets API 設定
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "credentials.json"  # 你的 Google 憑證 JSON 檔案
SPREADSHEET_ID = "工作表1"

creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open_by_key(SPREADSHEET_ID).sheet1

# Google Sheets 寫入函式
def record_order(amount):
    sheet.append_row(["叫貨", amount])

def record_pending_order(item):
    sheet.append_row(["待訂", item])

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
                    record_order(amount)
                    response = f"已記錄叫貨金額: {amount} 元"

                elif user_message.startswith("#待訂"):
                    item = user_message.replace("#待訂", "").strip()
                    record_pending_order(item)
                    response = f"已記錄待訂貨品: {item}"

                else:
                    response = "請使用 #叫貨 或 #待訂 指令"

                line_bot_api.reply_message(reply_token, TextSendMessage(text=response))

    except Exception as e:
        print(f"Error: {e}")

    return "OK"

# Render 啟動 FastAPI
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
