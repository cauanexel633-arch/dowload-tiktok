import requests
import random
import os

PASTA = "downloads"
USADOS = "usados.txt"

os.makedirs(PASTA, exist_ok=True)

if not os.path.exists(USADOS):
    open(USADOS, "w").close()


def ja_usado(link):
    with open(USADOS, "r") as f:
        return link in f.read()


def salvar(link):
    with open(USADOS, "a") as f:
        f.write(link + "\n")


def baixar_video(url, nome):
    try:
        caminho = os.path.join(PASTA, f"{nome}_{random.randint(1000,9999)}.mp4")

        headers = {
            "User-Agent": "Mozilla/5.0"
        }

        r = requests.get(url, headers=headers, stream=True)

        if r.status_code != 200:
            return None

        with open(caminho, "wb") as f:
            for chunk in r.iter_content(1024):
                if chunk:
                    f.write(chunk)

        return caminho

    except:
        return None


# 🔥 SIMULA BUSCA (TikTok bloqueia scraping fácil)
def buscar_videos_fake(produto):
    base = "https://sample-videos.com/video123/mp4/720/"
    return [
        base + "big_buck_bunny_720p_1mb.mp4",
        base + "big_buck_bunny_720p_1mb.mp4"
    ]