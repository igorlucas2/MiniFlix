import os
import subprocess

# 👇 Ajusta esse caminho para a pasta da temporada que você quer converter
input_folder = "media/Quarteto Fantástico Primeiros Passos"

FFMPEG_EXE = r"C:\ffmpeg\bin\ffmpeg.exe"
 # se não estiver no PATH, pode por o caminho completo aqui

# Extensões de vídeo que serão convertidas
VIDEO_EXTS = (".mkv", ".avi", ".mov", ".wmv", ".mpg", ".mpeg")

for file in os.listdir(input_folder):
    if file.lower().endswith(VIDEO_EXTS):
        mkv_path = os.path.join(input_folder, file)
        mp4_path = os.path.splitext(mkv_path)[0] + ".mp4"

        cmd = [
            FFMPEG_EXE,
            "-i", mkv_path,
            "-c:v", "copy",
            "-c:a", "aac",
            "-movflags", "+faststart",
            mp4_path,
        ]

        print("Convertendo:", mkv_path)
        print("Comando:", " ".join(cmd))

        # check=True faz o Python estourar erro se a conversão falhar
        subprocess.run(cmd, check=True)

print("✅ Conversão finalizada!")
