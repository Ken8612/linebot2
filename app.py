from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
import os
import json

app = Flask(__name__)

# LINE Bot configuration
CHANNEL_ACCESS_TOKEN = 'YOUR_CHANNEL_ACCESS_TOKEN'
CHANNEL_SECRET = 'YOUR_CHANNEL_SECRET'

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(CHANNEL_SECRET)

# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
SPREADSHEET_ID = '17kJHc0aJp7K3Gsxrjes9ZCSVwadD9tPm-enQBs25tg4'

# Load Google credentials
def get_credentials():
    creds = None
    if os.path.exists('token.json'):
        with open('token.json', 'r') as token:
            creds = json.load(token)
    if not creds or not creds.valid:
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            json.dump(creds.to_json(), token)
    return creds

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
    text = event.message.text
    response = f"你說的是: {text}"

    # Example: Insert data to Google Sheets
    creds = get_credentials()
    service = build('sheets', 'v4', credentials=creds)
    sheet = service.spreadsheets()
    sheet.values().append(
        spreadsheetId=SPREADSHEET_ID,
        range="Sheet1!A1",
        valueInputOption="RAW",
        body={"values": [[text]]}
    ).execute()

    line_bot_api.reply_message(
        event.reply_token,
        TextMessage(text=response)
    )

if __name__ == "__main__":
    app.run(debug=True)
