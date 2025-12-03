import os
import subprocess

# ajuste para a pasta onde estão suas séries
MEDIA_ROOT = r"E:\metflix\media"

VIDEO_EXTS = (".mp4", ".mkv", ".avi", ".mov", ".wmv")
IMAGE_EXTS = (".jpg", ".jpeg", ".png", ".webp")


def has_thumb(video_path: str) -> bool:
    """Verifica se já existe uma imagem com o mesmo nome do vídeo."""
    stem, _ = os.path.splitext(video_path)
    for ext in IMAGE_EXTS:
        if os.path.exists(stem + ext):
            return True
    return False


def make_thumb(video_path: str):
    """Gera um frame do vídeo e salva como JPG ao lado do arquivo."""
    stem, _ = os.path.splitext(video_path)
    thumb_path = stem + ".jpg"

    # -ss: tempo do frame (aqui 10 segundos, pode ajustar)
    # -frames:v 1: só 1 frame
    # -qscale:v 3: qualidade boa (1–5, quanto menor melhor)
    cmd = [
        "ffmpeg",
        "-y",
        "-ss", "00:00:10",
        "-i", video_path,
        "-frames:v", "1",
        "-qscale:v", "3",
        thumb_path,
    ]

    print(f"Gerando thumb para: {video_path}")
    subprocess.run(cmd, check=True)


def main():
    for root, dirs, files in os.walk(MEDIA_ROOT):
        for name in files:
            if not name.lower().endswith(VIDEO_EXTS):
                continue

            video_path = os.path.join(root, name)

            if has_thumb(video_path):
                # já tem thumb, pula
                continue

            try:
                make_thumb(video_path)
            except subprocess.CalledProcessError as e:
                print(f"Erro ao gerar thumb para {video_path}: {e}")


if __name__ == "__main__":
    main()
