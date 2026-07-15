from flask import Flask, request, jsonify, send_from_directory, url_for,render_template, redirect,Flash
from flask_cors import CORS
import json
import os
from .env import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user,
    login_required, logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash



app = Flask(__name__, static_folder="static", static_url_path="")
CORS(app)

DATA_FILE = "data.json"

# データファイルがなければ作成
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=2)

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"          # 未ログイン時にリダイレクトするページ
login_manager.login_message = "先にログインしてください"

# ---------- ユーザーモデル ----------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    def set_password(self, password):
        # パスワードをそのまま保存せず、ハッシュ化して保存する
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        # 入力されたパスワードとハッシュを照合する
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    # セッションに保存されたIDからユーザーを復元する
    return db.session.get(User, int(user_id))


# ---------- ルーティング ----------



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
    return redirect(url_for("choose")) if current_user.is_authenticated else redirect(url_for("login"))


@app.route("/choose")
@login_required
def choose():
    # ログインしていない人はここに来ると自動的に /login に飛ばされる
    return render_template("choose.html", username=current_user.username)

@app.route('/post')
@login_required
def post():
    return render_template('post.html')

@app.route('/support')
@login_required
def support():
    return render_template('support.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if not username or not password:
            flash("ユーザー名とパスワードを入力してください")
            return redirect(url_for("register"))

        if User.query.filter_by(username=username).first():
            flash("そのユーザー名はすでに使われています")
            return redirect(url_for("register"))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash("登録が完了しました。ログインしてください")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username).first()

        if user is None or not user.check_password(password):
            flash("ユーザー名またはパスワードが違います")
            return redirect(url_for("login"))

        login_user(user)
        return redirect(url_for("choose"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()  # 初回起動時にusers.dbとテーブルを自動作成
    # スマホの実機から接続確認したい場合は host="0.0.0.0" のままでOK
    app.run(host="0.0.0.0", port=5050, debug=True)

if __name__ == '__main__':
    app.run(debug=True)
