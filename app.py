"""
THE TAMERS USERBOT v2.0 - RAILWAY EDITION
Udah pake string session, ga butuh file .session lagi tai
"""

import sys
import warnings
import logging
import asyncio
import random
import json
import os
import re
import threading
import time
import ctypes
from datetime import datetime
from typing import Set
from flask import Flask, request

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, PeerIdInvalid, SessionRevoked
from pyrogram.types import Message
from pyrogram.enums import ChatType

# =============================================
# MATIKAN SEMUA LOG YANG GAK PENTING
# =============================================
warnings.filterwarnings("ignore")
logging.getLogger("pyrogram").setLevel(logging.CRITICAL)
logging.getLogger("pyrogram.client").setLevel(logging.CRITICAL)
logging.getLogger("pyrogram.session").setLevel(logging.CRITICAL)
logging.getLogger("pyrogram.dispatcher").setLevel(logging.CRITICAL)
logging.getLogger("pyrogram.connection").setLevel(logging.CRITICAL)
logging.getLogger("pyrogram.storage").setLevel(logging.CRITICAL)
logging.getLogger("asyncio").setLevel(logging.CRITICAL)
logging.getLogger("werkzeug").setLevel(logging.CRITICAL)

# =============================================
# KONFIGURASI
# =============================================
API_ID = 32584214
API_HASH = "6a59dd69d7e9db9916ff9c07eb237076"
BLACKLIST_FILE = "blacklist.json"
SETTINGS_FILE = "settings.json"
WHITELIST_FILE = "whitelist.json"
GBAN_LIST_FILE = "gban_list.json"
BOT_START_TIME = time.time()
BRAND = "THE TAMERS"
VERSION = "2.0.0"

# Flask app
app_flask = Flask(__name__)

# Client global
client = None

# =============================================
# DATA GLOBAL
# =============================================
BLOCKED_GROUPS = set()
WHITELIST_GROUPS = set()
settings = {}
is_afk = False
afk_pending_users = {}
afk_approved_users = set()
GBAN_USERS = set()

# =============================================
# SIMPLE REPLIES
# =============================================
SIMPLE_REPLIES = [
    "hmm 💀", "ya 💀", "Y 💀", "iyaaa 💀", "oke 💀",
    "hmm 🦴", "ya 🐍", "Y 🔥", "iyaaa ☠️", "oke 👻",
    "hmm 🕷️", "ya ⚰️", "Y 🕸️", "iyaaa 🦇", "oke 🔪",
    "hmm 🧛", "ya 🧟", "Y 👹", "iyaaa 😈", "oke 🎃",
]
MENTION_REPLIES = ["hmm? 💀", "ya? 🦴", "iyeee? ☠️", "ada apa? 👻", "💀?", "👹?"]
AFK_REPLY = "💀 **THE TAMERS** sedang AFK, sabar takut nanti kena kutukan! 🦴"

def get_simple_reply():
    return random.choice(SIMPLE_REPLIES)

def get_mention_reply():
    return random.choice(MENTION_REPLIES)

# =============================================
# THE TAMERS STYLE
# =============================================
def title_bar(text, icon="💀"):
    return f"{icon} {text} {icon}"

def info_line(label, value, icon="┃"):
    return f"{icon} {label}: {value}"

def get_uptime():
    elapsed = time.time() - BOT_START_TIME
    days = int(elapsed // 86400)
    hours = int((elapsed % 86400) // 3600)
    mins = int((elapsed % 3600) // 60)
    secs = int(elapsed % 60)
    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {mins}m"
    elif mins > 0:
        return f"{mins}m {secs}s"
    return f"{secs}s"

def progress_bar(current, total, width=12):
    if total == 0:
        return f"[{'░'*width}] 0%"
    persen = int(current / total * 100)
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {persen}%"

# =============================================
# MANAJEMEN DATA
# =============================================
def load_blacklist():
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, "r") as f:
                return set(json.load(f).get("blacklisted_groups", []))
        except:
            pass
    return set()

def save_blacklist(blacklist):
    with open(BLACKLIST_FILE, "w") as f:
        json.dump({"blacklisted_groups": list(blacklist)}, f, indent=4)

def load_whitelist():
    if os.path.exists(WHITELIST_FILE):
        try:
            with open(WHITELIST_FILE, "r") as f:
                return set(json.load(f).get("whitelisted_groups", []))
        except:
            pass
    return set()

def save_whitelist(whitelist):
    with open(WHITELIST_FILE, "w") as f:
        json.dump({"whitelisted_groups": list(whitelist)}, f, indent=4)

def load_settings():
    default = {"auto_reply_group": True, "auto_reply_private": True}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                for k, v in default.items():
                    if k not in data:
                        data[k] = v
                return data
        except:
            pass
    return default

def save_settings(settings_dict):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings_dict, f, indent=4)

def load_gban_list():
    if os.path.exists(GBAN_LIST_FILE):
        try:
            with open(GBAN_LIST_FILE, "r") as f:
                return set(json.load(f).get("gban_users", []))
        except:
            pass
    return set()

def save_gban_list(gban_set):
    with open(GBAN_LIST_FILE, "w") as f:
        json.dump({"gban_users": list(gban_set)}, f, indent=4)

# =============================================
# COMMAND: PING
# =============================================
async def cmd_ping(client, message):
    start = time.time()
    await asyncio.sleep(0.05)
    ping = int((time.time() - start) * 1000)
    me = await client.get_me()
    
    if ping < 50:
        status = "🟢 OVERPOWER"
    elif ping < 150:
        status = "🟡 NORMAL"
    elif ping < 300:
        status = "🟠 SLOW"
    else:
        status = "🔴 WEAK"
    
    reply = f"""
{title_bar("PING", "💀")}
{info_line("Response", f"{ping} ms", "┃")}
{info_line("Status", status, "┃")}
{info_line("Uptime", get_uptime(), "┃")}
{info_line("Owner", me.first_name, "┃")}
{info_line("ID", me.id, "┃")}
{BRAND} 🦴
"""
    await message.reply(reply)

# =============================================
# COMMAND: STATUS
# =============================================
async def cmd_status(client, message):
    me = await client.get_me()
    total_users = 0
    total_groups = 0
    total_channels = 0
    
    async for dialog in client.get_dialogs():
        if dialog.chat.type == ChatType.PRIVATE and dialog.chat.id > 0:
            total_users += 1
        elif dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            total_groups += 1
        elif dialog.chat.type == ChatType.CHANNEL:
            total_channels += 1
    
    reply = f"""
{title_bar("STATUS", "📊")}
{info_line("Owner", me.first_name, "👑")}
{info_line("Username", f"@{me.username}" if me.username else "-", "📱")}
{info_line("ID", me.id, "🆔")}
{info_line("Private", f"{total_users} chats", "👤")}
{info_line("Groups", f"{total_groups} groups", "👥")}
{info_line("Channels", f"{total_channels} channels", "📢")}
{info_line("Uptime", get_uptime(), "⏱️")}
{info_line("Blacklist", f"{len(BLOCKED_GROUPS)} groups", "🚫")}
{info_line("Auto Reply", "ON" if settings.get('auto_reply_private', True) else "OFF", "🤖")}
{BRAND} v{VERSION} 🦴
"""
    await message.reply(reply)

# =============================================
# COMMAND: INFO
# =============================================
async def cmd_info(client, message):
    me = await client.get_me()
    nama = me.first_name + (f" {me.last_name}" if me.last_name else "")
    is_premium = "✅ Yes" if getattr(me, 'is_premium', False) else "❌ No"
    afk_status = "🔴 AFK" if is_afk else "🟢 Active"
    
    reply = f"""
{title_bar("USER INFO", "👤")}
{info_line("Name", nama, "📛")}
{info_line("Username", f"@{me.username}" if me.username else "-", "📱")}
{info_line("ID", me.id, "🆔")}
{info_line("Premium", is_premium, "💎")}
{info_line("Bot Status", afk_status, "🎯")}
{info_line("Version", f"v{VERSION}", "📌")}
{info_line("Uptime", get_uptime(), "⏱️")}
{BRAND} 🦴
"""
    await message.reply(reply)

# =============================================
# COMMAND: AFK & UNAFK
# =============================================
async def cmd_afk(client, message):
    global is_afk
    is_afk = True
    await message.reply(f"{title_bar('AFK MODE', '😴')}\n{info_line('Status', 'AFK ACTIVE', '┃')}\n💀 I'm away! Type .unafk to back\n{BRAND} 🦴")

async def cmd_unafk(client, message):
    global is_afk
    is_afk = False
    await message.reply(f"{title_bar('AFK MODE', '✅')}\n{info_line('Status', 'BACK ONLINE', '┃')}\n{info_line('Duration', get_uptime(), '⏰')}\n👋 I'm back!\n{BRAND} 🦴")

# =============================================
# COMMAND: GCAST
# =============================================
async def cmd_gcast(client, message):
    pesan = None
    
    if message.reply_to_message:
        if message.reply_to_message.text:
            pesan = message.reply_to_message.text
        elif message.reply_to_message.caption:
            pesan = message.reply_to_message.caption
        else:
            pesan = "⚠️ No text found"
    elif len(message.command) > 1:
        pesan = message.text.split(maxsplit=1)[1]
    else:
        await message.reply(f"{title_bar('ERROR', '❌')}\n.gcast <pesan> atau reply ke pesan")
        return
    
    if not pesan:
        await message.reply("❌ Pesan kosong!")
        return
    
    try:
        await message.delete()
    except:
        pass
    
    total = 0
    async for dialog in client.get_dialogs():
        if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] and dialog.chat.id not in BLOCKED_GROUPS:
            total += 1
    
    if total == 0:
        await client.send_message(message.chat.id, "❌ Gak ada grup!")
        return
    
    task_id = random.randint(1000, 9999)
    start_time = time.time()
    
    status_msg = await client.send_message(
        message.chat.id,
        f"{title_bar('GCAST', '📢')}\nTask: #{task_id}\nTarget: {total} groups\n{progress_bar(0, total)}\nProcessing..."
    )
    
    berhasil = 0
    gagal = 0
    processed = 0
    
    async for dialog in client.get_dialogs():
        chat = dialog.chat
        if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] and chat.id not in BLOCKED_GROUPS:
            try:
                await client.send_message(chat.id, pesan)
                berhasil += 1
            except Exception as e:
                gagal += 1
            
            processed += 1
            if processed % 5 == 0 or processed == total:
                await status_msg.edit(
                    f"{title_bar('GCAST', '📢')}\nTask: #{task_id}\nTarget: {total} groups\n{progress_bar(processed, total)}\n✅ {berhasil} | ❌ {gagal}\n{processed}/{total}"
                )
            await asyncio.sleep(0.3)
    
    elapsed = int(time.time() - start_time)
    success_rate = int(berhasil / total * 100) if total > 0 else 0
    
    await status_msg.edit(
        f"{title_bar('GCAST DONE', '✅')}\nTask: #{task_id}\nDuration: {elapsed}s\n✅ Success: {berhasil}\n❌ Failed: {gagal}\n📊 Rate: {success_rate}%\n{BRAND} 🦴"
    )

# =============================================
# COMMAND: UCAST_ALL
# =============================================
async def cmd_ucast_all(client, message):
    pesan = None
    
    if message.reply_to_message:
        if message.reply_to_message.text:
            pesan = message.reply_to_message.text
        elif message.reply_to_message.caption:
            pesan = message.reply_to_message.caption
        else:
            pesan = "⚠️ No text found"
    elif len(message.command) > 1:
        pesan = message.text.split(maxsplit=1)[1]
    else:
        await message.reply(f"{title_bar('ERROR', '❌')}\n.ucast_all <pesan> atau reply ke pesan")
        return
    
    if not pesan:
        await message.reply("❌ Pesan kosong!")
        return
    
    try:
        await message.delete()
    except:
        pass
    
    total = 0
    async for dialog in client.get_dialogs():
        if dialog.chat.type == ChatType.PRIVATE and dialog.chat.id > 0:
            total += 1
    
    if total == 0:
        await client.send_message(message.chat.id, "❌ Gak ada private chat!")
        return
    
    task_id = random.randint(1000, 9999)
    start_time = time.time()
    
    status_msg = await client.send_message(
        message.chat.id,
        f"{title_bar('UCAST', '📨')}\nTask: #{task_id}\nTarget: {total} users\n{progress_bar(0, total)}\nProcessing..."
    )
    
    berhasil = 0
    gagal = 0
    diblokir = 0
    processed = 0
    
    async for dialog in client.get_dialogs():
        if dialog.chat.type == ChatType.PRIVATE and dialog.chat.id > 0:
            try:
                await client.send_message(dialog.chat.id, pesan)
                berhasil += 1
            except UserIsBlocked:
                diblokir += 1
                gagal += 1
            except:
                gagal += 1
            
            processed += 1
            if processed % 5 == 0 or processed == total:
                await status_msg.edit(
                    f"{title_bar('UCAST', '📨')}\nTask: #{task_id}\nTarget: {total} users\n{progress_bar(processed, total)}\n✅ {berhasil} | ❌ {gagal} | 🚫 {diblokir}\n{processed}/{total}"
                )
            await asyncio.sleep(0.5)
    
    elapsed = int(time.time() - start_time)
    success_rate = int(berhasil / total * 100) if total > 0 else 0
    
    await status_msg.edit(
        f"{title_bar('UCAST DONE', '✅')}\nTask: #{task_id}\nDuration: {elapsed}s\n✅ Success: {berhasil}\n❌ Failed: {gagal}\n🚫 Blocked: {diblokir}\n📊 Rate: {success_rate}%\n{BRAND} 🦴"
    )

# =============================================
# COMMAND: SPAM
# =============================================
async def cmd_spam(client, message):
    if len(message.command) < 3 and not message.reply_to_message:
        await message.reply(f"{title_bar('ERROR', '❌')}\n.spam <jumlah> <pesan>")
        return
    
    try:
        count = min(int(message.command[1]), 50)
    except:
        await message.reply("❌ Jumlah harus angka!")
        return
    
    if message.reply_to_message:
        teks = message.reply_to_message.text or message.reply_to_message.caption
    else:
        teks = ' '.join(message.command[2:])
    
    if not teks:
        await message.reply("❌ Teks kosong!")
        return
    
    status = await message.reply(f"{title_bar('SPAM', '🔄')}\nTarget: {count} messages\n{progress_bar(0, count)}\nSending...")
    await message.delete()
    
    for i in range(count):
        await client.send_message(message.chat.id, teks)
        await asyncio.sleep(0.3)
        
        if (i + 1) % 5 == 0 or (i + 1) == count:
            await status.edit(f"{title_bar('SPAM', '🔄')}\nTarget: {count} messages\n{progress_bar(i + 1, count)}\nSending...")
    
    await status.edit(f"{title_bar('SPAM DONE', '✅')}\nSent {count} messages!\n{BRAND} 🦴")

# =============================================
# COMMAND LAINNYA
# =============================================
async def cmd_approve(client, message):
    global afk_pending_users, afk_approved_users
    target_id, target_name = None, None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        inp = message.command[1]
        try:
            target_id = int(inp)
            user = await client.get_users(target_id)
            target_name = user.first_name
        except:
            if not inp.startswith('@'):
                inp = '@' + inp
            try:
                user = await client.get_users(inp)
                target_id, target_name = user.id, user.first_name
            except:
                await message.reply(f"❌ Gak nemu: {inp}")
                return
    
    if not target_id:
        await message.reply("❌ `.acc @username` atau reply")
        return
    
    afk_approved_users.add(target_id)
    afk_pending_users.pop(target_id, None)
    try:
        await client.unblock_user(target_id)
    except:
        pass
    
    await message.reply(f"{title_bar('APPROVED', '✅')}\nUser {target_name} has been approved!")

async def cmd_reject(client, message):
    global afk_pending_users, afk_approved_users
    target_id, target_name = None, None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        inp = message.command[1]
        try:
            target_id = int(inp)
            user = await client.get_users(target_id)
            target_name = user.first_name
        except:
            if not inp.startswith('@'):
                inp = '@' + inp
            try:
                user = await client.get_users(inp)
                target_id, target_name = user.id, user.first_name
            except:
                await message.reply(f"❌ Gak nemu: {inp}")
                return
    
    if not target_id:
        await message.reply("❌ `.reject @username` atau reply")
        return
    
    try:
        await client.block_user(target_id)
    except:
        pass
    
    afk_pending_users.pop(target_id, None)
    afk_approved_users.discard(target_id)
    await message.reply(f"{title_bar('REJECTED', '🚫')}\nUser {target_name} has been blocked!")

async def cmd_afklist(client, message):
    if not afk_pending_users:
        await message.reply(f"{title_bar('AFK PENDING', '📋')}\nNo pending users")
        return
    
    lines = []
    for uid, data in list(afk_pending_users.items())[:20]:
        try:
            user = await client.get_users(uid)
            name = user.first_name
            warned = "⚠️" if data.get("warned", False) else "○"
            lines.append(f"{warned} {name} - {data['count']}/5")
        except:
            lines.append(f"○ User {uid}")
    
    await message.reply(f"{title_bar('AFK PENDING', '📋')}\n" + "\n".join(lines) + f"\nUse .acc @user to approve")

async def cmd_unblock_user(client, message):
    target_id, target_name = None, None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        inp = message.command[1]
        try:
            target_id = int(inp)
            user = await client.get_users(target_id)
            target_name = user.first_name
        except:
            if not inp.startswith('@'):
                inp = '@' + inp
            try:
                user = await client.get_users(inp)
                target_id, target_name = user.id, user.first_name
            except:
                await message.reply(f"❌ Gak nemu: {inp}")
                return
    
    if not target_id:
        await message.reply("❌ `.unblock @username` atau reply")
        return
    
    try:
        await client.unblock_user(target_id)
        await message.reply(f"{title_bar('UNBLOCKED', '✅')}\nUser {target_name} has been unblocked!")
        afk_pending_users.pop(target_id, None)
        afk_approved_users.discard(target_id)
    except Exception as e:
        await message.reply(f"❌ Gagal: {e}")

async def cmd_addbl(client, message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Ketik di grup!")
        return
    gid, title = message.chat.id, message.chat.title or "Grup"
    if gid in BLOCKED_GROUPS:
        await message.reply(f"⚠️ {title} udah diblacklist")
        return
    BLOCKED_GROUPS.add(gid)
    save_blacklist(BLOCKED_GROUPS)
    await message.reply(f"{title_bar('BLACKLISTED', '🚫')}\n{title} added to blacklist!")

async def cmd_rmbl(client, message):
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Ketik di grup!")
        return
    gid, title = message.chat.id, message.chat.title or "Grup"
    if gid not in BLOCKED_GROUPS:
        await message.reply(f"⚠️ {title} gak di blacklist")
        return
    BLOCKED_GROUPS.remove(gid)
    save_blacklist(BLOCKED_GROUPS)
    await message.reply(f"{title_bar('REMOVED', '✅')}\n{title} removed from blacklist!")

async def cmd_listbl(client, message):
    if not BLOCKED_GROUPS:
        await message.reply(f"{title_bar('BLACKLIST', '📋')}\nNo blacklisted groups")
        return
    lines = []
    for gid in list(BLOCKED_GROUPS)[:20]:
        try:
            chat = await client.get_chat(gid)
            lines.append(f"▸ {chat.title}")
        except:
            lines.append(f"▸ ID: {gid}")
    await message.reply(f"{title_bar('BLACKLIST', '📋')}\nTotal: {len(BLOCKED_GROUPS)}\n" + "\n".join(lines))

async def cmd_grup_on(client, message):
    global WHITELIST_GROUPS
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Ketik di grup!")
        return
    cid, title = message.chat.id, message.chat.title or "Grup"
    WHITELIST_GROUPS.add(cid)
    save_whitelist(WHITELIST_GROUPS)
    await message.reply(f"{title_bar('AUTO REPLY', '✅')}\nAuto reply ENABLED in {title}")

async def cmd_grup_off(client, message):
    global WHITELIST_GROUPS
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Ketik di grup!")
        return
    cid, title = message.chat.id, message.chat.title or "Grup"
    WHITELIST_GROUPS.discard(cid)
    save_whitelist(WHITELIST_GROUPS)
    await message.reply(f"{title_bar('AUTO REPLY', '❌')}\nAuto reply DISABLED in {title}")

async def cmd_private_on(client, message):
    settings["auto_reply_private"] = True
    save_settings(settings)
    await message.reply(f"{title_bar('PRIVATE AUTO REPLY', '✅')}\nPrivate auto reply is ON")

async def cmd_private_off(client, message):
    settings["auto_reply_private"] = False
    save_settings(settings)
    await message.reply(f"{title_bar('PRIVATE AUTO REPLY', '❌')}\nPrivate auto reply is OFF")

async def cmd_list_whitelist(client, message):
    if not WHITELIST_GROUPS:
        await message.reply(f"{title_bar('AUTO REPLY GROUPS', '📋')}\nNo groups enabled")
        return
    lines = []
    for gid in list(WHITELIST_GROUPS)[:30]:
        try:
            chat = await client.get_chat(gid)
            lines.append(f"▸ {chat.title}")
        except:
            lines.append(f"▸ ID: {gid}")
    await message.reply(f"{title_bar('AUTO REPLY GROUPS', '📋')}\nTotal: {len(WHITELIST_GROUPS)}\n" + "\n".join(lines))

# =============================================
# GBAN ULTIMATE
# =============================================
async def report_to_spambot(client, user_id):
    try:
        await client.send_message("SpamBot", f"/report {user_id} spam")
        await asyncio.sleep(1)
        return True
    except:
        return False

async def report_impersonation(client, user_id):
    try:
        await client.send_message("SpamBot", f"/report {user_id} impersonation")
        await asyncio.sleep(1)
        return True
    except:
        return False

async def block_user_everywhere_silent(client, user_id):
    blocked_count = 0
    try:
        await client.block_user(user_id)
        blocked_count += 1
        async for dialog in client.get_dialogs():
            if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                try:
                    await dialog.chat.ban_member(user_id)
                    blocked_count += 1
                    await asyncio.sleep(0.2)
                except:
                    pass
    except:
        pass
    return blocked_count

async def cmd_gban(client, message):
    global GBAN_USERS
    
    target_id = None
    target_name = None
    target_username = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
        target_username = message.reply_to_message.from_user.username
    elif len(message.command) > 1:
        inp = message.command[1]
        try:
            target_id = int(inp)
            user = await client.get_users(target_id)
            target_name = user.first_name
            target_username = user.username
        except:
            if not inp.startswith('@'):
                inp = '@' + inp
            try:
                user = await client.get_users(inp)
                target_id = user.id
                target_name = user.first_name
                target_username = user.username
            except:
                await message.reply(f"❌ Gak nemu: {inp}")
                return
    
    if not target_id:
        await message.reply("❌ `.gban @username` atau reply")
        return
    
    me = await client.get_me()
    if target_id == me.id:
        await message.reply("❌ Mau gban diri sendiri? Goblok! 💀")
        return
    
    if target_id in GBAN_USERS:
        await message.reply(f"⚠️ {target_name} udah kena GBAN!")
        return
    
    status_msg = await message.reply(f"{title_bar('GBAN', '🔥')}\nTarget: {target_name}\nMode: SILENT\n{progress_bar(0, 3)}\nProcessing...")
    
    report_spam = await report_to_spambot(client, target_id)
    await status_msg.edit(f"{title_bar('GBAN', '🔥')}\nTarget: {target_name}\n✅ Spam report {'✓' if report_spam else '✗'}\n{progress_bar(1, 3)}")
    
    report_imp = await report_impersonation(client, target_id)
    await status_msg.edit(f"{title_bar('GBAN', '🔥')}\nTarget: {target_name}\n✅ Spam report {'✓' if report_spam else '✗'}\n✅ Impersonation {'✓' if report_imp else '✗'}\n{progress_bar(2, 3)}")
    
    block_count = await block_user_everywhere_silent(client, target_id)
    
    GBAN_USERS.add(target_id)
    save_gban_list(GBAN_USERS)
    
    await status_msg.edit(
        f"{title_bar('GBAN DONE', '✅')}\nTarget: {target_name}\nID: {target_id}\n"
        f"📋 Spam: {'✓' if report_spam else '✗'}\n"
        f"🎭 Impersonation: {'✓' if report_imp else '✗'}\n"
        f"🚫 Silent block: {block_count} locations\n"
        f"💀 Target does NOT know!\n{BRAND} 🦴"
    )

async def cmd_ungban(client, message):
    global GBAN_USERS
    
    target_id = None
    target_name = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        inp = message.command[1]
        try:
            target_id = int(inp)
            user = await client.get_users(target_id)
            target_name = user.first_name
        except:
            if not inp.startswith('@'):
                inp = '@' + inp
            try:
                user = await client.get_users(inp)
                target_id = user.id
                target_name = user.first_name
            except:
                await message.reply(f"❌ Gak nemu: {inp}")
                return
    
    if not target_id:
        await message.reply("❌ `.ungban @username` atau reply")
        return
    
    if target_id not in GBAN_USERS:
        await message.reply(f"⚠️ {target_name} gak ada di GBAN list!")
        return
    
    GBAN_USERS.discard(target_id)
    save_gban_list(GBAN_USERS)
    
    try:
        await client.unblock_user(target_id)
    except:
        pass
    
    await message.reply(f"{title_bar('UNGBAN', '✅')}\nUser {target_name} removed from GBAN list!")

async def cmd_listgban(client, message):
    if not GBAN_USERS:
        await message.reply(f"{title_bar('GBAN LIST', '📋')}\nNo users GBANNED yet")
        return
    
    user_list = []
    for uid in list(GBAN_USERS)[:30]:
        try:
            user = await client.get_users(uid)
            name = user.first_name
            username = f"@{user.username}" if user.username else "-"
            user_list.append(f"▸ {name} ({username})")
        except:
            user_list.append(f"▸ User ID: {uid}")
    
    await message.reply(f"{title_bar('GBAN LIST', '📋')}\nTotal: {len(GBAN_USERS)}\n" + "\n".join(user_list) + f"\n{BRAND} 🦴")

# =============================================
# HANDLER BALAS OTOMATIS
# =============================================
async def process_incoming_message(client, message):
    global is_afk, afk_pending_users, afk_approved_users, WHITELIST_GROUPS, BLOCKED_GROUPS, GBAN_USERS
    
    if message.text and message.text.startswith('.'):
        return
    if not message.from_user or message.from_user.is_bot or message.chat.type == ChatType.CHANNEL or message.sender_chat:
        return
    
    if message.from_user.id in GBAN_USERS:
        try:
            await client.block_user(message.from_user.id)
        except:
            pass
        return
    
    current_settings = load_settings()
    auto_reply_private = current_settings.get("auto_reply_private", True)
    chat_type = message.chat.type
    
    try:
        if is_afk and chat_type == ChatType.PRIVATE:
            user_id = message.from_user.id
            
            if user_id in afk_approved_users:
                if auto_reply_private:
                    await message.reply(get_simple_reply())
                return
            
            if user_id in afk_pending_users and afk_pending_users[user_id].get("blocked", False):
                return
            
            if user_id not in afk_pending_users:
                afk_pending_users[user_id] = {"count": 0, "warned": False, "blocked": False}
            
            afk_pending_users[user_id]["count"] += 1
            count = afk_pending_users[user_id]["count"]
            
            if count >= 5:
                if not afk_pending_users[user_id].get("blocked", False):
                    try:
                        await client.block_user(user_id)
                        afk_pending_users[user_id]["blocked"] = True
                        await message.reply("💀 SPAM! You have been blocked by THE TAMERS!")
                    except:
                        pass
                return
            
            if count >= 3 and not afk_pending_users[user_id].get("warned", False):
                afk_pending_users[user_id]["warned"] = True
                await message.reply("⚠️ WARNING! Don't spam, or THE TAMERS will block you!")
                return
            
            await message.reply(AFK_REPLY)
            return
        
        if chat_type == ChatType.PRIVATE:
            if auto_reply_private:
                await message.reply(get_simple_reply())
            return
        
        if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            if message.chat.id not in WHITELIST_GROUPS or message.chat.id in BLOCKED_GROUPS:
                return
            
            try:
                me = await client.get_me()
                if me.username and message.text and f"@{me.username.lower()}" in message.text.lower():
                    await message.reply(get_mention_reply())
                    return
            except:
                pass
            
            await message.reply(get_simple_reply())
    
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception as e:
        pass

# =============================================
# FLASK ROUTES (Biar ga kena idle)
# =============================================
@app_flask.route("/", methods=["GET"])
def index():
    return "💀 THE TAMERS USERBOT v2.0 - RUNNING ON RAILWAY 💀", 200

@app_flask.route("/ping", methods=["GET"])
def ping():
    return "pong", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port, threaded=True)

# =============================================
# MAIN
# =============================================
async def main():
    global client, BLOCKED_GROUPS, WHITELIST_GROUPS, settings, GBAN_USERS
    
    # Load data
    BLOCKED_GROUPS = load_blacklist()
    WHITELIST_GROUPS = load_whitelist()
    settings = load_settings()
    GBAN_USERS = load_gban_list()
    
    print("═" * 40)
    print("💀 THE TAMERS v2.0 - RAILWAY EDITION 💀")
    print("═" * 40)
    print(f"📋 GBAN: {len(GBAN_USERS)} victims")
    print(f"🚫 Blacklist: {len(BLOCKED_GROUPS)} groups")
    print(f"✅ Whitelist: {len(WHITELIST_GROUPS)} groups")
    print("🔇 GBAN Mode: SILENT DEATH")
    print("🌐 Platform: RAILWAY")
    print("")
    
    # Pake string session dari environment variable
    session_string = os.getenv("SESSION_STRING")
    
    if session_string:
        print("🔑 Using String Session...")
        client = Client("userbot", session_string=session_string, api_id=API_ID, api_hash=API_HASH)
    else:
        print("❌ SESSION_STRING not found in environment variables!")
        print("📌 Please add SESSION_STRING to Railway Variables")
        return
    
    try:
        await client.start()
        me = await client.get_me()
        print(f"✅ Login: {me.first_name} (@{me.username if me.username else '-'})")
        print(f"👤 Tamer: {me.first_name}")
        print(f"🆔 ID: {me.id}")
        print("")
        
        # Command handlers
        @client.on_message(filters.me & filters.command("ping", prefixes="."))
        async def ping_handler(c, m): await cmd_ping(c, m)
        
        @client.on_message(filters.me & filters.command("status", prefixes="."))
        async def status_handler(c, m): await cmd_status(c, m)
        
        @client.on_message(filters.me & filters.command("info", prefixes="."))
        async def info_handler(c, m): await cmd_info(c, m)
        
        @client.on_message(filters.me & filters.command("afk", prefixes="."))
        async def afk_handler(c, m): await cmd_afk(c, m)
        
        @client.on_message(filters.me & filters.command("unafk", prefixes="."))
        async def unafk_handler(c, m): await cmd_unafk(c, m)
        
        @client.on_message(filters.me & filters.command("acc", prefixes="."))
        async def acc_handler(c, m): await cmd_approve(c, m)
        
        @client.on_message(filters.me & filters.command("reject", prefixes="."))
        async def reject_handler(c, m): await cmd_reject(c, m)
        
        @client.on_message(filters.me & filters.command("afklist", prefixes="."))
        async def afklist_handler(c, m): await cmd_afklist(c, m)
        
        @client.on_message(filters.me & filters.command("unblock", prefixes="."))
        async def unblock_handler(c, m): await cmd_unblock_user(c, m)
        
        @client.on_message(filters.me & filters.command("addbl", prefixes="."))
        async def addbl_handler(c, m): await cmd_addbl(c, m)
        
        @client.on_message(filters.me & filters.command("rmbl", prefixes="."))
        async def rmbl_handler(c, m): await cmd_rmbl(c, m)
        
        @client.on_message(filters.me & filters.command("listbl", prefixes="."))
        async def listbl_handler(c, m): await cmd_listbl(c, m)
        
        @client.on_message(filters.me & filters.command("grup on", prefixes="."))
        async def grupon_handler(c, m): await cmd_grup_on(c, m)
        
        @client.on_message(filters.me & filters.command("grup off", prefixes="."))
        async def grupoff_handler(c, m): await cmd_grup_off(c, m)
        
        @client.on_message(filters.me & filters.command("listgrup", prefixes="."))
        async def listgrup_handler(c, m): await cmd_list_whitelist(c, m)
        
        @client.on_message(filters.me & filters.command("private on", prefixes="."))
        async def privateon_handler(c, m): await cmd_private_on(c, m)
        
        @client.on_message(filters.me & filters.command("private off", prefixes="."))
        async def privateoff_handler(c, m): await cmd_private_off(c, m)
        
        @client.on_message(filters.me & filters.command("gcast", prefixes="."))
        async def gcast_handler(c, m): await cmd_gcast(c, m)
        
        @client.on_message(filters.me & filters.command("ucast_all", prefixes="."))
        async def ucast_handler(c, m): await cmd_ucast_all(c, m)
        
        @client.on_message(filters.me & filters.command("spam", prefixes="."))
        async def spam_handler(c, m): await cmd_spam(c, m)
        
        @client.on_message(filters.me & filters.command("gban", prefixes="."))
        async def gban_handler(c, m): await cmd_gban(c, m)
        
        @client.on_message(filters.me & filters.command("ungban", prefixes="."))
        async def ungban_handler(c, m): await cmd_ungban(c, m)
        
        @client.on_message(filters.me & filters.command("listgban", prefixes="."))
        async def listgban_handler(c, m): await cmd_listgban(c, m)
        
        # Auto reply handler
        @client.on_message(filters.incoming & ~filters.me)
        async def auto_reply_handler(c, m):
            await process_incoming_message(c, m)
        
        print("📌 ALL COMMANDS LOADED!")
        print(f"📌 Bot is RUNNING on Railway!")
        print(f"📌 Press Ctrl+C to stop...")
        print("")
        
        # Keep running
        while True:
            await asyncio.sleep(60)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Bot still alive tai...")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

# =============================================
# RUN
# =============================================
if __name__ == "__main__":
    # Jalanin Flask di thread background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Jalanin bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n💀 THE TAMERS HAS RISEN... Goodbye! 🦴")
