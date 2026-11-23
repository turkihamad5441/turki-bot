import sqlite3

def init_db():
    conn = sqlite3.connect('turki_bot.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, coins INTEGER, vip_expiry REAL, 
                 role TEXT DEFAULT 'user', is_banned INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS promos (code TEXT PRIMARY KEY, reward INTEGER, max_uses INTEGER, current_uses INTEGER)''')
    
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('price', '5')")
    conn.commit(); conn.close()

def get_user(user_id):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone(); conn.close()
    return user

def add_user(user_id, username, role='user'):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, username, coins, role) VALUES (?, ?, 30, ?)", (user_id, username, role))
    conn.commit(); conn.close()

def update_user(user_id, field, value):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
    conn.commit(); conn.close()

def get_all_users():
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE is_banned = 0")
    users = c.fetchall(); conn.close()
    return [u[0] for u in users]

def get_price():
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = 'price'")
    price = c.fetchone()[0]; conn.close()
    return int(price)

def set_price(new_price):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("UPDATE settings SET value = ? WHERE key = 'price'", (new_price,))
    conn.commit(); conn.close()

def create_promo(code, reward, max_uses):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    try:
        c.execute("INSERT INTO promos (code, reward, max_uses, current_uses) VALUES (?, ?, ?, 0)", (code.upper(), reward, max_uses))
        conn.commit(); conn.close()
        return True
    except:
        conn.close()
        return False

def use_promo(user_id, code):
    conn = sqlite3.connect('turki_bot.db'); c = conn.cursor()
    c.execute("SELECT reward, max_uses, current_uses FROM promos WHERE code = ?", (code.upper(),))
    promo = c.fetchone()
    if promo and promo[2] < promo[1]:
        c.execute("UPDATE promos SET current_uses = current_uses + 1 WHERE code = ?", (code.upper(),))
        c.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (promo[0], user_id))
        conn.commit(); conn.close()
        return promo[0]
    conn.close()
    return None

init_db()
