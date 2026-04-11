import sqlite3
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "segredo_super_forte"

# ================= DB =================
def db():
    return sqlite3.connect("database.db")

def criar_db():
    conn = db()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        login TEXT UNIQUE,
        email TEXT,
        senha TEXT,
        plano TEXT,
        downloads INTEGER,
        reset_date TEXT
    )
    """)

    conn.commit()
    conn.close()

criar_db()

# ================= RESET =================
def resetar(user):
    hoje = datetime.now()
    reset = datetime.strptime(user[6], "%Y-%m-%d")

    if hoje >= reset:
        conn = db()
        c = conn.cursor()

        novo = (hoje + timedelta(days=7)).strftime("%Y-%m-%d")

        c.execute("""
        UPDATE users SET downloads = 0, reset_date = ?
        WHERE id = ?
        """, (novo, user[0]))

        conn.commit()
        conn.close()

# ================= ROTAS =================

@app.route("/")
def home():
    if "user_id" not in session:
        return redirect("/login")

    conn = db()
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
    user = c.fetchone()

    resetar(user)

    limite = 2 if user[4] == "free" else 999

    return render_template("dashboard.html",
        login=user[1],
        plano=user[4],
        usados=user[5],
        limite=limite
    )

# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        login = request.form["login"]
        email = request.form["email"]
        senha = generate_password_hash(request.form["senha"])

        conn = db()
        c = conn.cursor()

        try:
            reset = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

            c.execute("""
            INSERT INTO users (login, email, senha, plano, downloads, reset_date)
            VALUES (?, ?, ?, 'free', 0, ?)
            """, (login, email, senha, reset))

            conn.commit()
            return redirect("/login")

        except:
            return "❌ Login já existe!"

        finally:
            conn.close()

    return render_template("register.html")

# ================= LOGIN =================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        login = request.form["login"]
        senha = request.form["senha"]

        conn = db()
        c = conn.cursor()

        c.execute("SELECT * FROM users WHERE login = ?", (login,))
        user = c.fetchone()

        conn.close()

        if user and check_password_hash(user[3], senha):
            session["user_id"] = user[0]
            return redirect("/")

        return "❌ Login inválido"

    return render_template("login.html")

# ================= DOWNLOAD =================
@app.route("/baixar")
def baixar():
    if "user_id" not in session:
        return redirect("/login")

    conn = db()
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE id = ?", (session["user_id"],))
    user = c.fetchone()

    resetar(user)

    limite = 2 if user[4] == "free" else 999

    if user[5] >= limite:
        return "🚫 Limite do plano FREE atingido!"

    c.execute("""
    UPDATE users SET downloads = downloads + 1 WHERE id = ?
    """, (user[0],))

    conn.commit()
    conn.close()

    return "✅ Download liberado!"

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)