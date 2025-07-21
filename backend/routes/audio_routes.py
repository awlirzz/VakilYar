"""
audio_routes – endpoint صوتی /chatbot/audio
"""
from flask import Blueprint, request, jsonify
from backend import bot
from backend.audio_handler import transcribe, TranscriptionError

bp_audio = Blueprint("audio_routes", __name__)


@bp_audio.post("/chatbot/audio")
def chat_audio():
    if "audio" not in request.files:
        return jsonify({"error": "فایل audio ارسال نشده است"}), 400

    try:
        transcript = transcribe(request.files["audio"])
    except TranscriptionError as te:
        return jsonify({"error": str(te)}), 400
    except Exception as exc:
        return jsonify({"error": f"خطا در تبدیل گفتار: {exc}"}), 500

    try:
        answer = bot.chat_with_gpt(transcript)
        return jsonify({"transcript": transcript, "answer": answer}), 200
    except Exception as exc:
        return jsonify({"error": f"خطای داخلی: {exc}"}), 500
