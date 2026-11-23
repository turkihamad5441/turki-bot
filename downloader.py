import yt_dlp
import os
import uuid
from config import DOWNLOAD_DIR

def download_media(url, action):
    file_id = str(uuid.uuid4())
    out = f"{DOWNLOAD_DIR}/{file_id}.%(ext)s"
    
    # إعدادات سحرية لسحب الفيديو الأصلي (بدون علامة مائية) وتخطي الحظر
    ydl_opts = {
        'outtmpl': out, 
        'quiet': True, 
        'nocheckcertificate': True, 
        'noplaylist': True,
        'geo_bypass': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    if action == 'dl_vid':
        ydl_opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
    else:
        ydl_opts.update({
            'format': 'bestaudio/best', 
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}]
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            # تعديل الامتداد في حال كان صوت
            if action == 'dl_aud': 
                file_path = os.path.splitext(file_path)[0] + '.mp3'
                
        return file_path if os.path.exists(file_path) else None
    except Exception as e:
        print(f"Download Error: {e}")
        return None
