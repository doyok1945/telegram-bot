"""
THE TAMERS USERBOT v5.0 - AUTO MUTE SPAMMER EDITION
Mute otomatis user spam! Gak bakal mute admin!
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
from typing import Set, Dict
from flask import Flask, request
from concurrent.futures import ThreadPoolExecutor

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, PeerIdInvalid, SessionRevoked, RPCError
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ChatType, UserStatus

# =============================================
# MATIKAN SEMUA LOG
# =============================================
warnings.filterwarnings("ignore")
logging.getLogger("pyrogram").setLevel(logging.ERROR)
logging.getLogger("pyrogram.client").setLevel(logging.ERROR)
logging.getLogger("pyrogram.session").setLevel(logging.ERROR)
logging.getLogger("pyrogram.dispatcher").setLevel(logging.ERROR)
logging.getLogger("pyrogram.connection").setLevel(logging.ERROR)
logging.getLogger("pyrogram.storage").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)
logging.getLogger("werkzeug").setLevel(logging.ERROR)

sys.stderr = open(os.devnull, 'w')

# Flask app
app_flask = Flask(__name__)

# Client global
client = None

# Thread pool
executor = ThreadPoolExecutor(max_workers=10)

# =============================================
# KONFIGURASI
# =============================================
API_ID = 32584214
API_HASH = "6a59dd69d7e9db9916ff9c07eb237076"
BLACKLIST_FILE = "blacklist.json"
SETTINGS_FILE = "settings.json"
WHITELIST_FILE = "whitelist.json"
GBAN_LIST_FILE = "gban_list.json"
SUPERBRUTAL_FILE = "superbrutal_groups.json"
AUTOMUTE_FILE = "automute_groups.json"
BOT_START_TIME = time.time()
BRAND = "THE TAMERS"
VERSION = "5.0.0"

# =============================================
# DATA GLOBAL
# =============================================
BLOCKED_GROUPS = set()
WHITELIST_GROUPS = set()
SUPERBRUTAL_GROUPS = set()
AUTOMUTE_GROUPS = set()  # GRUP YANG AUTO MUTE NYALA
settings = {}
is_afk = False
afk_pending_users = {}
afk_approved_users = set()
GBAN_USERS = set()

# DATA PELACAK SPAM PER USER
spam_counter: Dict[int, Dict[int, int]] = {}  # {group_id: {user_id: count}}
spam_warned: Dict[int, Dict[int, bool]] = {}  # {group_id: {user_id: warned}}
muted_users: Dict[int, Set[int]] = {}  # {group_id: {muted_user_ids}}

# =============================================
# BRUTAL SPAM REPLIES (SEMUA PAKAI 💀 SEKARANG!)
# =============================================
BRUTAL_REPLIES = [
    "💀 **SPAM DETECTED! YOU ARE CURSED!** 💀",
    "💀 **THE TAMERS DON'T TOLERATE SPAM!** 💀",
    "💀 **YOUR MESSAGE IS TRASH! GET LOST!** 💀",
    "💀 **SPAM = INSTANT REPORT + BLOCK!** 💀",
    "💀 **WASTE YOUR TIME ELSEWHERE, SPAMMER!** 💀",
    "💀 **THE TAMERS HAVE SPOKEN: YOU ARE NOTHING!** 💀",
    "💀 **ENJOY YOUR REPORT TO @SpamBot!** 💀",
    "💀 **YOUR ACCOUNT IS MARKED! GOODBYE!** 💀",
    "💀 **SPAMMERS ARE NOT WELCOME HERE!** 💀",
    "💀 **THE TAMERS WILL HAUNT YOUR ACCOUNT!** 💀",
    "💀 **GO F*CK YOURSELF, SPAMMER!** 💀",
    "💀 **YOUR IP HAS BEEN LOGGED!** 💀",
    "💀 **SAY GOODBYE TO YOUR TELEGRAM ACCOUNT!** 💀",
    "💀 **THE TAMERS ARE WATCHING YOU!** 💀",
    "💀 **SPAM = AUTOMATIC MUTE!** 💀",
    "💀 **YOU'VE BEEN MARKED BY THE TAMERS!** 💀",
    "💀 **YOUR MESSAGE IS WORTHLESS!** 💀",
    "💀 **GET REKT SPAMMER!** 💀",
    "💀 **THE TAMERS NEVER SLEEP!** 💀",
    "💀 **SPAM = BANNED FOREVER!** 💀",
    "💀 **AUTO MUTE ACTIVATED!** 💀",
    "💀 **YOU ARE MUTED NOW!** 💀",
]

SIMPLE_REPLIES = [
    "hmm 💀", "ya 💀", "Y 💀", "iyaaa 💀", "oke 💀",
    "hmm 💀", "ya 💀", "Y 💀", "iyaaa 💀", "oke 💀",
    "hmm 💀", "ya 💀", "Y 💀", "iyaaa 💀", "oke 💀",
]
MENTION_REPLIES = ["hmm? 💀", "ya? 💀", "iyeee? 💀", "ada apa? 💀", "💀?", "💀?"]
AFK_REPLY = "💀 **THE TAMERS** sedang AFK, sabar takut nanti kena kutukan! 💀"

def get_brutal_reply():
    return random.choice(BRUTAL_REPLIES)

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

def load_superbrutal_groups():
    if os.path.exists(SUPERBRUTAL_FILE):
        try:
            with open(SUPERBRUTAL_FILE, "r") as f:
                return set(json.load(f).get("superbrutal_groups", []))
        except:
            pass
    return set()

def save_superbrutal_groups(groups):
    with open(SUPERBRUTAL_FILE, "w") as f:
        json.dump({"superbrutal_groups": list(groups)}, f, indent=4)

def load_automute_groups():
    if os.path.exists(AUTOMUTE_FILE):
        try:
            with open(AUTOMUTE_FILE, "r") as f:
                return set(json.load(f).get("automute_groups", []))
        except:
            pass
    return set()

def save_automute_groups(groups):
    with open(AUTOMUTE_FILE, "w") as f:
        json.dump({"automute_groups": list(groups)}, f, indent=4)

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
# AUTO MUTE FUNCTIONS (FIX VERSION)
# =============================================

async def is_admin(client, chat_id, user_id):
    """Cek apakah user adalah admin di grup"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        admin_statuses = ["administrator", "creator"]
        status = str(member.status).lower() if member.status else ""
        return status in admin_statuses
    except:
        return False

async def mute_user(client, chat_id, user_id, duration=60):
    """Mute user dengan durasi tertentu (detik)"""
    try:
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False
        )
        until_date = datetime.now() + timedelta(seconds=duration)
        await client.restrict_chat_member(chat_id, user_id, permissions, until_date)
        return True
    except Exception as e:
        print(f"Mute error: {e}")
        return False

async def unmute_user(client, chat_id, user_id):
    """Unmute user"""
    try:
        permissions = ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
        await client.restrict_chat_member(chat_id, user_id, permissions)
        return True
    except:
        return False

async def check_and_mute_spammer(client, chat_id, user_id, user_name, message):
    """Cek dan mute spammer jika perlu (FIX VERSION)"""
    global spam_counter, spam_warned, muted_users
    
    if chat_id not in AUTOMUTE_GROUPS:
        return False
    
    # CEK APAKAH USER ADALAH ADMIN (GAK BISA MUTE ADMIN!)
    if await is_admin(client, chat_id, user_id):
        return False
    
    # CEK APAKAH USERBOT ADMIN
    me = await client.get_me()
    bot_is_admin = False
    try:
        bot_member = await client.get_chat_member(chat_id, me.id)
        bot_status = str(bot_member.status).lower() if bot_member.status else ""
        bot_is_admin = bot_status in ["administrator", "creator"]
    except:
        bot_is_admin = False
    
    # Inisialisasi counter
    if chat_id not in spam_counter:
        spam_counter[chat_id] = {}
    if chat_id not in spam_warned:
        spam_warned[chat_id] = {}
    if chat_id not in muted_users:
        muted_users[chat_id] = set()
    
    # Tambah counter spam
    spam_counter[chat_id][user_id] = spam_counter[chat_id].get(user_id, 0) + 1
    count = spam_counter[chat_id][user_id]
    
    # LEVEL 1: PERINGATAN (3-4 pesan)
    if count == 3 and not spam_warned[chat_id].get(user_id, False):
        spam_warned[chat_id][user_id] = True
        if bot_is_admin:
            await message.reply(f"💀 **PERINGATAN!** @{user_name} JANGAN SPAM! Kalo sampai 5x bakal kena MUTE 5 menit! 💀")
        else:
            await message.reply(f"💀 **PERINGATAN!** @{user_name} JANGAN SPAM! (Userbot bukan admin, jadi gak bisa mute) 💀")
        return False
    
    # KALO USERBOT BUKAN ADMIN, STOP DISINI (GAK BISA MUTE)
    if not bot_is_admin:
        # TAPI TETAP HITUNG BUAT PERINGATAN
        if count >= 5:
            await message.reply(f"⚠️ @{user_name} UDAH {count}x SPAM! TAPI USERBOT BUKAN ADMIN JADI GAK BISA MUTE! 💀")
        return False
    
    # LEVEL 2: MUTE 5 MENIT (5-9 pesan)
    if count == 5 and user_id not in muted_users[chat_id]:
        muted_users[chat_id].add(user_id)
        if await mute_user(client, chat_id, user_id, 300):
            await message.reply(f"🔇 **AUTO MUTE!** @{user_name} KENA MUTE 5 MENIT KARENA SPAM! 💀")
        else:
            await message.reply(f"⚠️ GAGAL MUTE! Pastikan userbot punya hak 'Restrict Members'! 💀")
        spam_counter[chat_id][user_id] = 0
        return True
    
    # LEVEL 3: MUTE 30 MENIT (10-14 pesan)
    if count == 10 and user_id in muted_users[chat_id]:
        if await mute_user(client, chat_id, user_id, 1800):
            await message.reply(f"🔇 **MUTE DIPERPANJANG!** @{user_name} KENA MUTE 30 MENIT! 💀")
        spam_counter[chat_id][user_id] = 0
        return True
    
    # LEVEL 4: MUTE 1 JAM (15+ pesan)
    if count >= 15:
        if await mute_user(client, chat_id, user_id, 3600):
            await message.reply(f"🔇 **MUTE TOTAL!** @{user_name} KENA MUTE 1 JAM! GOBLOK BANGET! 💀")
        spam_counter[chat_id][user_id] = 0
        return True
    
    return False

# =============================================
# COMMAND: PING, STATUS, INFO
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
    
    await message.reply(f"{title_bar('PING', '💀')}\n{info_line('Response', f'{ping} ms', '┃')}\n{info_line('Status', status, '┃')}\n{info_line('Uptime', get_uptime(), '┃')}\n{BRAND} 💀")

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
    
    await message.reply(f"""
{title_bar("STATUS", "💀")}
{info_line("Owner", me.first_name, "👑")}
{info_line("ID", me.id, "🆔")}
{info_line("Private", f"{total_users} chats", "👤")}
{info_line("Groups", f"{total_groups} groups", "👥")}
{info_line("Uptime", get_uptime(), "⏱️")}
{info_line("Super Brutal", f"{len(SUPERBRUTAL_GROUPS)} groups", "🔥")}
{info_line("Auto Mute", f"{len(AUTOMUTE_GROUPS)} groups", "🔇")}
{BRAND} v{VERSION} 💀
""")

async def cmd_info(client, message):
    me = await client.get_me()
    nama = me.first_name + (f" {me.last_name}" if me.last_name else "")
    is_premium = "✅ Yes" if getattr(me, 'is_premium', False) else "❌ No"
    await message.reply(f"{title_bar('USER INFO', '👤')}\n{info_line('Name', nama, '📛')}\n{info_line('Username', f'@{me.username}' if me.username else '-', '📱')}\n{info_line('ID', me.id, '🆔')}\n{info_line('Premium', is_premium, '💎')}\n{BRAND} 💀")

async def cmd_afk(client, message):
    global is_afk
    is_afk = True
    await message.reply(f"{title_bar('AFK MODE', '😴')}\n💀 I'm away! Type .unafk to back\n{BRAND} 💀")

async def cmd_unafk(client, message):
    global is_afk
    is_afk = False
    await message.reply(f"{title_bar('AFK MODE', '✅')}\n👋 I'm back!\n{BRAND} 💀")

# =============================================
# COMMAND: SUPER BRUTAL (PER GRUP)
# =============================================
async def cmd_superbrutal_on(client, message):
    global SUPERBRUTAL_GROUPS
    
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Command ini harus diketik di dalam grup!")
        return
    
    chat_id = message.chat.id
    chat_title = message.chat.title or "Grup"
    
    if chat_id in SUPERBRUTAL_GROUPS:
        await message.reply(f"⚠️ Super Brutal already ON in {chat_title}")
        return
    
    SUPERBRUTAL_GROUPS.add(chat_id)
    save_superbrutal_groups(SUPERBRUTAL_GROUPS)
    
    await message.reply(f"""
{title_bar("SUPER BRUTAL", "🔥")}
{info_line("Group", chat_title, "📌")}
{info_line("Status", "ENABLED", "✅")}

💀 EVERY MESSAGE IN THIS GROUP WILL BE REPLIED!
🔥 SPAMMERS WILL BE DESTROYED!
{BRAND} 💀
""")

async def cmd_superbrutal_off(client, message):
    global SUPERBRUTAL_GROUPS
    
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Command ini harus diketik di dalam grup!")
        return
    
    chat_id = message.chat.id
    chat_title = message.chat.title or "Grup"
    
    if chat_id not in SUPERBRUTAL_GROUPS:
        await message.reply(f"⚠️ Super Brutal not active in {chat_title}")
        return
    
    SUPERBRUTAL_GROUPS.discard(chat_id)
    save_superbrutal_groups(SUPERBRUTAL_GROUPS)
    
    await message.reply(f"{title_bar('SUPER BRUTAL', '❌')}\nSuper Brutal DISABLED in {chat_title}\n{BRAND} 💀")

async def cmd_list_superbrutal(client, message):
    if not SUPERBRUTAL_GROUPS:
        await message.reply(f"{title_bar('SUPER BRUTAL LIST', '📋')}\nNo groups with Super Brutal active")
        return
    
    lines = []
    for gid in list(SUPERBRUTAL_GROUPS)[:30]:
        try:
            chat = await client.get_chat(gid)
            lines.append(f"▸ {chat.title}")
        except:
            lines.append(f"▸ ID: {gid}")
    
    await message.reply(f"{title_bar('SUPER BRUTAL LIST', '📋')}\nTotal: {len(SUPERBRUTAL_GROUPS)}\n" + "\n".join(lines) + f"\n{BRAND} 💀")

# =============================================
# COMMAND: AUTO MUTE (PER GRUP - KAYAK GRUP ON)
# =============================================
async def cmd_automute_on(client, message):
    """Aktifin auto mute di grup ini"""
    global AUTOMUTE_GROUPS
    
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Command ini harus diketik di dalam grup!")
        return
    
    chat_id = message.chat.id
    chat_title = message.chat.title or "Grup"
    
    # CEK APAKAH USERBOT JADI ADMIN
    try:
        bot_member = await client.get_chat_member(chat_id, (await client.get_me()).id)
        if bot_member.status not in ["administrator", "creator"]:
            await message.reply(f"""
{title_bar("AUTO MUTE", "❌")}
{info_line("Group", chat_title, "📌")}
{info_line("Status", "FAILED", "⚠️")}

💀 USERBOT HARUS JADI ADMIN DULU GOBLOK!
🔥 Jadikan userbot sebagai admin grup baru bisa auto mute!
{BRAND} 💀
""")
            return
    except:
        await message.reply(f"{title_bar('AUTO MUTE', '❌')}\nGagal cek status admin! Pastikan userbot admin di grup!\n{BRAND} 💀")
        return
    
    if chat_id in AUTOMUTE_GROUPS:
        await message.reply(f"⚠️ Auto Mute already ON in {chat_title}")
        return
    
    AUTOMUTE_GROUPS.add(chat_id)
    save_automute_groups(AUTOMUTE_GROUPS)
    
    await message.reply(f"""
{title_bar("AUTO MUTE", "🔇")}
{info_line("Group", chat_title, "📌")}
{info_line("Status", "ENABLED", "✅")}

💀 AUTO MUTE ACTIVATED!
🔥 Users who spam 5x will be muted for 5 minutes!
💀 Admins are SAFE from auto mute!
{BRAND} 💀
""")

async def cmd_automute_off(client, message):
    """Matiin auto mute di grup ini"""
    global AUTOMUTE_GROUPS
    
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Command ini harus diketik di dalam grup!")
        return
    
    chat_id = message.chat.id
    chat_title = message.chat.title or "Grup"
    
    if chat_id not in AUTOMUTE_GROUPS:
        await message.reply(f"⚠️ Auto Mute not active in {chat_title}")
        return
    
    AUTOMUTE_GROUPS.discard(chat_id)
    save_automute_groups(AUTOMUTE_GROUPS)
    
    await message.reply(f"{title_bar('AUTO MUTE', '❌')}\nAuto Mute DISABLED in {chat_title}\n{BRAND} 💀")

async def cmd_list_automute(client, message):
    """Lihat daftar grup yang auto mute aktif"""
    if not AUTOMUTE_GROUPS:
        await message.reply(f"{title_bar('AUTO MUTE LIST', '📋')}\nNo groups with Auto Mute active")
        return
    
    lines = []
    for gid in list(AUTOMUTE_GROUPS)[:30]:
        try:
            chat = await client.get_chat(gid)
            lines.append(f"▸ {chat.title}")
        except:
            lines.append(f"▸ ID: {gid}")
    
    await message.reply(f"{title_bar('AUTO MUTE LIST', '📋')}\nTotal: {len(AUTOMUTE_GROUPS)}\n" + "\n".join(lines) + f"\n{BRAND} 💀")

async def cmd_unmute(client, message):
    """Unmute user di grup"""
    target_id = None
    target_name = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        inp = message.command[1]
        try:
            target_id = int(inp)
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
        await message.reply("❌ `.unmute @username` atau reply ke pesan user")
        return
    
    chat_id = message.chat.id
    
    if await unmute_user(client, chat_id, target_id):
        await message.reply(f"{title_bar('UNMUTE', '✅')}\nUser {target_name or target_id} has been unmuted!\n{BRAND} 💀")
    else:
        await message.reply(f"❌ Gagal unmute user! Pastikan userbot admin!")
    
    if chat_id in muted_users and target_id in muted_users[chat_id]:
        muted_users[chat_id].discard(target_id)

# =============================================
# COMMAND: WHITELIST & BLACKLIST
# =============================================
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

# =============================================
# COMMAND: GCAST, UCAST, SPAM
# =============================================
async def cmd_gcast(client, message):
    pesan = None
    if message.reply_to_message:
        pesan = message.reply_to_message.text or message.reply_to_message.caption
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
    status_msg = await client.send_message(message.chat.id, f"{title_bar('GCAST', '📢')}\nTask: #{task_id}\nTarget: {total} groups\nProcessing...")
    
    berhasil, gagal = 0, 0
    async for dialog in client.get_dialogs():
        chat = dialog.chat
        if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] and chat.id not in BLOCKED_GROUPS:
            try:
                await client.send_message(chat.id, pesan)
                berhasil += 1
            except:
                gagal += 1
            await asyncio.sleep(0.2)
    
    await status_msg.edit(f"{title_bar('GCAST DONE', '✅')}\n✅ {berhasil} | ❌ {gagal}\n{BRAND} 💀")

async def cmd_ucast_all(client, message):
    pesan = None
    if message.reply_to_message:
        pesan = message.reply_to_message.text or message.reply_to_message.caption
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
    status_msg = await client.send_message(message.chat.id, f"{title_bar('UCAST', '📨')}\nTask: #{task_id}\nTarget: {total} users\nProcessing...")
    
    berhasil, gagal, diblokir = 0, 0, 0
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
            await asyncio.sleep(0.3)
    
    await status_msg.edit(f"{title_bar('UCAST DONE', '✅')}\n✅ {berhasil} | ❌ {gagal} | 🚫 {diblokir}\n{BRAND} 💀")

async def cmd_spam(client, message):
    if len(message.command) < 3 and not message.reply_to_message:
        await message.reply(f"{title_bar('ERROR', '❌')}\n.spam <jumlah> <pesan>")
        return
    
    try:
        count = min(int(message.command[1]), 100)
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
    
    status = await message.reply(f"{title_bar('SPAM', '🔄')}\nSpamming {count} messages...")
    await message.delete()
    
    for i in range(count):
        await client.send_message(message.chat.id, teks)
        await asyncio.sleep(0.1)
    
    await status.edit(f"{title_bar('SPAM DONE', '✅')}\nSent {count} messages!\n{BRAND} 💀")

# =============================================
# COMMAND: GBAN, UNGBAN, LISTGBAN
# =============================================
async def report_to_spambot(client, user_id):
    try:
        await client.send_message("SpamBot", f"/report {user_id} spam")
        await asyncio.sleep(0.5)
        return True
    except:
        return False

async def report_impersonation(client, user_id):
    try:
        await client.send_message("SpamBot", f"/report {user_id} impersonation")
        await asyncio.sleep(0.5)
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
                    await asyncio.sleep(0.1)
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
    
    status_msg = await message.reply(f"{title_bar('GBAN', '🔥')}\nTarget: {target_name}\nProcessing...")
    
    report_spam = await report_to_spambot(client, target_id)
    report_imp = await report_impersonation(client, target_id)
    block_count = await block_user_everywhere_silent(client, target_id)
    
    GBAN_USERS.add(target_id)
    save_gban_list(GBAN_USERS)
    
    await status_msg.edit(f"{title_bar('GBAN DONE', '✅')}\nTarget: {target_name}\n📋 Spam: {'✓' if report_spam else '✗'}\n🎭 Impersonation: {'✓' if report_imp else '✗'}\n🚫 Blocked: {block_count} locations\n💀 Target does NOT know!\n{BRAND} 💀")

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
    
    await message.reply(f"{title_bar('UNGBAN', '✅')}\nUser {target_name} removed from GBAN list!\n{BRAND} 💀")

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
    
    await message.reply(f"{title_bar('GBAN LIST', '📋')}\nTotal: {len(GBAN_USERS)}\n" + "\n".join(user_list) + f"\n{BRAND} 💀")

# =============================================
# COMMAND: APPROVAL AFK
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
    
    await message.reply(f"{title_bar('APPROVED', '✅')}\nUser {target_name} has been approved!\n{BRAND} 💀")

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
    await message.reply(f"{title_bar('REJECTED', '🚫')}\nUser {target_name} has been blocked!\n{BRAND} 💀")

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
        await message.reply(f"{title_bar('UNBLOCKED', '✅')}\nUser {target_name} has been unblocked!\n{BRAND} 💀")
        afk_pending_users.pop(target_id, None)
        afk_approved_users.discard(target_id)
    except Exception as e:
        await message.reply(f"❌ Gagal: {e}")

# =============================================
# ULTRA BRUTAL HANDLER + AUTO MUTE!
# =============================================
async def ultra_brutal_handler(client, message):
    """Handler super cepat - balas semua pesan + auto mute spammer!"""
    global is_afk, afk_pending_users, afk_approved_users, WHITELIST_GROUPS, BLOCKED_GROUPS, GBAN_USERS, SUPERBRUTAL_GROUPS, AUTOMUTE_GROUPS
    
    # SKIP COMMAND
    if message.text and message.text.startswith('.'):
        return
    
    # SKIP BOT & CHANNEL
    if not message.from_user or message.from_user.is_bot or message.chat.type == ChatType.CHANNEL or message.sender_chat:
        return
    
    # SKIP PESAN DARI USERBOT SENDIRI
    me = await client.get_me()
    if message.from_user.id == me.id:
        return
    
    # CEK GBAN
    if message.from_user.id in GBAN_USERS:
        try:
            await client.block_user(message.from_user.id)
        except:
            pass
        return
    
    chat_type = message.chat.type
    chat_id = message.chat.id
    
    # AFK MODE DI PRIVATE
    if is_afk and chat_type == ChatType.PRIVATE:
        user_id = message.from_user.id
        
        if user_id in afk_approved_users:
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
    
    # PRIVATE CHAT
    if chat_type == ChatType.PRIVATE:
        settings_local = load_settings()
        if settings_local.get("auto_reply_private", True):
            await message.reply(get_brutal_reply())
        return
    
    # GROUP CHAT
    if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        # ==========================================
        # AUTO MUTE SPAMMER (HANYA JIKA ADMIN!)
        # ==========================================
        if chat_id in AUTOMUTE_GROUPS:
            # CEK APAKAH USERBOT ADMIN (KALO GA ADMIN, AUTO MUTE GAK BISA JALAN!)
            try:
                bot_member = await client.get_chat_member(chat_id, me.id)
                if bot_member.status in ["administrator", "creator"]:
                    # PROSES AUTO MUTE
                    user_name = message.from_user.first_name or message.from_user.username or str(message.from_user.id)
                    await check_and_mute_spammer(client, chat_id, message.from_user.id, user_name, message)
                else:
                    # KALO GA ADMIN, SKIP AUTO MUTE TAPI TETEP BALAS PESAN
                    pass
            except:
                pass
        
        # PRIORITAS 1: SUPER BRUTAL (BALAS SEMUA PESAN!)
        if chat_id in SUPERBRUTAL_GROUPS:
            await message.reply(get_brutal_reply())
            return
        
        # PRIORITAS 2: WHITELIST (BALAS NORMAL)
        if chat_id in WHITELIST_GROUPS:
            try:
                if me.username and message.text and f"@{me.username.lower()}" in message.text.lower():
                    await message.reply(get_mention_reply())
                    return
            except:
                pass
            
            await message.reply(get_simple_reply())
            return
        
        # PRIORITAS 3: BLACKLIST - JANGAN BALAS
        if chat_id in BLOCKED_GROUPS:
            return
        
        # DEFAULT - JANGAN BALAS
        return

# =============================================
# FLASK ROUTES
# =============================================
@app_flask.route("/", methods=["GET"])
def index():
    return "💀 THE TAMERS ULTRA BRUTAL v5.0 - RUNNING ON RAILWAY 💀", 200

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
    global client, BLOCKED_GROUPS, WHITELIST_GROUPS, SUPERBRUTAL_GROUPS, AUTOMUTE_GROUPS, settings, GBAN_USERS
    
    # Load data
    BLOCKED_GROUPS = load_blacklist()
    WHITELIST_GROUPS = load_whitelist()
    SUPERBRUTAL_GROUPS = load_superbrutal_groups()
    AUTOMUTE_GROUPS = load_automute_groups()
    settings = load_settings()
    GBAN_USERS = load_gban_list()
    
    print("=" * 60)
    print("💀 THE TAMERS v5.0 - AUTO MUTE SPAMMER EDITION 💀")
    print("=" * 60)
    print(f"📋 GBAN: {len(GBAN_USERS)} victims")
    print(f"🚫 Blacklist: {len(BLOCKED_GROUPS)} groups")
    print(f"✅ Whitelist: {len(WHITELIST_GROUPS)} groups")
    print(f"🔥 Super Brutal: {len(SUPERBRUTAL_GROUPS)} groups")
    print(f"🔇 Auto Mute: {len(AUTOMUTE_GROUPS)} groups")
    print("⚡ Mode: ULTRA BRUTAL + AUTO MUTE!")
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
        
        # =============================================
        # REGISTER ALL COMMANDS
        # =============================================
        
        # Basic commands
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
        
        # Approval commands
        @client.on_message(filters.me & filters.command("acc", prefixes="."))
        async def _(c, m): await cmd_approve(c, m)
        
        @client.on_message(filters.me & filters.command("reject", prefixes="."))
        async def _(c, m): await cmd_reject(c, m)
        
        @client.on_message(filters.me & filters.command("afklist", prefixes="."))
        async def _(c, m): await cmd_afklist(c, m)
        
        @client.on_message(filters.me & filters.command("unblock", prefixes="."))
        async def _(c, m): await cmd_unblock_user(c, m)
        
        # Blacklist/Whitelist commands
        @client.on_message(filters.me & filters.command("addbl", prefixes="."))
        async def _(c, m): await cmd_addbl(c, m)
        
        @client.on_message(filters.me & filters.command("rmbl", prefixes="."))
        async def _(c, m): await cmd_rmbl(c, m)
        
        @client.on_message(filters.me & filters.command("listbl", prefixes="."))
        async def _(c, m): await cmd_listbl(c, m)
        
        @client.on_message(filters.me & filters.command("grup on", prefixes="."))
        async def _(c, m): await cmd_grup_on(c, m)
        
        @client.on_message(filters.me & filters.command("grup off", prefixes="."))
        async def _(c, m): await cmd_grup_off(c, m)
        
        @client.on_message(filters.me & filters.command("listgrup", prefixes="."))
        async def _(c, m): await cmd_list_whitelist(c, m)
        
        # Broadcast commands
        @client.on_message(filters.me & filters.command("gcast", prefixes="."))
        async def _(c, m): await cmd_gcast(c, m)
        
        @client.on_message(filters.me & filters.command("ucast_all", prefixes="."))
        async def _(c, m): await cmd_ucast_all(c, m)
        
        @client.on_message(filters.me & filters.command("spam", prefixes="."))
        async def _(c, m): await cmd_spam(c, m)
        
        # GBAN commands
        @client.on_message(filters.me & filters.command("gban", prefixes="."))
        async def _(c, m): await cmd_gban(c, m)
        
        @client.on_message(filters.me & filters.command("ungban", prefixes="."))
        async def _(c, m): await cmd_ungban(c, m)
        
        @client.on_message(filters.me & filters.command("listgban", prefixes="."))
        async def _(c, m): await cmd_listgban(c, m)
        
        # Super Brutal commands
        @client.on_message(filters.me & filters.command("superbrutal on", prefixes="."))
        async def _(c, m): await cmd_superbrutal_on(c, m)
        
        @client.on_message(filters.me & filters.command("superbrutal off", prefixes="."))
        async def _(c, m): await cmd_superbrutal_off(c, m)
        
        @client.on_message(filters.me & filters.command("listsuperbrutal", prefixes="."))
        async def _(c, m): await cmd_list_superbrutal(c, m)
        
        # Auto Mute commands
        @client.on_message(filters.me & filters.command("automute on", prefixes="."))
        async def _(c, m): await cmd_automute_on(c, m)
        
        @client.on_message(filters.me & filters.command("automute off", prefixes="."))
        async def _(c, m): await cmd_automute_off(c, m)
        
        @client.on_message(filters.me & filters.command("listautomute", prefixes="."))
        async def _(c, m): await cmd_list_automute(c, m)
        
        @client.on_message(filters.me & filters.command("unmute", prefixes="."))
        async def _(c, m): await cmd_unmute(c, m)
        
        # =============================================
        # ULTRA BRUTAL AUTO REPLY + AUTO MUTE
        # =============================================
        @client.on_message(filters.incoming & ~filters.me)
        async def auto_reply(c, m):
            await ultra_brutal_handler(c, m)
        
        print("📌 ALL COMMANDS LOADED!")
        print("🔥 ULTRA BRUTAL MODE: ACTIVE!")
        print("🔇 AUTO MUTE MODE: ACTIVE (if userbot is admin)!")
        print("💀 WILL REPLY TO EVERY MESSAGE & MUTE SPAMMERS!")
        print("⚡ NO DELAY, NO FLOOD WAIT, NO LIMITS!")
        print("")
        print(f"📌 Bot is RUNNING on Railway!")
        print(f"📌 Press Ctrl+C to stop...")
        print("")
        
        # Keep running
        while True:
            await asyncio.sleep(60)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔥 THE TAMERS STILL KILLING SPAMMERS! 🔥")
            print(f"   📋 Super Brutal active in {len(SUPERBRUTAL_GROUPS)} groups")
            print(f"   🔇 Auto Mute active in {len(AUTOMUTE_GROUPS)} groups")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

# =============================================
# RUN
# =============================================
if __name__ == "__main__":
    from datetime import timedelta
    
    # Jalanin Flask di thread background
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Jalanin bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n💀 THE TAMERS HAS RISEN... Goodbye! 💀")
