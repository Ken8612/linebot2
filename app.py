from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage, TextSendMessage, SourceUser, SourceGroup, SourceRoom
from linebot.exceptions import InvalidSignatureError
import os

app = Flask(__name__)

# 設定 LINE Bot 憑證（建議從環境變數讀取）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "你的 Channel Access Token")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET", "你的 Channel Secret")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

@app.route("/", methods=["GET"])
def home():
    return "LINE Bot is running."

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_message = event.message.text

    # 判斷訊息來自哪裡
    if isinstance(event.source, SourceGroup):  # 來自群組
        source_id = event.source.group_id
        source_type = "群組"
    elif isinstance(event.source, SourceRoom):  # 來自聊天室
        source_id = event.source.room_id
        source_type = "聊天室"
    else:  # 來自個人聊天
        source_id = event.source.user_id
        source_type = "個人"

    reply = f"你說：{user_message}\n來源：{source_type}\nID: {source_id}"
    line_bot_api.reply_message(event.reply_token, TextSendMessage(text=reply))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # 確保 Render 能讀取正確的 PORT
    app.run(host="0.0.0.0", port=port)