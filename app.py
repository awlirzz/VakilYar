"""
Bootstrap Flask app + ثبت روت‌ها + CORS و Sentry
"""
import os
from flask import Flask
from flask_cors import CORS
import sentry_sdk

from backend.routes.chat_routes import bp_chat
from backend.routes.audio_routes import bp_audio

# ───────────────────────────── sentry
sentry_sdk.init(
    dsn="https://ef6083428e8791ad603a1d53b6a6666c@sentry.kloudify.net/53",
    traces_sample_rate=1.0,
)

# ───────────────────────────── flask
def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    # Register blueprints
    app.register_blueprint(bp_chat)
    app.register_blueprint(bp_audio)

    return app


# ───────────────────────────── run local
if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
