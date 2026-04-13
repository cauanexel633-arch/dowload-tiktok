from flask import Flask, render_template, request, redirect, session, send_file
import requests
import re
import os
from supabase import create_client

app = Flask(__name__)
app.secret_key = "segredo123"

# ================= SUPABASE =================
SUPABASE_URL = "https://sijudfgbumzaczlcsnac.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNpanVkZmdidW16YWN6bGNzbmFjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjA2OTc4MCwiZXhwIjoyMDkxNjQ1NzgwfQ.8O8ZDztZNHVQc_m0kt7nQv5i0yvTwfUzFrQp_vzrWsU"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= LOGIN =================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form["user"]
        senha = request.form["senha"]

        res = supabase.table("users").select("*").eq("user", user).eq("senha", senha).execute()

        if res.data:
            session["user"] = user
            return redirect("/dashboard")

        return render_template("login.html", erro="Usuário inválido")

    return render_template("login.html")


# ================= REGISTRO =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = request.form["user"]
        senha = request.form["senha"]

        supabase.table("users").insert({
            "user": user,
            "senha": senha
        }).execute()

        return redirect("/")

    return render_template("register.html")


# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html")


# ================= PEGAR VIDEO =================
def pegar_video_url(link):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(link, headers=headers)
        html = r.text

        match = re.search(r'"playAddr":"(https:[^"]+)"', html)

        if match:
            return match.group(1).replace("\\u0026", "&").replace("\\u002F", "/")

        return None
    except:
        return None


# ================= PREVIEW =================
@app.route("/preview", methods=["POST"])
def preview():
    link = request.form.get("link")
    video_url = pegar_video_url(link)

    if not video_url:
        return render_template("dashboard.html", erro="❌ Vídeo não encontrado")

    return render_template("dashboard.html", video_url=video_url)


# ================= DOWNLOAD =================
@app.route("/download", methods=["POST"])
def download():
    video_url = request.form.get("video_url")

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.tiktok.com/"
    }

    r = requests.get(video_url, headers=headers, stream=True)

    caminho = "video.mp4"

    with open(caminho, "wb") as f:
        for chunk in r.iter_content(1024 * 1024):
            if chunk:
                f.write(chunk)

    return send_file(caminho, as_attachment=True)


# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)