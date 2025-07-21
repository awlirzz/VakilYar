"""
chat_routes – endpoint متنی /chatbot/responses
"""
from flask import Blueprint, request, jsonify
from backend import bot

bp_chat = Blueprint("chat_routes", __name__)

AUTHORIZED_DOMAINS = {
    'https://mobit.ir',
    'mobit.ir',
    'www.mobit.ir',
    'http://localhost',
    'http://localhost:5000',
    'localhost',
    'file://',

}


@bp_chat.post("/chatbot/responses")
def chat():
    origin = request.headers.get("X-Domain", "")
    if origin not in AUTHORIZED_DOMAINS:
        return jsonify({"error": "دامنه مجاز نیست"}), 403

    question = (request.get_json(silent=True) or {}).get("question", "").strip()
    if not question:
        return jsonify({"error": "سؤال خالی است"}), 400

    try:
        answer = bot.chat_with_gpt(question)
        return jsonify({"answer": answer}), 200
    except Exception as exc:
        return jsonify({"error": f"خطای داخلی: {exc}"}), 500
