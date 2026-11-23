import os

TOKEN = os.environ.get('BOT_TOKEN')
OWNER_ID = int(os.environ.get('ADMIN_ID', 0))
BOT_USERNAME = os.environ.get('BOT_USERNAME', 'turkidownloads_bot')

DOWNLOAD_DIR = 'downloads'
COOLDOWN = 10
