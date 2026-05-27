"""
THE TAMERS USERBOT v2.1 - RAILWAY PROOF EDITION
No Memory Leak | No Crash | Auto Restart Protection
"""

import sys
import warnings
import logging
import asyncio
import random
import json
import os
import time
import signal
from datetime import datetime
from flask import Flask

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked
from pyrogram.types import Message
from pyrogram.enums import ChatType

# ========================== MATIKAN SEMUA LOG ==========================
warnings.filterwarnings("ignore")
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("werkzeug").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("urllib3").setLevel(logging.ERROR)

# ========================== BACA ENV ==========================
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

if not API_ID or not API_HASH or not SESSION_STRING:
    print("🩸 ERROR: API_ID, API_HASH, SESSION_STRING harus di set di Railway Env!")
    sys.exit(1)

# ========================== KONFIGURASI ==========================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

BLACKLIST_FILE = f"{DATA_DIR}/blacklist.json"
WHITELIST_FILE = f"{DATA_DIR}/whitelist.json"
GBAN_FILE = f"{DATA_DIR}/gban.json"

BOT_START = time.time()
BRAND = "THE TAMERS"
VERSION = "2.1.0"

# ========================== DATA GLOBAL ==========================
blacklist = set()
whitelist = set()
gban = set()
afk_mode = False
afk_pending = {}
afk_approved = set()
auto_reply_private = True
me_cache = None
me_cache_time = 0

# ========================== TOXIC REPLIES ==========================
BLOOD_REPLIES = [
    "🩸 diam.", "🩸 hah?", "🩸 y.", "🩸 iya.", "🩸 oke.",
    "🩸 sbr.", "🩸 nguik.", "🩸 Y.", "🩸 mampus.",
    "🩸 bacot.", "🩸 goblok.", "🩸 tai.", "🩸 diem."
]
MENTION_BLOOD = ["🩸 hah? DM.", "🩸 nyari apa?", "🩸 berisik.", "🩸 bacot lo."]
AFK_BLOOD = "🩸 **THE TAMERS** lagi AFK. Lo sabar. Atau lo gue setrum."

def random_blood(): return random.choice(BLOOD_REPLIES)
def random_mention(): return random.choice(MENTION_BLOOD)

def get_uptime():
    e = time.time() - BOT_START
    d = int(e // 86400)
    h = int((e % 86400) // 3600)
    m = int((e % 3600) // 60)
    s = int(e % 60)
    if d > 0: return f"{d}d {h}h"
    if h > 0: return f"{h}h {m}m"
    if m > 0: return f"{m}m {s}s"
    return f"{s}s"

def blood_progress(curr, total, bar_len=8):
    if total <= 0: return "🩸░░░░░░░░ 0%"
    percent = int(curr / total * 100)
    filled = int(bar_len * curr / total)
    bar = "🩸" * filled + "░" * (bar_len - filled)
    return f"{bar} {percent}%"

# ========================== JSON LOAD/SAVE ==========================
def save_json(filepath, data_set):
    try:
        with open(filepath, "w") as f:
            json.dump({"data": list(data_set)}, f)
    except Exception as e:
        print(f"⚠️ Gagal save {filepath}: {e}")

def load_json(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                return set(json.load(f).get("data", []))
        except:
            pass
    return set()

# ========================== CACHE ME ==========================
async def get_cached_me(client):
    global me_cache, me_cache_time
    if not me_cache or time.time() - me_cache_time > 300:
        me_cache = await client.get_me()
        me_cache_time = time.time()
    return me_cache

# ========================== PERINTAH ==========================
async def cmd_ping(client, message):
    start = time.time()
    await asyncio.sleep(0.03)
    ping = int((time.time() - start) * 1000)
    me = await get_cached_me(client)
    status = "🩸 CEPAT" if ping < 80 else "🩸 NGOPI" if ping < 200 else "🩸 LEMOT"
    await message.reply(
        f"🩸 **PING**\n"
        f"┃ respon : {ping} ms\n"
        f"┃ status : {status}\n"
        f"┃ uptime : {get_uptime()}\n"
        f"┃ tamer  : {me.first_name}\n"
        f"🩸 {BRAND}"
    )

async def cmd_status(client, message):
    me = await get_cached_me(client)
    await message.reply(
        f"🩸 **STATUS**\n"
        f"┃ tamer    : {me.first_name}\n"
        f"┃ username : @{me.username or 'none'}\n"
        f"┃ id       : `{me.id}`\n"
        f"┃ uptime   : {get_uptime()}\n"
        f"┃ blacklist: {len(blacklist)}\n"
        f"┃ whitelist: {len(whitelist)}\n"
        f"┃ gban     : {len(gban)}\n"
        f"┃ afk      : {'ON' if afk_mode else 'OFF'}\n"
        f"┃ autoreply: {'ON' if auto_reply_private else 'OFF'}\n"
        f"🩸 {BRAND} {VERSION}"
    )

async def cmd_info(client, message):
    me = await get_cached_me(client)
    nama = me.first_name + (f" {me.last_name}" if me.last_name else "")
    await message.reply(
        f"🩸 **INFO**\n"
        f"┃ nama     : {nama}\n"
        f"┃ username : @{me.username or 'none'}\n"
        f"┃ id       : `{me.id}`\n"
        f"┃ premium  : {'YA' if getattr(me, 'is_premium', False) else 'TIDAK'}\n"
        f"┃ uptime   : {get_uptime()}\n"
        f"🩸 {BRAND}"
    )

async def cmd_afk(client, message):
    global afk_mode
    afk_mode = True
    await message.reply("🩸 **AFK ON**\n┃ gue pergi. ketik .unafk.\n🩸 THE TAMERS")

async def cmd_unafk(client, message):
    global afk_mode
    afk_mode = False
    await message.reply(f"🩸 **AFK OFF**\n┃ gue balik ({get_uptime()})\n🩸 THE TAMERS")

async def cmd_grup_on(client, message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("🩸 ini bukan grup.")
        return
    whitelist.add(message.chat.id)
    save_json(WHITELIST_FILE, whitelist)
    await message.reply(f"🩸 **AUTO REPLY ON**\n┃ {message.chat.title}\n🩸 {BRAND}")

async def cmd_grup_off(client, message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("🩸 ini bukan grup.")
        return
    whitelist.discard(message.chat.id)
    save_json(WHITELIST_FILE, whitelist)
    await message.reply(f"🩸 **AUTO REPLY OFF**\n┃ {message.chat.title}\n🩸 {BRAND}")

async def cmd_listgrup(client, message):
    if not whitelist:
        await message.reply("🩸 kosong.")
        return
    txt = "🩸 **GRUP AUTO REPLY**\n"
    for gid in list(whitelist)[:20]:
        try:
            chat = await client.get_chat(gid)
            txt += f"┃ {chat.title}\n"
        except:
            txt += f"┃ {gid}\n"
    await message.reply(txt)

async def cmd_private_on(client, message):
    global auto_reply_private
    auto_reply_private = True
    await message.reply("🩸 **PRIVATE ON**\n┃ DM dibales.\n🩸 {BRAND}")

async def cmd_private_off(client, message):
    global auto_reply_private
    auto_reply_private = False
    await message.reply("🩸 **PRIVATE OFF**\n┃ DM gak digubris.\n🩸 {BRAND}")

async def cmd_addbl(client, message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("🩸 ini bukan grup.")
        return
    blacklist.add(message.chat.id)
    save_json(BLACKLIST_FILE, blacklist)
    await message.reply(f"🩸 **BLACKLIST**\n┃ {message.chat.title}\n🩸 {BRAND}")

async def cmd_rmbl(client, message):
    if message.chat.id in blacklist:
        blacklist.discard(message.chat.id)
        save_json(BLACKLIST_FILE, blacklist)
        await message.reply(f"🩸 **UNBLACKLIST**\n┃ {message.chat.title}\n🩸 {BRAND}")
    else:
        await message.reply("🩸 gak ada di blacklist.")

async def cmd_listbl(client, message):
    if not blacklist:
        await message.reply("🩸 kosong.")
        return
    txt = "🩸 **BLACKLIST**\n"
    for gid in list(blacklist)[:20]:
        try:
            chat = await client.get_chat(gid)
            txt += f"┃ {chat.title}\n"
        except:
            txt += f"┃ {gid}\n"
    await message.reply(txt)

async def cmd_gban(client, message):
    global gban
    target = None
    name = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        try:
            u = await client.get_users(message.command[1])
            target = u.id
            name = u.first_name
        except:
            await message.reply("🩸 gak nemu user.")
            return
    if not target:
        await message.reply("🩸 .gban @user atau reply.")
        return
    me = await get_cached_me(client)
    if target == me.id:
        await message.reply("🩸 goblok, mau gban diri sendiri?")
        return
    if target in gban:
        await message.reply(f"🩸 {name} udah kena GBAN.")
        return
    await message.reply(f"🩸 **GBAN**\n┃ {name}\n{blood_progress(0,3)}")
    try:
        await client.block_user(target)
    except:
        pass
    gban.add(target)
    save_json(GBAN_FILE, gban)
    await message.reply(f"🩸 **GBAN DONE**\n┃ {name} telah dihapus.\n🩸 {BRAND}")

async def cmd_ungban(client, message):
    global gban
    target = None
    name = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        try:
            u = await client.get_users(message.command[1])
            target = u.id
            name = u.first_name
        except:
            await message.reply("🩸 gak nemu.")
            return
    if target not in gban:
        await message.reply(f"🩸 {name} gak ada di GBAN.")
        return
    gban.discard(target)
    save_json(GBAN_FILE, gban)
    await message.reply(f"🩸 **UNGBAN**\n┃ {name} dibebaskan.\n🩸 {BRAND}")

async def cmd_listgban(client, message):
    if not gban:
        await message.reply("🩸 kosong.")
        return
    txt = "🩸 **GBAN LIST**\n"
    for uid in list(gban)[:20]:
        try:
            u = await client.get_users(uid)
            txt += f"┃ {u.first_name} (@{u.username or 'none'})\n"
        except:
            txt += f"┃ {uid}\n"
    await message.reply(txt)

# ========================== AUTO REPLY ==========================
async def auto_reply_handler(client, message):
    if not message.from_user or message.from_user.is_bot:
        return
    if message.text and message.text.startswith('.'):
        return
    if message.from_user.id in gban:
        try:
            await client.block_user(message.from_user.id)
        except:
            pass
        return
    if afk_mode and message.chat.type == ChatType.PRIVATE:
        uid = message.from_user.id
        if uid in afk_approved:
            if auto_reply_private:
                await message.reply(random_blood())
            return
        if uid not in afk_pending:
            afk_pending[uid] = {"count": 0}
        afk_pending[uid]["count"] += 1
        if afk_pending[uid]["count"] >= 5:
            await client.block_user(uid)
            await message.reply("🩸 LO KEBLOKIR.")
            return
        await message.reply(AFK_BLOOD)
        return
    if message.chat.type == ChatType.PRIVATE:
        if auto_reply_private:
            await message.reply(random_blood())
        return
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        if message.chat.id not in whitelist or message.chat.id in blacklist:
            return
        me = await get_cached_me(client)
        if me.username and message.text and f"@{me.username.lower()}" in message.text.lower():
            await message.reply(random_mention())
            return
        await message.reply(random_blood())

# ========================== FLASK UNTUK KEEP ALIVE ==========================
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "🩸 THE TAMERS USERBOT RUNNING", 200

@flask_app.route("/health")
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port, threaded=False)

# ========================== SHUTDOWN HANDLER ==========================
def signal_handler(sig, frame):
    print("🩸 Shutting down...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ========================== MAIN ==========================
async def main():
    global whitelist, blacklist, gban
    
    whitelist = load_json(WHITELIST_FILE)
    blacklist = load_json(BLACKLIST_FILE)
    gban = load_json(GBAN_FILE)
    
    print("🩸"*30)
    print("🩸 THE TAMERS - RAILWAY STABLE")
    print(f"🩸 GBAN: {len(gban)} | BLACKLIST: {len(blacklist)} | WHITELIST: {len(whitelist)}")
    print("🩸"*30)
    
    app = Client("userbot", session_string=SESSION_STRING, api_id=API_ID, api_hash=API_HASH)
    await app.start()
    
    me = await app.get_me()
    print(f"🩸 LOGIN: {me.first_name} (@{me.username or 'none'})")
    print("🩸 BOT SIAP")
    
    # REGISTER COMMANDS
    @app.on_message(filters.me & filters.command("ping", prefixes="."))
    async def _(c,m): await cmd_ping(c,m)
    @app.on_message(filters.me & filters.command("status", prefixes="."))
    async def _(c,m): await cmd_status(c,m)
    @app.on_message(filters.me & filters.command("info", prefixes="."))
    async def _(c,m): await cmd_info(c,m)
    @app.on_message(filters.me & filters.command("afk", prefixes="."))
    async def _(c,m): await cmd_afk(c,m)
    @app.on_message(filters.me & filters.command("unafk", prefixes="."))
    async def _(c,m): await cmd_unafk(c,m)
    @app.on_message(filters.me & filters.command("grup on", prefixes="."))
    async def _(c,m): await cmd_grup_on(c,m)
    @app.on_message(filters.me & filters.command("grup off", prefixes="."))
    async def _(c,m): await cmd_grup_off(c,m)
    @app.on_message(filters.me & filters.command("listgrup", prefixes="."))
    async def _(c,m): await cmd_listgrup(c,m)
    @app.on_message(filters.me & filters.command("private on", prefixes="."))
    async def _(c,m): await cmd_private_on(c,m)
    @app.on_message(filters.me & filters.command("private off", prefixes="."))
    async def _(c,m): await cmd_private_off(c,m)
    @app.on_message(filters.me & filters.command("addbl", prefixes="."))
    async def _(c,m): await cmd_addbl(c,m)
    @app.on_message(filters.me & filters.command("rmbl", prefixes="."))
    async def _(c,m): await cmd_rmbl(c,m)
    @app.on_message(filters.me & filters.command("listbl", prefixes="."))
    async def _(c,m): await cmd_listbl(c,m)
    @app.on_message(filters.me & filters.command("gban", prefixes="."))
    async def _(c,m): await cmd_gban(c,m)
    @app.on_message(filters.me & filters.command("ungban", prefixes="."))
    async def _(c,m): await cmd_ungban(c,m)
    @app.on_message(filters.me & filters.command("listgban", prefixes="."))
    async def _(c,m): await cmd_listgban(c,m)
    
    @app.on_message(filters.incoming & ~filters.me)
    async def _(c,m): await auto_reply_handler(c,m)
    
    print("🩸 ALL COMMANDS LOADED")
    print("🩸 KEEP ALIVE ACTIVE")
    
    while True:
        await asyncio.sleep(60)
        print(f"🩸 [{datetime.now().strftime('%H:%M:%S')}] Alive")

if __name__ == "__main__":
    import threading
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🩸 THE TAMERS PERGI.")
    except Exception as e:
        print(f"🩸 FATAL: {e}")
        sys.exit(1)
