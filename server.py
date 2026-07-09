from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os

app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

DATA_FILE = "data.json"

# データファイルがなければ作成
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)


@app.route("/add", methods=["POST"])
def add_marker():
    data = request.json
    data["approved"] = False  # 承認状態を追加

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        markers = json.load(f)

    markers.append(data)

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(markers, f, ensure_ascii=False, indent=2)

    return jsonify({"status": "ok"})


@app.route("/list", methods=["GET"])
def list_markers():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        markers = json.load(f)
    return jsonify(markers)


@app.route("/approve", methods=["POST"])
def approve_marker():
    index = request.json.get("index")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        markers = json.load(f)

    if 0 <= index < len(markers):
        markers[index]["approved"] = True

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(markers, f, ensure_ascii=False, indent=2)

        return jsonify({"status": "ok"})

    return jsonify({"status": "error"}), 400


@app.route("/delete", methods=["POST"])
def delete_marker():
    index = request.json.get("index")

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        markers = json.load(f)

    if 0 <= index < len(markers):
        markers.pop(index)

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(markers, f, ensure_ascii=False, indent=2)

        return jsonify({"status": "ok"})

    return jsonify({"status": "error"}), 400


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
