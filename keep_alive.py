from flask import Flask, render_template_string
from threading import Thread
import os

app = Flask('')

HTML_PAGE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تركي للتنزيلات</title>
    <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Cairo', sans-serif; }
        body { background-color: #0f172a; color: #fff; text-align: center; padding: 20px; }
        .container { max-width: 600px; margin: 0 auto; background: #1e293b; border-radius: 20px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); border: 1px solid #334155; }
        h1 { font-size: 32px; font-weight: 900; background: linear-gradient(90deg, #8b5cf6, #3b82f6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 15px; }
        p { font-size: 16px; color: #94a3b8; margin-bottom: 30px; line-height: 1.6; }
        .btn { display: inline-block; width: 100%; padding: 15px; background: linear-gradient(90deg, #8b5cf6, #3b82f6); color: #fff; text-decoration: none; font-weight: bold; font-size: 18px; border-radius: 12px; transition: 0.3s; box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4); }
        .btn:hover { transform: translateY(-3px); }
    </style>
</head>
<body>
    <div class="container">
        <h1>تركي للتنزيلات 🎬</h1>
        <p>البوت الأسرع والأقوى لتنزيل الفيديوهات بدون علامة مائية، مع محادثة ذكية وأذكار تلقائية.</p>
        <a href="https://t.me/turkidownloads_bot" class="btn" target="_blank">ابدأ استخدام البوت الآن 🚀</a>
    </div>
</body>
</html>
"""

@app.route('/')
def home(): return render_template_string(HTML_PAGE)

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

def keep_alive():
    t = Thread(target=run)
    t.start()
