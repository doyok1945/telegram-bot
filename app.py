"""
THE TAMERS USERBOT v2.0 - BLOOD EDITION
Railway Ready | No Border | Full Blood | Toxic AF
"""

import sys
import warnings
import logging
import asyncio
import random
import json
import os
import threading
import time
from datetime import datetime
from flask import Flask, request

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, PeerIdInvalid
from pyrogram.types import Message
from pyrogram.enums import ChatType

# ========================== MATIKAN LOG SAMPAH ==========================
warnings.filterwarnings("ignore")
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

# ========================== KONFIG DARAH ==========================
API_ID = int(os.getenv("API_ID", 32584214))
API_HASH = os.getenv("API_HASH", "6a59dd69d7e9db9916ff9c07eb237076")
SESSION_STRING = os.getenv("SESSION_STRING", "")
if not SESSION_STRING:
    print("🩸 SESSION_STRING NGGAK ADA, TAI!")
    sys.exit(1)

BLACKLIST_FILE = "blacklist.json"
WHITELIST_FILE = "whitelist.json"
GBAN_FILE = "gban_list.json"
BOT_START = time.time()

BRAND = "THE TAMERS"
VERSION = "2.0.0-BLOOD"

# ========================== DATA GLOBAL ==========================
BLACKLIST = set()
WHITELIST = set()
GBAN = set()
AFK_MODE = False
AFK_PENDING = {}
AFK_APPROVED = set()
AUTO_REPLY_PRIVATE = True

# ========================== BALASAN TOXIC + DARAH ==========================
BLOOD_REPLIES = [
    "🩸 diam.", "🩸 hah?", "🩸 y.", "🩸 iya.", "🩸 oke.",
    "🩸 sbr.", "🩸 nguik.", "🩸  Y.", "🩸   .", "🩸  *diam*",
    "🩸  mampus.", "🩸  bacot.", "🩸  goblok.", "🩸  tai."
]
MENTION_BLOOD = [
    "🩸 hah? DM.", "🩸 nyari apa?", "🩸  berisik.", "🩸  .", "🩸  bacot lo."
]
AFK_BLOOD = "🩸 **THE TAMERS** lagi nyekar. Lo sabar. Atau lo gue setrum."

def random_blood():
    return random.choice(BLOOD_REPLIES)

def random_mention():
    return random.choice(MENTION_BLOOD)

# ========================== FUNGSI KERAS & REAL TIME ==========================
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

def blood_progress(curr, total, len_bar=10):
    if total <= 0:
        return "🩸░░░░░░░░░░ 0%"
    persen = int(curr / total * 100)
    filled = int(len_bar * curr / total)
    bar = "🩸" * filled + "░" * (len_bar - filled)
    return f"{bar} {persen}%"

# ========================== LOAD/SAVE ==========================
def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, "r") as f:
                return set(json.load(f).get("data", []))
        except:
            pass
    return default

def save_json(file, data_set):
    with open(file, "w") as f:
        json.dump({"data": list(data_set)}, f, indent=2)

BLACKLIST = load_json(BLACKLIST_FILE, set())
WHITELIST = load_json(WHITELIST_FILE, set())
GBAN = load_json(GBAN_FILE, set())

# ========================== PERINTAH BERDARAH ==========================
async def cmd_ping(client, message):
    start = time.time()
    await asyncio.sleep(0.05)
    ping_ms = int((time.time() - start) * 1000)
    me = await client.get_me()
    status = "🩸SUPER CEPAT" if ping_ms < 60 else "🩸 NGOPI DULU" if ping_ms < 180 else "🩸LEMOT GOBLOK"
    await message.reply(
        f"🩸 **PING**\n"
        f"┃ respon : {ping_ms} ms\n"
        f"┃ status  : {status}\n"
        f"┃ uptime  : {get_uptime()}\n"
        f"┃ tamer   : {me.first_name}\n"
        f"┃ id      : `{me.id}`\n"
        f"🩸 {BRAND}"
    )

async def cmd_status(client, message):
    me = await client.get_me()
    pvt = grp = ch = 0
    async for d in client.get_dialogs():
        if d.chat.type == ChatType.PRIVATE and d.chat.id > 0: pvt += 1
        elif d.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]: grp += 1
        elif d.chat.type == ChatType.CHANNEL: ch += 1
    await message.reply(
        f"🩸 **STATUS DARAH**\n"
        f"┃ tamer    : {me.first_name}\n"
        f"┃ username : @{me.username if me.username else 'none'}\n"
        f"┃ id       : `{me.id}`\n"
        f"┃ private  : {pvt} chat\n"
        f"┃ group    : {grp}\n"
        f"┃ channel  : {ch}\n"
        f"┃ uptime   : {get_uptime()}\n"
        f"┃ blacklist: {len(BLACKLIST)}\n"
        f"┃ gban     : {len(GBAN)}\n"
        f"┃ autoreply: {'ON' if AUTO_REPLY_PRIVATE else 'OFF'}\n"
        f"🩸 {BRAND} {VERSION}"
    )

async def cmd_info(client, message):
    me = await client.get_me()
    nama = me.first_name + (f" {me.last_name}" if me.last_name else "")
    await message.reply(
        f"🩸 **INFO TAMER**\n"
        f"┃ nama     : {nama}\n"
        f"┃ username : @{me.username if me.username else 'none'}\n"
        f"┃ id       : `{me.id}`\n"
        f"┃ premium  : {'🩸YA' if getattr(me, 'is_premium', False) else '🩸BODO'}\n"
        f"┃ afk      : {'🩸AKTIF' if AFK_MODE else '🩸OFF'}\n"
        f"┃ uptime   : {get_uptime()}\n"
        f"🩸 {BRAND}"
    )

async def cmd_afk(client, message):
    global AFK_MODE
    AFK_MODE = True
    await message.reply("🩸 **AFK AKTIF**\n┃ gue pergi. ketik .unafk.\n🩸 THE TAMERS")

async def cmd_unafk(client, message):
    global AFK_MODE
    AFK_MODE = False
    await message.reply(f"🩸 **AFK NONAKTIF**\n┃ gue balik ({get_uptime()})\n🩸 THE TAMERS")

async def cmd_gcast(client, message):
    teks = None
    if message.reply_to_message and message.reply_to_message.text:
        teks = message.reply_to_message.text
    elif len(message.command) > 1:
        teks = ' '.join(message.command[1:])
    if not teks:
        await message.reply("🩸 .gcast <pesan> atau reply")
        return
    await message.delete()
    total = 0
    async for d in client.get_dialogs():
        if d.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] and d.chat.id not in BLACKLIST:
            total += 1
    if total == 0:
        await message.reply("🩸 gak ada grup.")
        return
    msg = await client.send_message(message.chat.id, f"🩸 GCAST BERDARAH\n┃ target {total} grup\n{blood_progress(0,total)}")
    ok = fail = 0
    for i, d in enumerate(client.get_dialogs()):
        if d.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] and d.chat.id not in BLACKLIST:
            try:
                await client.send_message(d.chat.id, teks)
                ok += 1
            except:
                fail += 1
            if (i+1) % 5 == 0:
                await msg.edit(f"🩸 GCAST\n┃ {ok}✅ {fail}❌\n{blood_progress(i+1,total)}")
            await asyncio.sleep(0.3)
    await msg.edit(f"🩸 GCAST SELESAI\n┃ sukses {ok}\n┃ gagal {fail}\n🩸 {BRAND}")

async def cmd_gban(client, message):
    global GBAN
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        inp = message.command[1]
        try:
            u = await client.get_users(inp)
            target = u.id
            name = u.first_name
        except:
            await message.reply("🩸 gak nemu tai.")
            return
    if not target:
        await message.reply("🩸 .gban @user atau reply")
        return
    me = await client.get_me()
    if target == me.id:
        await message.reply("🩸 mau gban diri sendiri? tolol.")
        return
    if target in GBAN:
        await message.reply(f"🩸 {name} udah kena GBAN.")
        return
    await message.reply(f"🩸 **GBAN**\n┃ target {name}\n{blood_progress(0,3)}")
    await client.block_user(target)
    async for d in client.get_dialogs():
        if d.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            try:
                await d.chat.ban_member(target)
            except:
                pass
            await asyncio.sleep(0.2)
    GBAN.add(target)
    save_json(GBAN_FILE, GBAN)
    await message.reply(f"🩸 **GBAN DONE**\n┃ {name} dihapus dari muka bumi.\n🩸 {BRAND}")

async def cmd_ungban(client, message):
    global GBAN
    target = None
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
    if target not in GBAN:
        await message.reply(f"🩸 {name} gak ada di GBAN.")
        return
    GBAN.discard(target)
    save_json(GBAN_FILE, GBAN)
    await message.reply(f"🩸 **UNGBAN**\n┃ {name} bebas. buat sekarang.")

async def cmd_addbl(client, message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("🩸 ini bukan grup tai.")
        return
    BLACKLIST.add(message.chat.id)
    save_json(BLACKLIST_FILE, BLACKLIST)
    await message.reply(f"🩸 **BLACKLIST**\n┃ {message.chat.title} masuk daftar hitam.")

async def cmd_rmbl(client, message):
    if message.chat.id in BLACKLIST:
        BLACKLIST.discard(message.chat.id)
        save_json(BLACKLIST_FILE, BLACKLIST)
        await message.reply(f"🩸 **UNBLACKLIST**\n┃ {message.chat.title} dikeluarkan.")
    else:
        await message.reply("🩸 gak ada di blacklist.")

async def cmd_listbl(client, message):
    if not BLACKLIST:
        await message.reply("🩸 kosong.")
        return
    txt = "🩸 **BLACKLIST GROUP**\n"
    for gid in list(BLACKLIST)[:20]:
        try:
            chat = await client.get_chat(gid)
            txt += f"┃ {chat.title}\n"
        except:
            txt += f"┃ {gid}\n"
    await message.reply(txt)

async def cmd_spam(client, message):
    if len(message.command) < 3 and not message.reply_to_message:
        await message.reply("🩸 .spam 5 bacot")
        return
    try:
        count = min(int(message.command[1]), 30)
    except:
        await message.reply("🩸 angka goblok.")
        return
    if message.reply_to_message:
        teks = message.reply_to_message.text or message.reply_to_message.caption
    else:
        teks = ' '.join(message.command[2:])
    if not teks:
        await message.reply("🩸 teks kosong.")
        return
    status = await message.reply(f"🩸 SPAM\n┃ {count}x\n{blood_progress(0,count)}")
    await message.delete()
    for i in range(count):
        await client.send_message(message.chat.id, teks)
        if (i+1) % 5 == 0:
            await status.edit(f"🩸 SPAM\n┃ {count}x\n{blood_progress(i+1,count)}")
        await asyncio.sleep(0.2)
    await status.edit(f"🩸 SPAM DONE\n┃ {count} pesan terkirim.\n🩸 {BRAND}")

# ========================== AUTO REPLY DARAH ==========================
async def blood_reply_handler(client, message):
    if message.text and message.text.startswith('.'):
        return
    if not message.from_user or message.from_user.is_bot:
        return
    if message.from_user.id in GBAN:
        try:
            await client.block_user(message.from_user.id)
        except:
            pass
        return
    if AFK_MODE and message.chat.type == ChatType.PRIVATE:
        uid = message.from_user.id
        if uid in AFK_APPROVED:
            if AUTO_REPLY_PRIVATE:
                await message.reply(random_blood())
            return
        if uid not in AFK_PENDING:
            AFK_PENDING[uid] = {"count": 0, "warned": False}
        AFK_PENDING[uid]["count"] += 1
        cnt = AFK_PENDING[uid]["count"]
        if cnt >= 5:
            await client.block_user(uid)
            await message.reply("🩸 LO KEBLOKIR, GOBLOK.")
            return
        if cnt >= 3 and not AFK_PENDING[uid]["warned"]:
            AFK_PENDING[uid]["warned"] = True
            await message.reply("🩸 PERINGATAN! JANGAN SPAM.")
            return
        await message.reply(AFK_BLOOD)
        return
    if message.chat.type == ChatType.PRIVATE:
        if AUTO_REPLY_PRIVATE:
            await message.reply(random_blood())
        return
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        if message.chat.id not in WHITELIST or message.chat.id in BLACKLIST:
            return
        me = await client.get_me()
        if me.username and message.text and f"@{me.username.lower()}" in message.text.lower():
            await message.reply(random_mention())
            return
        await message.reply(random_blood())

# ========================== FLASK (Biar railway idup) ==========================
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "🩸 THE TAMERS BLOOD EDITION RUNNING 🩸", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port, threaded=True)

# ========================== MAIN ==========================
async def main():
    global AUTO_REPLY_PRIVATE, WHITELIST, BLACKLIST, GBAN
    WHITELIST = load_json(WHITELIST_FILE, set())
    BLACKLIST = load_json(BLACKLIST_FILE, set())
    GBAN = load_json(GBAN_FILE, set())

    print("🩸"*30)
    print("🩸 THE TAMERS BLOOD EDITION")
    print("🩸 RAILWAY | TOXIC | GBAN")
    print(f"🩸 GBAN : {len(GBAN)} korban")
    print("🩸"*30)

    app = Client("userbot", session_string=SESSION_STRING, api_id=API_ID, api_hash=API_HASH)
    await app.start()
    me = await app.get_me()
    print(f"🩸 LOGIN : {me.first_name} (@{me.username if me.username else 'none'})")
    print("🩸 ALL COMMANDS ACTIVE")

    # Commands
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
    @app.on_message(filters.me & filters.command("gcast", prefixes="."))
    async def _(c,m): await cmd_gcast(c,m)
    @app.on_message(filters.me & filters.command("gban", prefixes="."))
    async def _(c,m): await cmd_gban(c,m)
    @app.on_message(filters.me & filters.command("ungban", prefixes="."))
    async def _(c,m): await cmd_ungban(c,m)
    @app.on_message(filters.me & filters.command("addbl", prefixes="."))
    async def _(c,m): await cmd_addbl(c,m)
    @app.on_message(filters.me & filters.command("rmbl", prefixes="."))
    async def _(c,m): await cmd_rmbl(c,m)
    @app.on_message(filters.me & filters.command("listbl", prefixes="."))
    async def _(c,m): await cmd_listbl(c,m)
    @app.on_message(filters.me & filters.command("spam", prefixes="."))
    async def _(c,m): await cmd_spam(c,m)

    @app.on_message(filters.incoming & ~filters.me)
    async def _(c,m): await blood_reply_handler(c,m)

    print("🩸 BOT SIAP MEMBANTAI")
    while True:
        await asyncio.sleep(60)
        print(f"🩸 [{datetime.now().strftime('%H:%M:%S')}] still alive, tai.")

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🩸 THE TAMERS PERGI. SAMPAI JUMPA DI NERAKA.")
