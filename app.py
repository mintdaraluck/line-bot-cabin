import os
import hashlib
import hmac
import base64
import json
import requests
from flask import Flask, request, abort
from sheets import search_by_order, build_message

app = Flask(__name__)

LINE_CHANNEL_SECRET = os.environ.get("LINE_CHANNEL_SECRET", "")
LINE_CHANNEL_ACCESS_TOKEN = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN", "")
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"


def verify_signature(body: bytes, signature: str) -> bool:
    """ตรวจสอบว่า request มาจาก LINE จริง"""
    hash_val = hmac.new(
        LINE_CHANNEL_SECRET.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    expected = base64.b64encode(hash_val).decode("utf-8")
    return hmac.compare_digest(expected, signature)


def reply_message(reply_token: str, text: str):
    """ส่งข้อความตอบกลับไปยัง LINE"""
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
    }
    # LINE จำกัด 5000 ตัวอักษรต่อ message bubble
    if len(text) > 4999:
        text = text[:4996] + "..."

    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": text}],
    }
    requests.post(LINE_REPLY_URL, headers=headers, json=payload)


def handle_text(text: str) -> str:
    """ประมวลผลข้อความจากผู้ใช้"""
    text = text.strip()

    # คำสั่งช่วยเหลือ
    if text in ["help", "ช่วยเหลือ", "วิธีใช้", "?"]:
        return (
            "🚛 วิธีค้นหาหัวเก๋ง\n"
            "─────────────────\n"
            "พิมพ์ตัวเลข 4 หลัก\n"
            "จาก column ลำดับ\n\n"
            "💡 ตัวอย่าง:\n"
            "  พิมพ์: 1788\n"
            "  พิมพ์: 2312\n"
            "  พิมพ์: 2600\n\n"
            "📌 ระบบจะแสดงผลเป็น VIP1788"
        )

    # ค้นหาข้อมูล
    results = search_by_order(text)
    return build_message(results, text)


@app.route("/webhook", methods=["POST"])
def webhook():
    # ตรวจสอบ signature
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data()

    if not verify_signature(body, signature):
        abort(400, "Invalid signature")

    data = json.loads(body.decode("utf-8"))

    for event in data.get("events", []):
        if event.get("type") != "message":
            continue
        if event["message"].get("type") != "text":
            continue

        reply_token = event["replyToken"]
        user_text = event["message"]["text"]

        response_text = handle_text(user_text)
        reply_message(reply_token, response_text)

    return "OK", 200


@app.route("/", methods=["GET"])
def health():
    return "LINE Bot หัวเก๋ง ✅ Running", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
