import os
import sqlite3
import requests
import uuid

from flask import Flask, render_template, request, redirect, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "superseguro123")

DB = "database.db"
PASTA = "downloads"

os.makedirs(PASTA, exist_ok=True)

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password TEXT,
        plano TEXT DEFAULT 'free',
        downloads INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= DOWNLOAD TIKTOK =================
def baixar_video(url):
    try:
        api = f"https://tikwm.com/api/?url={url}"
        data = requests.get(api).json()

        if "data" not in data:
            return None

        video_url = data["data"]["play"]

        nome = f"{uuid.uuid4().hex}.mp4"
        path = os.path.join(PASTA, nome)

        r = requests.get(video_url, stream=True)

        if r.status_code != 200:
            return None

        with open(path, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

        return path

    except:
        return None

# ================= ROTAS =================

@app.route("/")
def home():
    if "user" in session:
        return redirect("/dashboard")
    return redirect("/login")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        user = request.form.get("username")
        senha = request.form.get("password")

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (user,))
        data = c.fetchone()
        conn.close()

        if data and check_password_hash(data[3], senha):
            session["user"] = data[1]
            return redirect("/dashboard")
        else:
            erro = "Login inválido"

    return render_template("login.html", erro=erro)

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    erro = None

    if request.method == "POST":
        user = request.form.get("username")
        email = request.form.get("email")
        senha = request.form.get("password")

        if not user or not email or not senha:
            erro = "Preencha tudo"
            return render_template("register.html", erro=erro)

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (username,email,password) VALUES (?,?,?)",
                      (user, email, generate_password_hash(senha)))
            conn.commit()
        except:
            erro = "Usuário já existe"
            return render_template("register.html", erro=erro)

        conn.close()
        return redirect("/login")

    return render_template("register.html", erro=erro)

# ---------- DASHBOARD ----------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    erro = None
    video = None

    if request.method == "POST":
        url = request.form.get("url")

        if not url or "tiktok.com" not in url:
            erro = "Link inválido"
            return render_template("dashboard.html", erro=erro)

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("SELECT downloads, plano FROM users WHERE username=?",
                  (session["user"],))
        data = c.fetchone()

        downloads, plano = data

        if plano == "free" and downloads >= 2:
            erro = "Limite do plano grátis atingido!"
        else:
            path = baixar_video(url)

            if path:
                video = path
                c.execute("UPDATE users SET downloads = downloads + 1 WHERE username=?",
                          (session["user"],))
                conn.commit()
            else:
                erro = "Erro ao baixar vídeo"

        conn.close()

    return render_template("dashboard.html", erro=erro, video=video)

# ---------- DOWNLOAD ----------
@app.route("/download")
def download():
    path = request.args.get("file")

    if not path or not os.path.exists(path):
        return "Arquivo não encontrado"

    return send_file(path, as_attachment=True)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)