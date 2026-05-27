"""
THE TAMERS USERBOT v2.2 - PEER ID FIX EDITION
Auto cleanup invalid peer IDs
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
from pyrogram.errors import FloodWait, UserIsBlocked, PeerIdInvalid
from pyrogram.types import Message
from pyrogram.enums import ChatType

warnings.filterwarnings("ignore")
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# ========================== ENV CHECK ==========================
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")

if not API_ID or not API_HASH or not SESSION_STRING:
    print("🩸 GOBLOK! SET API_ID, API_HASH, SESSION_STRING DI RAILWAY ENV!")
    sys.exit(1)

# ========================== KONFIG ==========================
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

BLACKLIST_FILE = f"{DATA_DIR}/blacklist.json"
WHITELIST_FILE = f"{DATA_DIR}/whitelist.json"
GBAN_FILE = f"{DATA_DIR}/gban.json"

BOT_START = time.time()
BRAND = "THE TAMERS"

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
BLOOD_REPLIES = ["🩸 diam.", "🩸 hah?", "🩸 y.", "🩸 iya.", "🩸 oke.", "🩸 bacot.", "🩸 goblok.", "🩸 tai."]
MENTION_BLOOD = ["🩸 hah? DM.", "🩸 nyari apa?", "🩸 berisik."]
AFK_BLOOD = "🩸 **THE TAMERS** lagi AFK."

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

# ========================== JSON IO DENGAN VALIDASI ==========================
def save_json(filepath, data_set):
    try:
        # Convert ke list biar json friendly
        data_list = [int(x) for x in data_set if isinstance(x, (int, str)) and str(x).lstrip('-').isdigit()]
        with open(filepath, "w") as f:
            json.dump({"data": data_list}, f)
    except Exception as e:
        print(f"⚠️ Gagal save {filepath}: {e}")

async def validate_and_clean_peer_ids(client, peer_set, set_name):
    """Bersihin ID yang gak valid dari blacklist/whitelist"""
    invalid_ids = []
    valid_ids = []
    
    for pid in peer_set:
        try:
            # Coba resolve peer
            await client.resolve_peer(int(pid))
            valid_ids.append(pid)
        except (ValueError, PeerIdInvalid, KeyError) as e:
            print(f"🩸 Hapus {set_name} ID invalid: {pid} - {e}")
            invalid_ids.append(pid)
        except Exception as e:
            print(f"⚠️ Error cek ID {pid}: {e}")
            invalid_ids.append(pid)
    
    if invalid_ids:
        print(f"🩸 Bersihin {len(invalid_ids)} ID invalid dari {set_name}")
    
    return set(valid_ids)

async def load_json_with_validation(client, filepath, set_name, default=set()):
    """Load JSON dan validasi ID"""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                raw_ids = data.get("data", [])
                # Convert ke int
                peer_set = {int(x) for x in raw_ids if str(x).lstrip('-').isdigit()}
                
                if client and peer_set:
                    peer_set = await validate_and_clean_peer_ids(client, peer_set, set_name)
                    
                    if peer_set != set(raw_ids):
                        # Simpan ulang yang udah dibersihin
                        save_json(filepath, peer_set)
                
                return peer_set
        except Exception as e:
            print(f"⚠️ Error load {filepath}: {e}")
    return default

# ========================== CACHE ME ==========================
async def get_cached_me(client):
    global me_cache, me_cache_time
    if not me_cache or time.time() - me_cache_time > 300:
        try:
            me_cache = await client.get_me()
            me_cache_time = time.time()
        except Exception as e:
            print(f"⚠️ Gagal get me: {e}")
    return me_cache

# ========================== PERINTAH ==========================
async def cmd_ping(client, message):
    start = time.time()
    await asyncio.sleep(0.03)
    ping = int((time.time() - start) * 1000)
    me = await get_cached_me(client)
    await message.reply(f"🩸 **PING**\n┃ {ping} ms\n┃ uptime: {get_uptime()}\n┃ {me.first_name if me else '?'}\n🩸 {BRAND}")

async def cmd_status(client, message):
    me = await get_cached_me(client)
    await message.reply(f"🩸 **STATUS**\n┃ {me.first_name if me else '?'}\n┃ @{me.username if me and me.username else 'none'}\n┃ blacklist: {len(blacklist)}\n┃ whitelist: {len(whitelist)}\n┃ gban: {len(gban)}\n┃ uptime: {get_uptime()}\n🩸 {BRAND}")

async def cmd_info(client, message):
    me = await get_cached_me(client)
    if not me:
        await message.reply("🩸 Gagal dapat info user.")
        return
    await message.reply(f"🩸 **INFO**\n┃ {me.first_name}\n┃ id: `{me.id}`\n┃ premium: {'YA' if getattr(me, 'is_premium', False) else 'TIDAK'}\n┃ uptime: {get_uptime()}\n🩸 {BRAND}")

async def cmd_afk(client, message):
    global afk_mode
    afk_mode = True
    await message.reply("🩸 **AFK ON**\n🩸 THE TAMERS")

async def cmd_unafk(client, message):
    global afk_mode
    afk_mode = False
    await message.reply(f"🩸 **AFK OFF** ({get_uptime()})\n🩸 THE TAMERS")

async def cmd_grup_on(client, message):
    global whitelist
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("🩸 ini bukan grup.")
        return
    whitelist.add(message.chat.id)
    save_json(WHITELIST_FILE, whitelist)
    await message.reply(f"🩸 **AUTO REPLY ON**\n┃ {message.chat.title}\n🩸 {BRAND}")

async def cmd_grup_off(client, message):
    global whitelist
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
            txt += f"┃ ID: {gid} (invalid)\n"
    await message.reply(txt)

async def cmd_private_on(client, message):
    global auto_reply_private
    auto_reply_private = True
    await message.reply("🩸 **PRIVATE ON**")

async def cmd_private_off(client, message):
    global auto_reply_private
    auto_reply_private = False
    await message.reply("🩸 **PRIVATE OFF**")

async def cmd_addbl(client, message):
    global blacklist
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("🩸 ini bukan grup.")
        return
    blacklist.add(message.chat.id)
    save_json(BLACKLIST_FILE, blacklist)
    await message.reply(f"🩸 **BLACKLIST**\n┃ {message.chat.title}")

async def cmd_rmbl(client, message):
    global blacklist
    if message.chat.id in blacklist:
        blacklist.discard(message.chat.id)
        save_json(BLACKLIST_FILE, blacklist)
        await message.reply(f"🩸 **REMOVED**\n┃ {message.chat.title}")
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
            txt += f"┃ ID: {gid} (invalid)\n"
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
    if me and target == me.id:
        await message.reply("🩸 goblok, mau gban diri sendiri?")
        return
    if target in gban:
        await message.reply(f"🩸 {name} udah kena GBAN.")
        return
    try:
        await client.block_user(target)
    except:
        pass
    gban.add(target)
    save_json(GBAN_FILE, gban)
    await message.reply(f"🩸 **GBAN DONE**\n┃ {name}\n🩸 {BRAND}")

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
    await message.reply(f"🩸 **UNGBAN**\n┃ {name}")

async def cmd_listgban(client, message):
    if not gban:
        await message.reply("🩸 kosong.")
        return
    txt = "🩸 **GBAN LIST**\n"
    for uid in list(gban)[:20]:
        try:
            u = await client.get_users(uid)
            txt += f"┃ {u.first_name}\n"
        except:
            txt += f"┃ ID: {uid}\n"
    await message.reply(txt)

# ========================== AUTO REPLY DENGAN TRY EXCEPT ==========================
async def auto_reply_handler(client, message):
    try:
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
        
        # AFK MODE
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
                try:
                    await client.block_user(uid)
                except:
                    pass
                await message.reply("🩸 LO KEBLOKIR.")
                return
            await message.reply(AFK_BLOOD)
            return
        
        # PRIVATE CHAT
        if message.chat.type == ChatType.PRIVATE:
            if auto_reply_private:
                await message.reply(random_blood())
            return
        
        # GROUP CHAT
        if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            if message.chat.id not in whitelist or message.chat.id in blacklist:
                return
            me = await get_cached_me(client)
            if me and me.username and message.text and f"@{me.username.lower()}" in message.text.lower():
                await message.reply(random_mention())
                return
            await message.reply(random_blood())
    except PeerIdInvalid:
        # Peer invalid, abaikan aja
        pass
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        # Jangan print error biar gak spam log
        pass

# ========================== FLASK ==========================
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "🩸 THE TAMERS RUNNING", 200

@flask_app.route("/health")
def health():
    return "OK", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port, threaded=False)

def signal_handler(sig, frame):
    print("🩸 Shutting down...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ========================== MAIN ==========================
async def main():
    global whitelist, blacklist, gban
    
    print("🩸"*30)
    print("🩸 THE TAMERS - PEER ID FIX EDITION")
    print("🩸"*30)
    
    app = Client("userbot", session_string=SESSION_STRING, api_id=API_ID, api_hash=API_HASH)
    await app.start()
    
    me = await app.get_me()
    print(f"🩸 LOGIN: {me.first_name} (@{me.username or 'none'})")
    
    # LOAD DENGAN VALIDASI (pake client yang udah start)
    print("🩸 Validasi blacklist/whitelist IDs...")
    blacklist = await load_json_with_validation(app, BLACKLIST_FILE, "BLACKLIST", set())
    whitelist = await load_json_with_validation(app, WHITELIST_FILE, "WHITELIST", set())
    gban = load_json(GBAN_FILE)  # GBAN user ID gak perlu divalidasi berat
    
    print(f"🩸 BLACKLIST: {len(blacklist)} | WHITELIST: {len(whitelist)} | GBAN: {len(gban)}")
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
    print("🩸 RUNNING...")
    
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
