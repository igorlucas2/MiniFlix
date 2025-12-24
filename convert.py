import os
import json
import subprocess

input_folder = "media/Fullmetal Alchemist Brotherhood/temporada 1"

FFMPEG_EXE = r"C:\ffmpeg\bin\ffmpeg.exe"
FFPROBE_EXE = r"C:\ffmpeg\bin\ffprobe.exe"

VIDEO_EXTS = (".mkv", ".avi", ".mov", ".wmv", ".mpg", ".mpeg")

# idiomas que vamos aceitar como "português"
PT_LANGS = {"por", "pt", "pt-br", "pob", "pb", "ptbr"}

def ffprobe_streams(path: str) -> dict:
    """Retorna JSON do ffprobe com streams."""
    cmd = [
        FFPROBE_EXE,
        "-v", "error",
        "-show_streams",
        "-of", "json",
        path
    ]
    out = subprocess.check_output(cmd, text=True, encoding="utf-8", errors="replace")
    return json.loads(out)

def pick_portuguese_audio_index(info: dict) -> int | None:
    """Escolhe índice do áudio em português (0:a:<index>), se existir."""
    streams = info.get("streams", [])
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]

    for i, s in enumerate(audio_streams):
        tags = s.get("tags") or {}
        lang = (tags.get("language") or "").strip().lower()
        title = (tags.get("title") or "").strip().lower()

        if lang in PT_LANGS:
            return i

        # fallback por título (às vezes vem "Portuguese", "PT-BR", "Brazilian Portuguese")
        if "portugu" in title or "pt-br" in title or "pt br" in title or "brazil" in title:
            return i

    return None

def has_any_audio(info: dict) -> bool:
    streams = info.get("streams", [])
    return any(s.get("codec_type") == "audio" for s in streams)

for file in os.listdir(input_folder):
    if not file.lower().endswith(VIDEO_EXTS):
        continue

    input_path = os.path.join(input_folder, file)
    output_path = os.path.splitext(input_path)[0] + ".mp4"

    print("\n🎬 Arquivo:", file)

    info = ffprobe_streams(input_path)

    if not has_any_audio(info):
        print("⚠️ Nenhum áudio encontrado. Pulando:", file)
        continue

    pt_audio_idx = pick_portuguese_audio_index(info)

    if pt_audio_idx is not None:
        audio_map = f"0:a:{pt_audio_idx}"
        print(f"✅ Áudio PT detectado: {audio_map}")
    else:
        audio_map = "0:a:0"
        print("⚠️ Áudio PT não encontrado (ou não marcado). Usando primeiro áudio: 0:a:0")

    cmd = [
        FFMPEG_EXE,
        "-y",
        "-i", input_path,

        "-map", "0:v:0",
        "-map", audio_map,

        "-c:v", "copy",
        "-c:a", "aac",
        "-ac", "2",
        "-movflags", "+faststart",

        output_path
    ]

    print("➡️ Comando:", " ".join(cmd))
    subprocess.run(cmd, check=True)

print("\n✅ Conversão finalizada!")
