import yt_dlp
import os
import uuid
from config import DOWNLOAD_DIR

def download_media(url, action):
    file_id = str(uuid.uuid4())
    out = f"{DOWNLOAD_DIR}/{file_id}.%(ext)s"
    
    ydl_opts = {'outtmpl': out, 'quiet': True, 'nocheckcertificate': True, 'noplaylist': True}
    
    if action == 'dl_vid':
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    else:
        ydl_opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]})

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if action == 'dl_aud': file_path = os.path.splitext(file_path)[0] + '.mp3'
        return file_path if os.path.exists(file_path) else None
    except:
        return None
