# ia_episodios.py
import os
import json
import time
from typing import Dict, Any

import requests
from dotenv import load_dotenv

# ==========================================
# CONFIG BÁSICA / AMBIENTE
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

DEBUG_IA_EP = True

DATA_DIR = os.path.join(BASE_DIR, "data")
DESCRIPTIONS_FILE = os.path.join(DATA_DIR, "descriptions.json")


def _debug(msg: str):
    if DEBUG_IA_EP:
        print(f"[IA_EP_DEBUG] {msg}")


# ==========================================
# CACHE LOCAL
# ==========================================

def _load_cache() -> Dict[str, Any]:
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(DESCRIPTIONS_FILE):
        return {}
    try:
        with open(DESCRIPTIONS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        _debug(f"Erro ao carregar cache: {e}")
        return {}


def _save_cache(cache: Dict[str, Any]) -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(DESCRIPTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


# ==========================================
# FALLBACK
# ==========================================

def _fallback_descricao(serie: str, temporada: str, numero: int, filename: str) -> str:
    titulo = filename.rsplit(".", 1)[0]
    return f"Episódio {numero} da série {serie}: \"{titulo}\"."


def _is_fallback(desc: str, serie: str, temporada: str, numero: int, filename: str) -> bool:
    """
    Verifica se o texto é o fallback gerado por _fallback_descricao.
    Assim a gente sabe se deve ou não salvar no cache.
    """
    expected_prefix = f"Episódio {numero} da série {serie}:"
    return desc.startswith(expected_prefix)


# ==========================================
# IA COM CACHE
# ==========================================

def gerar_descricao_episodio(serie: str, temporada: str, numero: int, filename: str) -> str:
    """
    Busca no cache. Se não tiver, tenta gerar via Gemini.
    Se falhar, usa fallback, mas NÃO salva fallback no cache.
    Assim, em uma próxima vez ele tenta gerar pela IA novamente.
    """
    cache = _load_cache()

    serie_key = serie
    temporada_key = temporada
    numero_key = str(numero)

    # 1 — Se já existe no cache
    if (
        serie_key in cache
        and temporada_key in cache[serie_key]
        and numero_key in cache[serie_key][temporada_key]
    ):
        return cache[serie_key][temporada_key][numero_key]

    # 2 — Se não existe → tentar gerar
    if not GEMINI_API_KEY:
        _debug("Sem GEMINI_API_KEY, usando fallback (sem salvar no cache).")
        desc = _fallback_descricao(serie, temporada, numero, filename)
    else:
        desc = _gerar_via_ia(serie, temporada, numero, filename)

    # 3 — Salvar NO CACHE só se NÃO for fallback
    if not _is_fallback(desc, serie, temporada, numero, filename):
        cache.setdefault(serie_key, {})
        cache[serie_key].setdefault(temporada_key, {})
        cache[serie_key][temporada_key][numero_key] = desc
        _save_cache(cache)
        _debug("Descrição real da IA salva no cache.")
    else:
        _debug("Fallback detectado — NÃO será salvo no cache.")

    return desc


# ==========================================
# CHAMADA À IA COM RETRY / BACKOFF
# ==========================================

def _gerar_via_ia(serie: str, temporada: str, numero: int, filename: str) -> str:
    titulo = filename.rsplit(".", 1)[0]

    prompt = f"""
Gere uma descrição curta (até 2 frases) para um episódio:

Série: {serie}
Temporada: {temporada}
Episódio: {numero}
Título: "{titulo}"

Regras:
- Responda em português.
- Estilo de catálogo Netflix.
- No máximo 2 frases.
"""

    url = f"{GEMINI_BASE_URL}/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    payload: Dict[str, Any] = {"contents": [{"parts": [{"text": prompt}]}]}

    max_tentativas = 5
    espera = 1  # segundos, com backoff exponencial

    for tentativa in range(1, max_tentativas + 1):
        try:
            _debug(f"Tentativa {tentativa}/{max_tentativas} para gerar descrição...")

            resp = requests.post(url, json=payload, timeout=20)

            # Se for erro de QUOTA / RATE LIMIT (429), espera e tenta de novo
            if resp.status_code == 429:
                _debug("Erro 429 (quota/rate limit) — aguardando para tentar novamente...")
                time.sleep(espera)
                espera = min(espera * 2, 30)  # evita explodir o tempo
                continue

            # Outros erros HTTP
            resp.raise_for_status()
            data = resp.json()

            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
                .strip()
            )

            if text:
                _debug("Descrição gerada com sucesso pela IA.")
                return text

            # Resposta vazia → tenta de novo
            _debug("Resposta vazia da IA — tentando novamente...")
            time.sleep(espera)
            espera = min(espera * 2, 30)
            continue

        except Exception as e:
            _debug(f"Erro ao chamar Gemini: {e} — tentando novamente em {espera} segundos...")
            time.sleep(espera)
            espera = min(espera * 2, 30)

    # Se todas tentativas falharem, usa fallback
    _debug("Todas as tentativas falharam — usando fallback (NÃO será salvo no cache).")
    return _fallback_descricao(serie, temporada, numero, filename)
