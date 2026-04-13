from flask import Flask, render_template, request, redirect, session, url_for, send_file
import requests
import os
from supabase import create_client

app = Flask(__name__)
app.secret_key = "segredo123"

# 🔗 SUPABASE
SUPABASE_URL = "https://sijudfgbumzaczlcsnac.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNpanVkZmdidW16YWN6bGNzbmFjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjA2OTc4MCwiZXhwIjoyMDkxNjQ1NzgwfQ.8O8ZDztZNHVQc_m0kt7nQv5i0yvTwfUzFrQp_vzrWsU"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================
# HOME
# =========================
@app.route("/")
def home():
    return redirect(url_for("login"))

# =========================
# REGISTER
# =========================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        senha = request.form.get("senha")

        if not username or not senha:
            return "Preencha tudo!"

        supabase.table("users").insert({
            "username": username,
            "senha": senha
        }).execute()

        return redirect(url_for("login"))

    return render_template("register.html")

# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        senha = request.form.get("senha")

        res = supabase.table("users")\
            .select("*")\
            .eq("username", username)\
            .eq("senha", senha)\
            .execute()

        if res.data:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", erro="Usuário inválido!")

    return render_template("login.html")

# =========================
# DASHBOARD
# =========================
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    video_url = None

    if request.method == "POST":
        link = request.form.get("link")

        try:
            api = f"https://api.tiklydown.eu.org/api/download?url={link}"
            r = requests.get(api).json()

            video_url = r["video"]["noWatermark"]

        except:
            return "Erro ao carregar vídeo!"

    return render_template("dashboard.html", video_url=video_url)

# =========================
# DOWNLOAD
# =========================
@app.route("/download", methods=["POST"])
def download():
    link = request.form.get("link")

    try:
        file = requests.get(link)

        with open("video.mp4", "wb") as f:
            f.write(file.content)

        return send_file("video.mp4", as_attachment=True)

    except:
        return "Erro ao baixar vídeo!"

# =========================
# CONTAS (NOVO)
# =========================
@app.route("/contas")
def contas():
    if "user" not in session:
        return redirect(url_for("login"))

    return render_template("contas.html")

# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# =========================
# RUN
# =========================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)