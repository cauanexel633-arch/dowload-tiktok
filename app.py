import os
import sqlite3
import requests
from flask import Flask, render_template, request, redirect, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "segredo123"

DB = "database.db"

# ================= DATABASE =================
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT,
        plano TEXT DEFAULT 'free',
        downloads INTEGER DEFAULT 0
    )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= TIKTOK =================
def baixar_video(url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(url, headers=headers, stream=True)

        if r.status_code != 200:
            return None

        path = "video.mp4"

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
    if request.method == "POST":
        user = request.form["username"]
        senha = request.form["password"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE username=?", (user,))
        data = c.fetchone()

        conn.close()

        if data and check_password_hash(data[3], senha):
            session["user"] = data[1]
            return redirect("/dashboard")

    return render_template("login.html")

# ---------- REGISTER ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        email = request.form["email"]
        senha = generate_password_hash(request.form["password"])

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("INSERT INTO users (username,email,password) VALUES (?,?,?)",
                  (user, email, senha))

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# ---------- DASHBOARD ----------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/login")

    video = None
    erro = None

    if request.method == "POST":
        url = request.form["url"]

        conn = sqlite3.connect(DB)
        c = conn.cursor()

        c.execute("SELECT downloads, plano FROM users WHERE username=?",
                  (session["user"],))
        data = c.fetchone()

        downloads, plano = data

        # limite plano
        if plano == "free" and downloads >= 2:
            erro = "Limite semanal atingido!"
        else:
            video = baixar_video(url)

            if video:
                c.execute("UPDATE users SET downloads = downloads + 1 WHERE username=?",
                          (session["user"],))
                conn.commit()

        conn.close()

    return render_template("dashboard.html", video=video, erro=erro)

# ---------- DOWNLOAD ----------
@app.route("/download")
def download():
    return send_file("video.mp4", as_attachment=True)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

# ================= RUN =================
if __name__ == "__main__":
    app.run(debug=True)