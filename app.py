import os
import sqlite3
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, session, send_file

app = Flask(__name__)
app.secret_key = "segredo123"

# ================= CONFIG =================
PLANOS = {
    "free": 2,
    "pro": 50
}

# ================= BANCO =================
def conectar():
    return sqlite3.connect("database.db")

def criar_db():
    con = conectar()
    cur = con.cursor()

    # usuários
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

    # pagamentos
    cur.execute("""
    CREATE TABLE IF NOT EXISTS pagamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT,
        valor TEXT,
        status TEXT
    )
    """)

    con.commit()
    con.close()

criar_db()

# ================= RESET SEMANAL =================
def reset_semanal(user):
    hoje = datetime.now()

    if user[6]:
        ultima = datetime.strptime(user[6], "%Y-%m-%d")

        if hoje - ultima >= timedelta(days=7):
            return True
    else:
        return True

    return False

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["username"]
        senha = request.form["password"]

        con = conectar()
        cur = con.cursor()

        cur.execute("SELECT * FROM users WHERE username=? AND password=?", (user, senha))
        resultado = cur.fetchone()

        if resultado:
            # reset semanal
            if reset_semanal(resultado):
                cur.execute("""
                UPDATE users SET downloads=0, ultima_reset=?
                WHERE id=?
                """, (datetime.now().strftime("%Y-%m-%d"), resultado[0]))
                con.commit()

            session["user"] = user
            con.close()
            return redirect("/dashboard")

        con.close()

    return render_template("login.html")

# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = request.form["username"]
        email = request.form["email"]
        senha = request.form["password"]

        con = conectar()
        cur = con.cursor()

        cur.execute("INSERT INTO users (username, email, password) VALUES (?,?,?)",
                    (user, email, senha))

        con.commit()
        con.close()

        return redirect("/")

    return render_template("register.html")

# ================= DASHBOARD =================
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect("/")

    con = conectar()
    cur = con.cursor()

    cur.execute("SELECT * FROM users WHERE username=?", (session["user"],))
    user = cur.fetchone()

    limite = PLANOS.get(user[4], 0)
    restante = limite - user[5]

    videos = []

    if request.method == "POST":
        query = request.form.get("query")

        # 🔥 MOCK de vídeos (depois você liga no bot)
        for i in range(6):
            videos.append(f"https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_{i}.mp4")

    con.close()

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

    limite = PLANOS.get(user[4], 0)

    # bloqueio por plano
    if user[5] >= limite:
        con.close()
        return "❌ Limite do plano atingido!"

    videos = request.form.get("videos")

    if not videos:
        return "Nenhum vídeo selecionado!"

    lista = videos.split(",")
    url = lista[0]

    try:
        r = requests.get(url, timeout=10)

        with open("video.mp4", "wb") as f:
            f.write(r.content)

    except:
        return "❌ Erro ao baixar vídeo"

    # soma download
    cur.execute("UPDATE users SET downloads = downloads + 1 WHERE id=?", (user[0],))
    con.commit()
    con.close()

    return send_file("video.mp4", as_attachment=True)

# ================= UPGRADE =================
@app.route("/upgrade")
def upgrade():
    if "user" not in session:
        return redirect("/")
    return render_template("upgrade.html")

# ================= GERAR PIX =================
@app.route("/gerar_pix", methods=["POST"])
def gerar_pix():
    if "user" not in session:
        return redirect("/")

    user = session["user"]

    con = conectar()
    cur = con.cursor()

    cur.execute("""
    INSERT INTO pagamentos (usuario, valor, status)
    VALUES (?, ?, ?)
    """, (user, "19.90", "pendente"))

    con.commit()
    con.close()

    pix_code = "000201PIXFAKE123456789"

    return render_template("pix.html", pix=pix_code)

# ================= CONFIRMAR PAGAMENTO =================
@app.route("/confirmar_pagamento")
def confirmar_pagamento():
    if "user" not in session:
        return redirect("/")

    user = session["user"]

    con = conectar()
    cur = con.cursor()

    cur.execute("UPDATE users SET plano='pro' WHERE username=?", (user,))
    cur.execute("UPDATE pagamentos SET status='pago' WHERE usuario=?", (user,))

    con.commit()
    con.close()

    return redirect("/dashboard")

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= RUN (CORRIGIDO PRO RENDER) =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)