from flask import Flask, render_template, request, redirect, session, send_file
from supabase import create_client
from werkzeug.security import generate_password_hash, check_password_hash
import requests, os, uuid

app = Flask(__name__)
app.secret_key = "segredo123"

# ================= SUPABASE =================
SUPABASE_URL = "https://sijudfgbumzaczlcsnac.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InNpanVkZmdidW16YWN6bGNzbmFjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwNjk3ODAsImV4cCI6MjA5MTY0NTc4MH0.08XVFqBE_SvbiNeLYLsUHd6xKa8xkDssbFjoKE0oYtI"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ================= ROTAS =================
@app.route("/")
def home():
    return render_template("login.html")

@app.route("/register_page")
def register_page():
    return render_template("register.html")

# ================= REGISTER =================
@app.route("/register", methods=["POST"])
def register():
    user = request.form["user"]
    email = request.form["email"]
    senha = request.form["senha"]

    # verifica se já existe usuário
    check = supabase.table("users").select("*").eq("username", user).execute()

    if check.data:
        return "❌ Usuário já existe!"

    senha_hash = generate_password_hash(senha)

    supabase.table("users").insert({
        "username": user,
        "email": email,
        "password": senha_hash
    }).execute()

    return redirect("/")

# ================= LOGIN =================
@app.route("/login", methods=["POST"])
def login():
    user = request.form["user"]
    senha = request.form["senha"]

    res = supabase.table("users").select("*").eq("username", user).execute()

    if res.data:
        user_db = res.data[0]

        if check_password_hash(user_db["password"], senha):
            session["user"] = user
            return redirect("/dashboard")

    return "❌ Login inválido"

# ================= DASHBOARD =================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")
    return render_template("dashboard.html", user=session["user"])

# ================= CONTAS =================
@app.route("/contas")
def contas():
    if "user" not in session:
        return redirect("/")

    res = supabase.table("users").select("username").execute()
    return render_template("contas.html", contas=res.data)

@app.route("/trocar_conta/<user>")
def trocar_conta(user):
    session["user"] = user
    return redirect("/dashboard")

# ================= DOWNLOAD =================
def baixar_video(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(url, headers=headers, stream=True, timeout=15)

        if r.status_code != 200:
            return None

        os.makedirs("downloads", exist_ok=True)

        nome = f"video_{uuid.uuid4().hex}.mp4"
        caminho = f"downloads/{nome}"

        with open(caminho, "wb") as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

        return caminho

    except:
        return None

@app.route("/baixar", methods=["POST"])
def baixar():
    if "user" not in session:
        return redirect("/")

    link = request.form["link"]
    caminho = baixar_video(link)

    if not caminho:
        return "❌ Erro ao baixar vídeo"

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