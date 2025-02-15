import os
import sys
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from linebot import LineBotApi
from linebot.models import TextMessage, Event, MessageEvent
from linebot.exceptions import LineBotApiError
from flask import Flask, request, abort
from datetime import datetime

# Line Bot 設定
CHANNEL_ACCESS_TOKEN = 'YOUR_LINE_CHANNEL_ACCESS_TOKEN'
CHANNEL_SECRET = 'YOUR_LINE_CHANNEL_SECRET'
line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)

# Google Sheets API 設定
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = 'YOUR_GOOGLE_SHEET_ID'

# 設定 Flask 應用程式
app = Flask(__name__)

# Google Sheets 服務設定
def get_google_sheets_service():
    credentials = Credentials.from_service_account_file(
        'path-to-your-service-account-credentials.json', scopes=SCOPES)
    service = build('sheets', 'v4', credentials=credentials)
    return service.spreadsheets()

# 記錄訊息到 Google Sheets
def record_to_google_sheets(user_id, user_message):
    try:
        service = get_google_sheets_service()
        range_ = 'Sheet1!A1:C1'  # 你希望寫入數據的範圍
        values = [
            [user_id, user_message, str(datetime.now())]  # 用戶 ID、訊息、時間
        ]
        body = {
            'values': values
        }
        result = service.values().append(spreadsheetId=SPREADSHEET_ID, range=range_,
                                          valueInputOption="RAW", body=body).execute()
        print(f"Updated {result.get('updates').get('updatedCells')} cells.")
    except Exception as e:
        print(f"Error recording to Google Sheets: {e}")

# 設定 Line Webhook 處理函數
@app.route("/callback", methods=['POST'])
def callback():
    if request.method == 'POST':
        body = request.get_data(as_text=True)
        signature = request.headers['X-Line-Signature']

        try:
            events = line_bot_api.parse_events_from_json(body, signature)
            for event in events:
                if isinstance(event, MessageEvent):
                    user_message = event.message.text
                    user_id = event.source.user_id
                    # 記錄訊息到 Google Sheets
                    record_to_google_sheets(user_id, user_message)
                    # 回覆用戶
                    line_bot_api.reply_message(
                        event.reply_token,
                        TextMessage(text=f"已收到您的訊息：{user_message}")
                    )
        except LineBotApiError as e:
            print(f"Error occurred: {e}")
            abort(400)
        return 'OK'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
