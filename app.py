from flask import Flask, render_template_string, request, redirect, session, send_file
import sqlite3
import os
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "segredo_super_forte"

DB = "database.db"
PASTA = "downloads"

os.makedirs(PASTA, exist_ok=True)

# ================= BANCO =================
def conectar():
    return sqlite3.connect(DB)

def criar_db():
    conn = conectar()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        email TEXT,
        password TEXT,
        plano TEXT DEFAULT 'free',
        downloads INTEGER DEFAULT 0,
        reset_data TEXT
    )
    """)

    conn.commit()
    conn.close()

criar_db()

# ================= LIMITES =================
def pode_baixar(user):
    if user["plano"] == "premium":
        return True

    # reset semanal
    if user["reset_data"]:
        if datetime.now() > datetime.fromisoformat(user["reset_data"]):
            conn = conectar()
            c = conn.cursor()
            c.execute("UPDATE users SET downloads=0, reset_data=? WHERE id=?",
                      ((datetime.now() + timedelta(days=7)).isoformat(), user["id"]))
            conn.commit()
            conn.close()
            return True

    return user["downloads"] < 2

# ================= HTML =================
HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Download TikTok</title>
<style>
body{background:#0f172a;color:white;font-family:Arial;text-align:center}
.card{background:#1e293b;padding:20px;border-radius:15px;width:300px;margin:auto;margin-top:50px}
input,button{width:90%;padding:10px;margin:5px;border-radius:10px;border:none}
button{background:#22c55e;color:white;cursor:pointer}
</style>
</head>
<body>

<div class="card">
<h2>🔥 Downloader TikTok</h2>

{% if not session.get("user") %}

<form method="post" action="/login">
<input name="username" placeholder="Usuário">
<input name="password" placeholder="Senha" type="password">
<button>Entrar</button>
</form>

<form method="post" action="/register">
<input name="username" placeholder="Usuário">
<input name="email" placeholder="Email">
<input name="password" placeholder="Senha" type="password">
<button>Criar Conta</button>
</form>

{% else %}

<p>👤 {{user["username"]}}</p>
<p>📦 Plano: {{user["plano"]}}</p>
<p>⬇️ Downloads: {{user["downloads"]}}</p>

<form method="post" action="/download">
<input name="url" placeholder="Cole o link do TikTok">
<button>Baixar</button>
</form>

<a href="/logout"><button>Sair</button></a>

{% endif %}
</div>

</body>
</html>
"""

# ================= ROTAS =================

@app.route("/")
def home():
    user = None

    if "user" in session:
        conn = conectar()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id=?", (session["user"],))
        row = c.fetchone()
        conn.close()

        if row:
            user = {
                "id": row[0],
                "username": row[1],
                "email": row[2],
                "password": row[3],
                "plano": row[4],
                "downloads": row[5],
                "reset_data": row[6]
            }

    return render_template_string(HTML, user=user)

# ================= LOGIN =================
@app.route("/login", methods=["POST"])
def login():
    user = request.form["username"]
    senha = request.form["password"]

    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? AND password=?", (user, senha))
    row = c.fetchone()
    conn.close()

    if row:
        session["user"] = row[0]

    return redirect("/")

# ================= REGISTER =================
@app.route("/register", methods=["POST"])
def register():
    user = request.form["username"]
    email = request.form["email"]
    senha = request.form["password"]

    conn = conectar()
    c = conn.cursor()
    c.execute("INSERT INTO users (username,email,password,reset_data) VALUES (?,?,?,?)",
              (user, email, senha, (datetime.now()+timedelta(days=7)).isoformat()))
    conn.commit()
    conn.close()

    return redirect("/")

# ================= DOWNLOAD =================
@app.route("/download", methods=["POST"])
def download():
    if "user" not in session:
        return redirect("/")

    url = request.form["url"]

    conn = conectar()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (session["user"],))
    row = c.fetchone()

    user = {
        "id": row[0],
        "plano": row[4],
        "downloads": row[5],
        "reset_data": row[6]
    }

    if not pode_baixar(user):
        return "Limite atingido (Plano grátis)"

    # API simples
    api = f"https://tikwm.com/api/?url={url}"
    r = requests.get(api).json()

    if "data" not in r:
        return "Erro ao baixar"

    video_url = r["data"]["play"]

    nome = os.path.join(PASTA, f"video_{datetime.now().timestamp()}.mp4")

    video = requests.get(video_url)

    with open(nome, "wb") as f:
        f.write(video.content)

    # atualiza contador
    c.execute("UPDATE users SET downloads = downloads + 1 WHERE id=?", (user["id"],))
    conn.commit()
    conn.close()

    return send_file(nome, as_attachment=True)

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)