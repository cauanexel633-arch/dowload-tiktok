from flask import Flask, render_template, request, redirect, session, url_for, send_file
import requests
import os
from supabase import create_client

app = Flask(__name__)
app.secret_key = "segredo123"

# ================= SUPABASE =================
SUPABASE_URL = "https://sijudfgbumzaczlcsnac.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNpanVkZmdidW16YWN6bGNzbmFjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NjA2OTc4MCwiZXhwIjoyMDkxNjQ1NzgwfQ.8O8ZDztZNHVQc_m0kt7nQv5i0yvTwfUzFrQp_vzrWsU"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= HOME =================
@app.route("/")
def home():
    return redirect(url_for("login"))

# ================= REGISTER =================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        senha = request.form.get("senha")

        if not username or not senha:
            return render_template("register.html", erro="Preencha tudo")

        check = supabase.table("users").select("*").eq("username", username).execute()

        if check.data:
            return render_template("register.html", erro="Usuário já existe")

        supabase.table("users").insert({
            "username": username,
            "senha": senha
        }).execute()

        return redirect(url_for("login"))

    return render_template("register.html")

# ================= LOGIN =================
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

        return render_template("login.html", erro="Login inválido")

    return render_template("login.html")

# ================= DASHBOARD =================
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    video_url = None
    erro = None

    if request.method == "POST":
        link = request.form.get("link")

        try:
            api = f"https://www.tikwm.com/api/?url={link}"
            response = requests.get(api)
            data = response.json()

            video_url = data.get("data", {}).get("play")

            if not video_url:
                raise Exception("Sem vídeo")

            # salvar histórico
            supabase.table("downloads").insert({
                "username": session["user"],
                "link": link
            }).execute()

        except Exception as e:
            print("ERRO API:", e)
            erro = "Link inválido ou vídeo não encontrado"

    # histórico
    try:
        historico = supabase.table("downloads")\
            .select("*")\
            .eq("username", session["user"])\
            .execute().data
    except:
        historico = []

    return render_template("dashboard.html",
                           video_url=video_url,
                           erro=erro,
                           historico=historico)

# ================= DOWNLOAD =================
@app.route("/download", methods=["POST"])
def download():
    if "user" not in session:
        return redirect(url_for("login"))

    video_url = request.form.get("video_url")

    try:
        r = requests.get(video_url)

        with open("video.mp4", "wb") as f:
            f.write(r.content)

        return send_file("video.mp4", as_attachment=True, mimetype="video/mp4")

    except Exception as e:
        print("ERRO DOWNLOAD:", e)
        return "Erro ao baixar vídeo"

# ================= LOGOUT =================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ================= RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
