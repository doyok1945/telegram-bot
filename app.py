"""
THE TAMERS USERBOT v2.0 - DARK EDITION
NO BORDER, NO ALAY, PURE SEREM
RAILWAY READY - KAGA BISA BANNED ANJING
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
from flask import Flask

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, PeerIdInvalid
from pyrogram.types import Message
from pyrogram.enums import ChatType

# MATIIN LOG SAMPah
warnings.filterwarnings("ignore")
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

app_flask = Flask(__name__)

# KONFIG
API_ID = int(os.getenv("API_ID", "32584214"))
API_HASH = os.getenv("API_HASH", "6a59dd69d7e9db9916ff9c07eb237076")
SESSION_STRING = os.getenv("SESSION_STRING", "")

BLACKLIST_FILE = "blacklist.json"
WHITELIST_FILE = "whitelist.json"
GBAN_FILE = "gban.json"

BOT_START = time.time()
VERSION = "2.0.0"

# DATA GLOBAL
BLACKLIST = set()
WHITELIST = set()
GBAN = set()
AFK_MODE = False
AFK_PENDING = {}
AFK_APPROVED = set()

# REPLY DARK
DARK_REPLIES = [
    "💀", "🦴", "🔪", "⚰️", "☠️", "👻", "🕷️", "🕸️", "🧛", "🧟",
    "mati ae", "okeee", "iya kah", "ngapain", "bodoamat", "peduli? kagak anj"
]
AFK_TEXT = "💀 THE TAMERS lagi AFK. lo ganggu, lo mati."

def dark_reply():
    return random.choice(DARK_REPLIES)

def load_json(file, default):
    if os.path.exists(file):
        try:
            with open(file, 'r') as f:
                return set(json.load(f).get("data", []))
        except:
            pass
    return default

def save_json(file, data):
    with open(file, 'w') as f:
        json.dump({"data": list(data)}, f, indent=2)

def uptime():
    e = time.time() - BOT_START
    d = int(e // 86400)
    h = int((e % 86400) // 3600)
    m = int((e % 3600) // 60)
    if d > 0: return f"{d}d {h}h"
    if h > 0: return f"{h}h {m}m"
    return f"{m}m"

# ============== COMMANDS ==============

async def cmd_ping(c, m):
    start = time.time()
    await asyncio.sleep(0.05)
    ping = int((time.time() - start) * 1000)
    me = await c.get_me()
    status = "🔥" if ping < 100 else "💀" if ping < 300 else "⚰️"
    await m.reply(f"{status} {ping}ms | {me.first_name} | {uptime()}")

async def cmd_status(c, m):
    me = await c.get_me()
    total_pc = 0
    total_gc = 0
    async for d in c.get_dialogs():
        if d.chat.type == ChatType.PRIVATE and d.chat.id > 0:
            total_pc += 1
        elif d.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            total_gc += 1
    await m.reply(f"💀 {me.first_name}\n🆔 {me.id}\n👤 {total_pc} chats\n👥 {total_gc} groups\n🚫 {len(BLACKLIST)}\n✅ {len(WHITELIST)}\n⏱️ {uptime()}\n🔫 THE TAMERS v{VERSION}")

async def cmd_info(c, m):
    me = await c.get_me()
    await m.reply(f"💀 {me.first_name}\n📛 @{me.username if me.username else '-'}\n🆔 {me.id}\n💎 {'Premium' if getattr(me, 'is_premium', False) else 'Free'}\n⏱️ {uptime()}")

async def cmd_afk(c, m):
    global AFK_MODE
    AFK_MODE = True
    await m.reply("💀 AFK ACTIVE. .unafk to wake up.")

async def cmd_unafk(c, m):
    global AFK_MODE
    AFK_MODE = False
    await m.reply(f"💀 BACK AFTER {uptime()}")

async def cmd_approve(c, m):
    global AFK_PENDING, AFK_APPROVED
    uid = None
    if m.reply_to_message and m.reply_to_message.from_user:
        uid = m.reply_to_message.from_user.id
    elif len(m.command) > 1:
        try:
            uid = int(m.command[1])
        except:
            try:
                u = await c.get_users(m.command[1])
                uid = u.id
            except:
                await m.reply("❌ gak nemu")
                return
    if not uid:
        await m.reply("❌ .acc @user atau reply")
        return
    AFK_APPROVED.add(uid)
    AFK_PENDING.pop(uid, None)
    try: await c.unblock_user(uid)
    except: pass
    await m.reply(f"✅ {uid} approved")

async def cmd_reject(c, m):
    global AFK_PENDING, AFK_APPROVED
    uid = None
    if m.reply_to_message and m.reply_to_message.from_user:
        uid = m.reply_to_message.from_user.id
    elif len(m.command) > 1:
        try:
            uid = int(m.command[1])
        except:
            try:
                u = await c.get_users(m.command[1])
                uid = u.id
            except:
                await m.reply("❌ gak nemu")
                return
    if not uid:
        await m.reply("❌ .reject @user atau reply")
        return
    try: await c.block_user(uid)
    except: pass
    AFK_PENDING.pop(uid, None)
    AFK_APPROVED.discard(uid)
    await m.reply(f"🚫 {uid} rejected")

async def cmd_addbl(c, m):
    if m.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await m.reply("❌ pake di grup")
        return
    gid = m.chat.id
    BLACKLIST.add(gid)
    save_json(BLACKLIST_FILE, BLACKLIST)
    await m.reply(f"🚫 {m.chat.title} added to blacklist")

async def cmd_rmbl(c, m):
    if m.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await m.reply("❌ pake di grup")
        return
    gid = m.chat.id
    BLACKLIST.discard(gid)
    save_json(BLACKLIST_FILE, BLACKLIST)
    await m.reply(f"✅ {m.chat.title} removed from blacklist")

async def cmd_grupon(c, m):
    if m.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await m.reply("❌ pake di grup")
        return
    gid = m.chat.id
    WHITELIST.add(gid)
    save_json(WHITELIST_FILE, WHITELIST)
    await m.reply(f"✅ auto-reply ON di {m.chat.title}")

async def cmd_grupoff(c, m):
    if m.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await m.reply("❌ pake di grup")
        return
    gid = m.chat.id
    WHITELIST.discard(gid)
    save_json(WHITELIST_FILE, WHITELIST)
    await m.reply(f"❌ auto-reply OFF di {m.chat.title}")

async def cmd_gban(c, m):
    global GBAN
    uid = None
    name = None
    if m.reply_to_message and m.reply_to_message.from_user:
        uid = m.reply_to_message.from_user.id
        name = m.reply_to_message.from_user.first_name
    elif len(m.command) > 1:
        try:
            uid = int(m.command[1])
            u = await c.get_users(uid)
            name = u.first_name
        except:
            try:
                u = await c.get_users(m.command[1])
                uid = u.id
                name = u.first_name
            except:
                await m.reply("❌ gak nemu")
                return
    if not uid:
        await m.reply("❌ .gban @user atau reply")
        return
    me = await c.get_me()
    if uid == me.id:
        await m.reply("💀 goblok, mau gban diri sendiri?")
        return
    if uid in GBAN:
        await m.reply(f"⚠️ {name} udah di GBAN")
        return
    # report ke spam bot
    try:
        await c.send_message("SpamBot", f"/report {uid} spam")
        await asyncio.sleep(1)
    except: pass
    try:
        await c.send_message("SpamBot", f"/report {uid} impersonation")
    except: pass
    # block dimana2
    try: await c.block_user(uid)
    except: pass
    async for d in c.get_dialogs():
        if d.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            try: await d.chat.ban_member(uid)
            except: pass
            await asyncio.sleep(0.2)
    GBAN.add(uid)
    save_json(GBAN_FILE, GBAN)
    await m.reply(f"🔥 GBAN {name} | {uid}\n💀 dia gak bakal sadar")

async def cmd_ungban(c, m):
    global GBAN
    uid = None
    if m.reply_to_message and m.reply_to_message.from_user:
        uid = m.reply_to_message.from_user.id
    elif len(m.command) > 1:
        try:
            uid = int(m.command[1])
        except:
            try:
                u = await c.get_users(m.command[1])
                uid = u.id
            except:
                await m.reply("❌ gak nemu")
                return
    if uid not in GBAN:
        await m.reply("⚠️ gak ada di GBAN list")
        return
    GBAN.discard(uid)
    save_json(GBAN_FILE, GBAN)
    try: await c.unblock_user(uid)
    except: pass
    await m.reply(f"✅ {uid} removed from GBAN")

async def cmd_gcast(c, m):
    msg = None
    if m.reply_to_message:
        msg = m.reply_to_message.text or m.reply_to_message.caption
    elif len(m.command) > 1:
        msg = m.text.split(maxsplit=1)[1]
    if not msg:
        await m.reply("❌ .gcast <pesan> atau reply")
        return
    await m.delete()
    total = 0
    async for d in c.get_dialogs():
        if d.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] and d.chat.id not in BLACKLIST:
            total += 1
    if total == 0:
        await c.send_message(m.chat.id, "❌ gak ada grup")
        return
    success = 0
    fail = 0
    status = await c.send_message(m.chat.id, f"🔥 GCAST START | target: {total}")
    async for d in c.get_dialogs():
        if d.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] and d.chat.id not in BLACKLIST:
            try:
                await c.send_message(d.chat.id, msg)
                success += 1
            except:
                fail += 1
            await asyncio.sleep(0.3)
    await status.edit(f"🔥 GCAST DONE\n✅ {success} | ❌ {fail}")

async def cmd_ucast(c, m):
    msg = None
    if m.reply_to_message:
        msg = m.reply_to_message.text or m.reply_to_message.caption
    elif len(m.command) > 1:
        msg = m.text.split(maxsplit=1)[1]
    if not msg:
        await m.reply("❌ .ucast_all <pesan> atau reply")
        return
    await m.delete()
    total = 0
    async for d in c.get_dialogs():
        if d.chat.type == ChatType.PRIVATE and d.chat.id > 0:
            total += 1
    if total == 0:
        await c.send_message(m.chat.id, "❌ gak ada private chat")
        return
    success = 0
    blocked = 0
    status = await c.send_message(m.chat.id, f"🔥 UCAST START | target: {total}")
    async for d in c.get_dialogs():
        if d.chat.type == ChatType.PRIVATE and d.chat.id > 0:
            try:
                await c.send_message(d.chat.id, msg)
                success += 1
            except UserIsBlocked:
                blocked += 1
            except:
                pass
            await asyncio.sleep(0.5)
    await status.edit(f"🔥 UCAST DONE\n✅ {success} | 🚫 {blocked}")

async def cmd_spam(c, m):
    if len(m.command) < 2 and not m.reply_to_message:
        await m.reply("❌ .spam <jumlah> <pesan>")
        return
    try:
        count = min(int(m.command[1]), 30)
    except:
        await m.reply("❌ jumlah harus angka")
        return
    text = None
    if m.reply_to_message:
        text = m.reply_to_message.text or m.reply_to_message.caption
    else:
        text = ' '.join(m.command[2:])
    if not text:
        await m.reply("❌ teks kosong")
        return
    await m.delete()
    for i in range(count):
        await c.send_message(m.chat.id, text)
        await asyncio.sleep(0.2)

# ============== AUTO REPLY HANDLER ==============

async def auto_reply_handler(c, m):
    if not m.from_user or m.from_user.is_bot or m.sender_chat:
        return
    if m.text and m.text.startswith('.'):
        return
    if m.from_user.id in GBAN:
        try: await c.block_user(m.from_user.id)
        except: pass
        return
    if AFK_MODE and m.chat.type == ChatType.PRIVATE:
        uid = m.from_user.id
        if uid in AFK_APPROVED:
            await m.reply(dark_reply())
            return
        if uid in AFK_PENDING and AFK_PENDING[uid].get("blocked"):
            return
        if uid not in AFK_PENDING:
            AFK_PENDING[uid] = {"count": 0, "blocked": False}
        AFK_PENDING[uid]["count"] += 1
        cnt = AFK_PENDING[uid]["count"]
        if cnt >= 5:
            if not AFK_PENDING[uid]["blocked"]:
                try:
                    await c.block_user(uid)
                    AFK_PENDING[uid]["blocked"] = True
                    await m.reply("💀 SPAM! LO KENA BLOKIR")
                except: pass
            return
        if cnt >= 3 and not AFK_PENDING[uid].get("warned"):
            AFK_PENDING[uid]["warned"] = True
            await m.reply("⚠️ JANGAN SPAM ATAU LO KENA BLOK")
            return
        await m.reply(AFK_TEXT)
        return
    if m.chat.type == ChatType.PRIVATE:
        await m.reply(dark_reply())
        return
    if m.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        if m.chat.id not in WHITELIST or m.chat.id in BLACKLIST:
            return
        me = await c.get_me()
        if me.username and m.text and f"@{me.username.lower()}" in m.text.lower():
            await m.reply(dark_reply())
            return
        await m.reply(dark_reply())

# ============== FLASK KEEP ALIVE ==============

@app_flask.route("/")
def index():
    return "💀 THE TAMERS IS RUNNING 💀", 200

def run_flask():
    port = int(os.getenv("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port, threaded=True)

# ============== MAIN ==============

async def main():
    global BLACKLIST, WHITELIST, GBAN
    BLACKLIST = load_json(BLACKLIST_FILE, set())
    WHITELIST = load_json(WHITELIST_FILE, set())
    GBAN = load_json(GBAN_FILE, set())
    
    print("═" * 30)
    print("💀 THE TAMERS v2.0 DARK EDITION")
    print("═" * 30)
    print(f"🔥 GBAN: {len(GBAN)} users")
    print(f"🚫 BLACKLIST: {len(BLACKLIST)} groups")
    print(f"✅ WHITELIST: {len(WHITELIST)} groups")
    print("🌐 RUNNING ON RAILWAY")
    print("")
    
    if not SESSION_STRING:
        print("❌ SESSION_STRING TIDAK ADA!")
        print("📌 SET ENVIRONMENT VARIABLE SESSION_STRING")
        return
    
    client = Client("tamers", session_string=SESSION_STRING, api_id=API_ID, api_hash=API_HASH)
    
    await client.start()
    me = await client.get_me()
    print(f"✅ LOGIN: {me.first_name} (@{me.username if me.username else '-'})")
    print(f"🆔 ID: {me.id}")
    print("")
    
    # COMMANDS
    @client.on_message(filters.me & filters.command("ping", prefixes="."))
    async def _(c, m): await cmd_ping(c, m)
    
    @client.on_message(filters.me & filters.command("status", prefixes="."))
    async def _(c, m): await cmd_status(c, m)
    
    @client.on_message(filters.me & filters.command("info", prefixes="."))
    async def _(c, m): await cmd_info(c, m)
    
    @client.on_message(filters.me & filters.command("afk", prefixes="."))
    async def _(c, m): await cmd_afk(c, m)
    
    @client.on_message(filters.me & filters.command("unafk", prefixes="."))
    async def _(c, m): await cmd_unafk(c, m)
    
    @client.on_message(filters.me & filters.command("acc", prefixes="."))
    async def _(c, m): await cmd_approve(c, m)
    
    @client.on_message(filters.me & filters.command("reject", prefixes="."))
    async def _(c, m): await cmd_reject(c, m)
    
    @client.on_message(filters.me & filters.command("addbl", prefixes="."))
    async def _(c, m): await cmd_addbl(c, m)
    
    @client.on_message(filters.me & filters.command("rmbl", prefixes="."))
    async def _(c, m): await cmd_rmbl(c, m)
    
    @client.on_message(filters.me & filters.command("grup on", prefixes="."))
    async def _(c, m): await cmd_grupon(c, m)
    
    @client.on_message(filters.me & filters.command("grup off", prefixes="."))
    async def _(c, m): await cmd_grupoff(c, m)
    
    @client.on_message(filters.me & filters.command("gban", prefixes="."))
    async def _(c, m): await cmd_gban(c, m)
    
    @client.on_message(filters.me & filters.command("ungban", prefixes="."))
    async def _(c, m): await cmd_ungban(c, m)
    
    @client.on_message(filters.me & filters.command("gcast", prefixes="."))
    async def _(c, m): await cmd_gcast(c, m)
    
    @client.on_message(filters.me & filters.command("ucast_all", prefixes="."))
    async def _(c, m): await cmd_ucast(c, m)
    
    @client.on_message(filters.me & filters.command("spam", prefixes="."))
    async def _(c, m): await cmd_spam(c, m)
    
    @client.on_message(filters.incoming & ~filters.me)
    async def _(c, m): await auto_reply_handler(c, m)
    
    print("🔥 ALL COMMANDS LOADED")
    print("💀 THE TAMERS IS UNSTOPPABLE")
    print("📌 PRESS Ctrl+C TO STOP")
    print("")
    
    while True:
        await asyncio.sleep(60)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 💀 ALIVE AND DEADLY")

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n💀 THE TAMERS WILL RETURN...")
