import os
import sqlite3
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, session, send_file

app = Flask(__name__)
app.secret_key = "segredo123"

PLANOS = {
    "free": 2,
    "pro": 50
}

# ================= DB =================
def conectar():
    return sqlite3.connect("database.db")

def criar_db():
    con = conectar()
    cur = con.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT,
        plano TEXT DEFAULT 'free',
        downloads INTEGER DEFAULT 0,
        ultima_reset TEXT
    )
    """)

    con.commit()
    con.close()

criar_db()

# ================= RESET =================
def reset(user):
    hoje = datetime.now()

    if user[6]:
        ultima = datetime.strptime(user[6], "%Y-%m-%d")
        if hoje - ultima >= timedelta(days=7):
            return True
    else:
        return True

    return False

# ================= BUSCAR TIKTOK =================
def buscar_videos(query):
    # ⚠️ Aqui é MOCK (substitua por API real depois)
    videos = []

    for i in range(8):
        videos.append({
            "video": "https://www.w3schools.com/html/mov_bbb.mp4",
            "thumb": "",
            "likes": 1000 + i*200
        })

    return videos

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        senha = request.form["password"]

        con = conectar()
        cur = con.cursor()

        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user, senha))
        u = cur.fetchone()

        if u:
            if reset(u):
                cur.execute("UPDATE users SET downloads=0, ultima_reset=? WHERE id=?",
                            (datetime.now().strftime("%Y-%m-%d"), u[0]))
                con.commit()

            session["user"] = user
            return redirect("/dashboard")

        return "Login inválido"

    return render_template("login.html")

# ================= REGISTER =================
@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        con = conectar()
        cur = con.cursor()

        cur.execute("INSERT INTO users (username,email,password) VALUES (?,?,?)",
                    (request.form["username"], request.form["email"], request.form["password"]))

        con.commit()
        con.close()

        return redirect("/")

    return render_template("register.html")

# ================= DASHBOARD =================
@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    con = conectar()
    cur = con.cursor()

    cur.execute("SELECT * FROM users WHERE username=?", (session["user"],))
    user = cur.fetchone()

    limite = PLANOS[user[4]]
    restante = limite - user[5]

    videos = []

    if request.method == "POST":
        query = request.form["query"]
        videos = buscar_videos(query)

    return render_template("dashboard.html",
                           videos=videos,
                           restante=restante,
                           plano=user[4])

# ================= DOWNLOAD =================
@app.route("/download", methods=["POST"])
def download():
    if "user" not in session:
        return redirect("/")

    con = conectar()
    cur = con.cursor()

    cur.execute("SELECT * FROM users WHERE username=?", (session["user"],))
    user = cur.fetchone()

    if user[5] >= PLANOS[user[4]]:
        return "Limite atingido"

    url = request.form.get("video")

    r = requests.get(url)

    with open("video.mp4", "wb") as f:
        f.write(r.content)

    cur.execute("UPDATE users SET downloads = downloads + 1 WHERE id=?", (user[0],))
    con.commit()

    return send_file("video.mp4", as_attachment=True)

# ================= UPGRADE =================
@app.route("/upgrade")
def upgrade():
    return render_template("upgrade.html")

@app.route("/comprar", methods=["POST"])
def comprar():
    con = conectar()
    cur = con.cursor()

    cur.execute("UPDATE users SET plano='pro' WHERE username=?", (session["user"],))
    con.commit()

    return redirect("/dashboard")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)