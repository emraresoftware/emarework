# {{PROJE_AD}} — Flask Giriş Noktası

from flask import Flask, render_template, jsonify
import os


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", "emare-dev-key")

    @app.route("/")
    def index():
        return render_template("index.html", title="{{PROJE_AD}}")

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "app": "{{PROJE_AD}}"})

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port={{PROJE_PORT}}, debug=True)
