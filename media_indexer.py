# media_indexer.py
import os
import re

VIDEO_EXTS = (".mp4", ".mkv", ".avi", ".mov", ".wmv")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def _find_thumb_for_video(folder_path: str, video_name: str, serie_name: str, season_name: str | None):
    """
    Procura uma imagem com o mesmo nome do vídeo (ex: S01E01.jpg).
    Retorna o caminho relativo para usar na rota /media.
    """
    stem, _ = os.path.splitext(video_name)

    for ext in IMAGE_EXTS:
        cand = stem + ext
        cand_full = os.path.join(folder_path, cand)
        if os.path.exists(cand_full):
            if season_name:
                return f"{serie_name}/{season_name}/{cand}"
            else:
                return f"{serie_name}/{cand}"
    return None


def extract_number(text: str) -> int:
    """
    Extrai o primeiro número encontrado no texto para usar como chave de ordenação.
    Se não tiver número, devolve 9999 (vai pro final).
    """
    nums = re.findall(r"\d+", text)
    return int(nums[0]) if nums else 9999


def get_series_library(media_root: str):
    """
    Estrutura:
    {
      "Nome da Série": {
          "poster": "Nome da Série/poster.jpg" ou None,
          "seasons": [
              {
                  "name": "Temporada 01",
                  "episodes": [
                      {
                        "filename": "S01E01 - Piloto.mp4",
                        "relative_path": "Nome da Série/Temporada 01/S01E01 - Piloto.mp4",
                        "thumb": "Nome da Série/Temporada 01/S01E01 - Piloto.jpg" ou None
                      },
                      ...
                  ]
              },
              ...
          ]
      },
      ...
    }
    """
    library = {}

    if not os.path.exists(media_root):
        return library

    for serie_name in sorted(os.listdir(media_root)):
        serie_path = os.path.join(media_root, serie_name)
        if not os.path.isdir(serie_path):
            continue

        # Poster da série
        poster = None
        for file in os.listdir(serie_path):
            lower = file.lower()
            if lower.startswith("poster") and lower.endswith(IMAGE_EXTS):
                poster = f"{serie_name}/{file}"
                break

        seasons = []
        season_dirs = []
        loose_episodes = []

        # Pastas = temporadas, vídeos soltos = "Episódios"
        for entry in os.listdir(serie_path):
            full = os.path.join(serie_path, entry)
            if os.path.isdir(full):
                season_dirs.append(entry)
            elif entry.lower().endswith(VIDEO_EXTS):
                loose_episodes.append(entry)

        # Temporadas em subpastas (ordenadas por número)
        for sd in sorted(season_dirs, key=extract_number):

            season_path = os.path.join(serie_path, sd)
            eps = []

            # Episódios ordenados por número
            for fname in sorted(os.listdir(season_path), key=extract_number):
                if not fname.lower().endswith(VIDEO_EXTS):
                    continue

                rel_path = f"{serie_name}/{sd}/{fname}"
                thumb = _find_thumb_for_video(season_path, fname, serie_name, sd)

                eps.append({
                    "filename": fname,
                    "relative_path": rel_path,
                    "thumb": thumb
                })

            if eps:
                seasons.append({
                    "name": sd,
                    "episodes": eps
                })

        # Episódios soltos (temporada "Episódios")
        if loose_episodes:
            eps = []
            for f in sorted(loose_episodes, key=extract_number):
                rel_path = f"{serie_name}/{f}"
                thumb = _find_thumb_for_video(serie_path, f, serie_name, None)

                eps.append({
                    "filename": f,
                    "relative_path": rel_path,
                    "thumb": thumb
                })

            seasons.insert(0, {
                "name": "Episódios",
                "episodes": eps
            })

        if seasons:
            library[serie_name] = {
                "poster": poster,
                "seasons": seasons
            }

    return library


def get_series_cards(library: dict):
    cards = []
    for name, data in library.items():
        cards.append({
            "name": name,
            "poster": data.get("poster")
        })
    cards.sort(key=lambda x: x["name"])
    return cards


def find_episode_info(library: dict, relative_path: str):
    """
    Encontra informações sobre um episódio a partir do caminho relativo.

    Retorna:
      {
        "serie_name": str,
        "episode_name": str,
        "season_name": str,
        "episode_index": int  # 1-based dentro da temporada
      }
    """
    rel_norm = relative_path.replace("\\", "/")

    for serie_name, data in library.items():
        for season in data.get("seasons", []):
            season_name = season.get("name", "")
            episodes = season.get("episodes", [])
            for idx, ep in enumerate(episodes):
                if ep["relative_path"] == rel_norm:
                    return {
                        "serie_name": serie_name,
                        "episode_name": ep["filename"],
                        "season_name": season_name,
                        "episode_index": idx + 1,
                    }

    return None
