# app.py
from flask import Flask, render_template, send_from_directory, abort
from config import MEDIA_ROOT, PROGRESS_FILE
from media_indexer import get_series_library, get_series_cards, find_episode_info
import os
import json
from datetime import datetime
from config import MEDIA_ROOT, PROGRESS_FILE
from media_indexer import get_series_library, get_series_cards, find_episode_info
import os
import json
from datetime import datetime


app = Flask(__name__)


# ======================
# Helpers de progresso
# ======================

def get_next_episode(library, serie_name, relative_path):
    """
    Acha o próximo episódio na mesma temporada.
    Se acabar a temporada, pega o primeiro da próxima.
    """
    serie = library.get(serie_name)
    if not serie:
        return None

    seasons = serie["seasons"]

    # localização do episódio atual
    found = False
    for si, season in enumerate(seasons):
        for ei, ep in enumerate(season["episodes"]):
            if ep["relative_path"] == relative_path:
                found = True

                # tenta próximo da mesma temporada
                if ei + 1 < len(season["episodes"]):
                    return season["episodes"][ei + 1]["relative_path"]

                # senão tenta próxima temporada
                if si + 1 < len(seasons):
                    next_season = seasons[si + 1]
                    if next_season["episodes"]:
                        return next_season["episodes"][0]["relative_path"]

    return None

def load_progress():
    if not os.path.exists(PROGRESS_FILE):
        return {}
    try:
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_progress(progress: dict):
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def build_continue_list(library: dict):
    """
    Monta a lista para a seção "Continuar assistindo".
    Pega do arquivo de progresso e junta com posters.
    """
    progress = load_progress()
    items = []

    # Mapa série -> poster
    poster_lookup = {}
    for serie_name, data in library.items():
        poster_lookup[serie_name] = data.get("poster")

    for rel_path, meta in progress.items():
        serie_name = meta.get("serie_name", "")
        episode_name = meta.get("episode_name", os.path.basename(rel_path))
        last_watched = meta.get("last_watched", "")

        items.append({
            "relative_path": rel_path,
            "serie_name": serie_name,
            "episode_name": episode_name,
            "poster": poster_lookup.get(serie_name),
            "last_watched": last_watched
        })

    # Ordena por último assistido (mais recente primeiro)
    items.sort(key=lambda x: x["last_watched"], reverse=True)

    # Opcional: manter só 1 por série
    unique = []
    seen_series = set()
    for item in items:
        if item["serie_name"] in seen_series:
            continue
        seen_series.add(item["serie_name"])
        unique.append(item)

    return unique


# ======================
# Rotas
# ======================

@app.route("/")
def index():
    library = get_series_library(MEDIA_ROOT)
    series_cards = get_series_cards(library)
    continue_list = build_continue_list(library)

    return render_template(
        "index.html",
        series_cards=series_cards,
        continue_list=continue_list
    )


@app.route("/serie/<serie_name>")
def serie_detail(serie_name):
    library = get_series_library(MEDIA_ROOT)
    serie = library.get(serie_name)
    if not serie:
        abort(404)

    poster = serie.get("poster")
    seasons = serie.get("seasons", [])

    # Descobre qual foi o último episódio assistido dessa série
    progress = load_progress()
    last_watched_path = None
    last_time = None

    for rel_path, meta in progress.items():
        if meta.get("serie_name") == serie_name:
            ts = meta.get("last_watched")
            if last_time is None or ts > last_time:
                last_time = ts
                last_watched_path = rel_path

    prepared_seasons = []
    for season in seasons:
        prepared_seasons.append({
            "name": season.get("name"),
            "episodes": season.get("episodes", [])
        })

    return render_template(
        "serie.html",
        serie_name=serie_name,
        poster=poster,
        seasons=prepared_seasons,
        last_watched_path=last_watched_path
    )


from datetime import datetime  # garante que isso está no topo do arquivo

@app.route("/watch/<path:relative_path>")
def watch(relative_path):
    # Normaliza as barras
    rel_norm = relative_path.replace("\\", "/")

    # Descobre série e nome do episódio
    library = get_series_library(MEDIA_ROOT)
    info = find_episode_info(library, rel_norm)

    if not info:
        abort(404)

    serie_name = info["serie_name"]
    episode_name = info["episode_name"]

    # Atualiza progresso para "continuar assistindo"
    progress = load_progress()
    progress[rel_norm] = {
        "serie_name": serie_name,
        "episode_name": episode_name,
        "last_watched": datetime.now().isoformat()
    }
    save_progress(progress)

    # Descobre o próximo episódio (mesma temporada ou próxima)
    next_episode = get_next_episode(library, serie_name, rel_norm)

    return render_template(
        "watch.html",
        relative_path=rel_norm,
        episode_name=episode_name,
        serie_name=serie_name,
        next_episode=next_episode
    )


@app.route("/stream/<path:relative_path>")
def stream(relative_path):
    dir_name = os.path.dirname(relative_path)
    file_name = os.path.basename(relative_path)
    video_dir = os.path.join(MEDIA_ROOT, dir_name)

    file_path = os.path.join(video_dir, file_name)
    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(video_dir, file_name, as_attachment=False)


@app.route("/media/<path:relative_path>")
def media_file(relative_path):
    """
    Serve imagens (poster.jpg etc.) que estão dentro da pasta media/.
    """
    dir_name = os.path.dirname(relative_path)
    file_name = os.path.basename(relative_path)
    base_dir = os.path.join(MEDIA_ROOT, dir_name)

    file_path = os.path.join(base_dir, file_name)
    if not os.path.exists(file_path):
        abort(404)

    return send_from_directory(base_dir, file_name, as_attachment=False)


if __name__ == "__main__":
    # host=0.0.0.0 para acessar de celular/TV na mesma rede
    app.run(debug=True, host="0.0.0.0")
