import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import os

app = Flask(__name__)

# LINE Bot 設定
CHANNEL_ACCESS_TOKEN = os.getenv("CHANNEL_ACCESS_TOKEN")
CHANNEL_SECRET = os.getenv("CHANNEL_SECRET")
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# 設定 Google Sheets API 權限
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

# 開啟 Google 試算表
SPREADSHEET_ID = "17kJHc0aJp7K3Gsxrjes9ZCSVwadD9tPm-enQBs25tg4"
sheet = client.open_by_key(SPREADSHEET_ID).sheet1  # 選擇第一個工作表

def save_order_to_sheets(order_list):
    """將訂單內容寫入 Google Sheets"""
    for item in order_list:
        sheet.append_row(item)  # 將每個訂單寫入新行

# 訂單格式解析
def parse_order(text):
    """解析訂單內容，例如 'Clear(magsafe) 12 *3' 轉成 ('Clear(magsafe) 12', 3)"""
    orders = []
    for line in text.split("\n"):
        parts = line.split("*")
        if len(parts) == 2:
            product, quantity = parts[0].strip(), parts[1].strip()
            orders.append([product, quantity])  # 格式：[商品名稱, 數量]
    return orders

@app.route("/callback", methods=["POST"])
def callback():
    """處理 LINE Webhook"""
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, request.headers)
    except Exception as e:
        print(f"Error: {e}")
    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """處理 LINE 訊息"""
    user_message = event.message.text.strip()
    
    if user_message.startswith("訂單"):
        # 解析訂單內容
        order_text = user_message.replace("訂單", "").strip()
        order_list = parse_order(order_text)

        # 儲存到 Google Sheets
        save_order_to_sheets(order_list)

        # 回覆用戶
        response_text = "✅ 訂單已儲存到 Google Sheets！\n\n" + "\n".join([f"{p} * {q}" for p, q in order_list])
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=response_text))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)