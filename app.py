from flask import Flask, request, jsonify, render_template, url_for
from flask_cors import CORS
import json
import os

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("choose.html")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
