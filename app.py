"""
THE TAMERS USERBOT v7.0 - GBAN NUCLEAR + AUTO MUTE EDITION
GBAN SUPER BRUTAL + Auto Mute NSFW/Promo/Spam!
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
from datetime import datetime, timedelta
from typing import Set, Dict, List
from flask import Flask, request
from concurrent.futures import ThreadPoolExecutor

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, PeerIdInvalid, SessionRevoked, RPCError
from pyrogram.types import Message, ChatPermissions
from pyrogram.enums import ChatType, ChatMemberStatus

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
executor = ThreadPoolExecutor(max_workers=20)

# =============================================
# KONFIGURASI
# =============================================
API_ID = 32584214
API_HASH = "6a59dd69d7e9db9916ff9c07eb237076"
BLACKLIST_FILE = "blacklist.json"
SETTINGS_FILE = "settings.json"
WHITELIST_FILE = "whitelist.json"
GBAN_LIST_FILE = "gban_list_nuclear.json"
SUPERBRUTAL_FILE = "superbrutal_groups.json"
AUTOMUTE_FILE = "automute_groups.json"
BOT_START_TIME = time.time()
BRAND = "THE TAMERS NUCLEAR"
VERSION = "7.0.0"

# =============================================
# DATA GLOBAL
# =============================================
BLOCKED_GROUPS = set()
WHITELIST_GROUPS = set()
SUPERBRUTAL_GROUPS = set()
AUTOMUTE_GROUPS = set()
settings = {}
is_afk = False
afk_pending_users = {}
afk_approved_users = set()
GBAN_USERS = set()

# Data untuk tracking GBAN
gban_report_count = {}
gban_block_count = {}

# Data untuk tracking spam per user (auto mute)
spam_counter: Dict[int, Dict[int, int]] = {}
spam_warned: Dict[int, Dict[int, bool]] = {}
muted_users: Dict[int, Set[int]] = {}

# =============================================
# DAFTAR KATA SPAM & NSFW
# =============================================

# Kata promosi & spam
SPAM_KEYWORDS = [
    r'promosi\s*grup', r'join\s*grup', r'gabung\s*grup', r'iklan\s*grup',
    r'sc:promosi', r'promosi\s+', r'iklan\s+', r'group\s+promosi',
    r'vvip', r'vip', r'murmer', r'murah', r'diskon', r'promo',
    r'jual', r'beli', r'toko', r'shop', r'dagang', r'bisnis',
    r'affiliate', r'referral', r'undangan', r'vc\s+cht', r'vc\s*chat',
    r'voice\s+chat', r'call\s+me', r'telepon', r'pm\s+me',
]

# Kata pornografi & dewasa (NSFW)
NSFW_KEYWORDS = [
    r'ngewe', r'ngentot', r'sex', r'seks', r'porn', r'porno',
    r'bokep', r'bokeb', r'blue', r'film\s+dewasa', r'video\s+dewasa',
    r'ml', r'melayani', r'ngocok', r'coli', r'toket', r'tete',
    r'memek', r'kontol', r'pepek', r'peler', r'pantat',
    r'temenin\s+mandi', r'temenin\s+os', r'os\s+os', r'mandi\s+bareng',
    r'mandi\s+bersama', r'jaket', r'kamar\s+mandi', r'keramas',
    r'pap', r'p\s*a\s*p', r'send\s+pap', r'pap\s+an', r'papan',
    r'nudes', r'nude', r'telanjang', r'buka\s+baju', r'buka\s+pakaian',
    r'open\s+baju', r'hot', r'panas', r'bokep\s+indo', r'video\s+bokep', r'foto\s+bugil', r'foto\s+telanjang', r'foto\s+panas', r'foto\s+hot', r'foto\s+seksi', r'foto\s+ngentot', r'foto\s+ngewe', r'foto\s+memek',
    r'chattan yuk', r'chat\s*yu?k', r'vc\s*yu?k', r'call\s*yu?k', r'mandi\s*yu?k', r'os\s*yu?k', r'temenin\s*yu?k', r'pap\s*yu?k', r'ridi VIP bokep telennt vcs semuanya ridi',
    r'Redyyy\s*VIP\s*bokep\s*telennt\s*vc\s*semuanya\s*Ridi', r'Ridi\s*VIP\s*bokep\s*telennt\s*vc\s*semuanya\s*Redyyy', r'emutt', r'colmek', r'col*mek', r'col\*mek', r'col\+mek', r'col\s*mek',
    r'promo', r'Temenin', r'VC', r'Voice\s*Chat', r'Call\s*Me', r'Telepon', r'PM\s*Me',
    r'b.ocils', r'hyprr', r'hypr', r'hyper', r'dm', r'temenin', r'co', r'chat', r'vc', r'os', r'mandi',
]

# Kata iklan & promo
PROMO_KEYWORDS = [
    r'beli\s+followers', r'beli\s+like', r'beli\s+view', r'jasa\s+social',
    r'boost\s+post', r'like\s+instagram', r'youtube\s+promosi',
    r'tiktok\s+promosi', r'shopee', r'tokopedia', r'lazada',
    r'whatsapp\s+promosi', r'telegram\s+channel',
]

def contains_forbidden_keywords(text: str) -> tuple:
    """Cek apakah teks mengandung kata terlarang. Return (is_forbidden, type)"""
    if not text:
        return False, None
    
    # Cek NSFW dulu (prioritas)
    for pattern in NSFW_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            return True, "nsfw"
    
    # Cek Promosi
    for pattern in PROMO_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            return True, "promo"
    
    # Cek Spam biasa
    for pattern in SPAM_KEYWORDS:
        if re.search(pattern, text, re.IGNORECASE):
            return True, "spam"
    
    return False, None

# =============================================
# DAFTAR BOT UNTUK REPORT MASSAL (GBAN)
# =============================================
REPORT_BOTS = [
    "SpamBot", "notoscam", "BotFather", "Telegram",
    "PremiumSupport", "Support", "SecurityBot"
]

REPORT_REASONS = [
    "spam", "abuse", "harassment", "impersonation",
    "scam", "fraud", "bot", "fake account", "spreading malware",
    "spam messages", "mass spam", "botnet", "phishing",
    "stolen account", "fake profile", "identity theft"
]

# =============================================
# BRUTAL REPLIES
# =============================================
BRUTAL_REPLIES = [
    "💀 **SPAM DETECTED!** 💀",
    "💀 **THE TAMERS DON'T TOLERATE SPAM!** 💀",
    "💀 **YOUR MESSAGE IS TRASH!** 💀",
    "💀 **WASTE YOUR TIME ELSEWHERE!** 💀",
    "💀 **THE TAMERS HAVE SPOKEN!** 💀",
]

NSFW_REPLIES = [
    "💀 **KONTEN DEWASA TERDETEKSI! ANDA KENA MUTE 1 JAM!** 💀",
    "🔞 **NSFW DETECTED! AUTOMATIC MUTE APPLIED!** 🔞",
    "💀 **KONTEN PORNO DILARANG! ANDA KENA MUTE!** 💀",
    "🔞 **YOUR MESSAGE CONTAINS INAPPROPRIATE CONTENT!** 🔞",
    "💀 **HARAM! ANDA DI-MUTE OTOMATIS!** 💀",
]

PROMO_REPLIES = [
    "💀 **PROMOSI DILARANG! ANDA KENA MUTE 30 MENIT!** 💀",
    "💀 **NO PROMOTION ALLOWED! AUTOMATIC MUTE!** 💀",
    "💀 **IKLAN/PROMOSI TIDAK DIPERBOLEHKAN!** 💀",
    "💀 **PROMO = MUTE! JANGAN PROMOSI DI SINI!** 💀",
]

SIMPLE_REPLIES = ["hmm 💀", "ya 💀", "Y 💀", "iyaaa 💀", "oke 💀"]
MENTION_REPLIES = ["hmm? 💀", "ya? 💀", "iyeee? 💀", "ada apa? 💀"]
AFK_REPLY = "💀 **THE TAMERS** lagi AFK, sabar ya! 💀"

def get_brutal_reply(): return random.choice(BRUTAL_REPLIES)
def get_nsfw_reply(): return random.choice(NSFW_REPLIES)
def get_promo_reply(): return random.choice(PROMO_REPLIES)
def get_simple_reply(): return random.choice(SIMPLE_REPLIES)
def get_mention_reply(): return random.choice(MENTION_REPLIES)

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
# AUTO MUTE FUNCTIONS (NSFW/PROMO/SPAM)
# =============================================

async def is_admin_group(client, chat_id, user_id):
    """Cek apakah user adalah admin di grup"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
        return False
    except:
        return False

async def can_restrict_members(client, chat_id):
    """Cek apakah bot punya hak restrict members"""
    try:
        me = await client.get_me()
        member = await client.get_chat_member(chat_id, me.id)
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            if member.privileges and member.privileges.can_restrict_members:
                return True
        elif member.status == ChatMemberStatus.OWNER:
            return True
        return False
    except:
        return False

async def mute_user_group(client, chat_id, user_id, duration=300):
    """Mute user dengan durasi tertentu (detik)"""
    try:
        await client.restrict_chat_member(
            chat_id, 
            user_id, 
            ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            ),
            datetime.now() + timedelta(seconds=duration)
        )
        return True
    except Exception as e:
        print(f"Mute error: {e}")
        return False

async def check_and_auto_mute(client, chat_id, user_id, user_name, message):
    """Cek pesan dan mute otomatis jika mengandung konten terlarang"""
    
    if chat_id not in AUTOMUTE_GROUPS:
        return False
    
    # Cek apakah user adalah admin (GAK BISA MUTE ADMIN!)
    if await is_admin_group(client, chat_id, user_id):
        return False
    
    # Cek apakah userbot bisa mute
    bot_can_mute = await can_restrict_members(client, chat_id)
    if not bot_can_mute:
        return False
    
    # Ambil teks pesan
    text = message.text or message.caption or ""
    
    # CEK KATA TERLARANG
    is_forbidden, content_type = contains_forbidden_keywords(text)
    
    if is_forbidden:
        # Tentukan durasi mute berdasarkan jenis konten
        if content_type == "nsfw":
            duration = 3600  # 1 jam untuk NSFW
            reply = get_nsfw_reply()
        elif content_type == "promo":
            duration = 1800  # 30 menit untuk promo
            reply = get_promo_reply()
        else:
            duration = 600  # 10 menit untuk spam biasa
            reply = get_brutal_reply()
        
        # Mute user
        if await mute_user_group(client, chat_id, user_id, duration):
            await message.reply(f"{reply}\n\n🔇 **MUTED FOR {duration//60} MINUTES!**")
            return True
    
    return False

# =============================================
# GBAN NUCLEAR FUNCTIONS
# =============================================

async def nuclear_report_to_spambot(client, user_id):
    """Report ke SpamBot dengan multiple reason (DIAM-DIAM)"""
    results = []
    for reason in REPORT_REASONS[:3]:
        try:
            await client.send_message("SpamBot", f"/report {user_id} {reason}")
            await asyncio.sleep(0.3)
            results.append(True)
        except:
            results.append(False)
    return any(results)

async def nuclear_report_multiple_bots(client, user_id):
    """Report ke multiple bot sekaligus (DIAM-DIAM)"""
    success_count = 0
    for bot in REPORT_BOTS:
        try:
            await client.send_message(bot, f"/report {user_id} spam")
            await asyncio.sleep(0.2)
            success_count += 1
        except:
            pass
    return success_count

async def nuclear_report_impersonation(client, user_id):
    """Report impersonation ke SpamBot"""
    try:
        await client.send_message("SpamBot", f"/report {user_id} impersonation")
        await asyncio.sleep(0.5)
        return True
    except:
        return False

async def nuclear_report_scam(client, user_id):
    """Report scam ke SpamBot"""
    try:
        await client.send_message("SpamBot", f"/report {user_id} scam")
        await asyncio.sleep(0.5)
        return True
    except:
        return False

async def nuclear_block_everywhere(client, user_id):
    """Blokir user dari semua tempat (GLOBAL BLOCK)"""
    blocked_count = 0
    
    try:
        await client.block_user(user_id)
        blocked_count += 1
    except:
        pass
    
    try:
        async for dialog in client.get_dialogs():
            if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                try:
                    await dialog.chat.ban_member(user_id)
                    blocked_count += 1
                    await asyncio.sleep(0.05)
                except:
                    pass
    except:
        pass
    
    return blocked_count

async def nuclear_mute_in_all_groups(client, user_id):
    """Mute user di semua grup (DIAM-DIAM)"""
    muted_count = 0
    try:
        async for dialog in client.get_dialogs():
            if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                try:
                    me = await client.get_me()
                    bot_member = await dialog.chat.get_member(me.id)
                    if bot_member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
                        permissions = ChatPermissions(
                            can_send_messages=False,
                            can_send_media_messages=False,
                            can_send_other_messages=False,
                            can_add_web_page_previews=False
                        )
                        await dialog.chat.restrict_member(user_id, permissions)
                        muted_count += 1
                        await asyncio.sleep(0.05)
                except:
                    pass
    except:
        pass
    return muted_count

async def nuclear_global_ban(client, user_id, user_name=None):
    """GBAN NUCLEAR - Multi-layer attack tanpa ketahuan!"""
    global gban_report_count, gban_block_count
    
    report_success = await nuclear_report_to_spambot(client, user_id)
    imp_success = await nuclear_report_impersonation(client, user_id)
    scam_success = await nuclear_report_scam(client, user_id)
    multi_report_count = await nuclear_report_multiple_bots(client, user_id)
    block_count = await nuclear_block_everywhere(client, user_id)
    mute_count = await nuclear_mute_in_all_groups(client, user_id)
    
    GBAN_USERS.add(user_id)
    save_gban_list(GBAN_USERS)
    
    gban_report_count[user_id] = multi_report_count
    gban_block_count[user_id] = block_count + mute_count
    
    return {
        "report": report_success,
        "impersonation": imp_success,
        "scam": scam_success,
        "multi_reports": multi_report_count,
        "blocks": block_count,
        "mutes": mute_count
    }

# =============================================
# COMMAND: PING, STATUS, INFO
# =============================================
async def cmd_ping(client, message):
    start = time.time()
    await asyncio.sleep(0.05)
    ping = int((time.time() - start) * 1000)
    
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
    
    async for dialog in client.get_dialogs():
        if dialog.chat.type == ChatType.PRIVATE and dialog.chat.id > 0:
            total_users += 1
        elif dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            total_groups += 1
    
    await message.reply(f"""
{title_bar("STATUS", "💀")}
{info_line("Owner", me.first_name, "👑")}
{info_line("ID", me.id, "🆔")}
{info_line("Private", f"{total_users} chats", "👤")}
{info_line("Groups", f"{total_groups} groups", "👥")}
{info_line("Uptime", get_uptime(), "⏱️")}
{info_line("GBAN Nuclear", f"{len(GBAN_USERS)} victims", "💀")}
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
# COMMAND: SUPER BRUTAL
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
💀 EVERY MESSAGE WILL BE REPLIED!
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
# COMMAND: AUTO MUTE (NSFW/PROMO/SPAM)
# =============================================
async def cmd_automute_on(client, message):
    """Aktifin auto mute (NSFW/Promo/Spam) di grup ini"""
    global AUTOMUTE_GROUPS
    
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Command ini harus diketik di dalam grup!")
        return
    
    chat_id = message.chat.id
    chat_title = message.chat.title or "Grup"
    me = await client.get_me()
    
    if chat_id in AUTOMUTE_GROUPS:
        await message.reply(f"⚠️ Auto Mute already ON in {chat_title}")
        return
    
    # CEK APAKAH USERBOT ADMIN DAN PUNYA HAK RESTRICT
    bot_can_mute = await can_restrict_members(client, chat_id)
    
    if not bot_can_mute:
        await message.reply(f"""
{title_bar("AUTO MUTE", "❌")}
{info_line("Group", chat_title, "📌")}
{info_line("Status", "FAILED", "⚠️")}

💀 USERBOT HARUS JADI ADMIN DULU!
🔥 Caranya:
   1. Jadikan @{me.username} sebagai admin di grup ini
   2. CENTANG "Restrict Members"

📌 Setelah itu ketik .automute on lagi!
{BRAND} 💀
""")
        return
    
    AUTOMUTE_GROUPS.add(chat_id)
    save_automute_groups(AUTOMUTE_GROUPS)
    
    await message.reply(f"""
{title_bar("AUTO MUTE", "🔇")}
{info_line("Group", chat_title, "📌")}
{info_line("Status", "ENABLED", "✅")}

💀 **AUTO MUTE ACTIVATED!**

🔞 **NSFW CONTENT** (pornografi, dewasa) → MUTE 1 JAM
📢 **PROMOTION/ADS** (iklan, promo, vvip/vip) → MUTE 30 MENIT
💀 **SPAM** (spam biasa) → MUTE 10 MENIT

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

# =============================================
# COMMAND: GBAN NUCLEAR
# =============================================

async def cmd_gban(client, message):
    """GBAN NUCLEAR - Hancurkan user tanpa jejak!"""
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
        await message.reply("❌ `.gban @username` atau reply ke pesan user!")
        return
    
    me = await client.get_me()
    if target_id == me.id:
        await message.reply("❌ Mau gban diri sendiri? Goblok! 💀")
        return
    
    if target_id in GBAN_USERS:
        await message.reply(f"⚠️ {target_name} udah kena GBAN NUCLEAR sebelumnya!")
        return
    
    status_msg = await message.reply(
        f"{title_bar('GBAN NUCLEAR', '💀')}\n"
        f"{info_line('Target', target_name, '🎯')}\n"
        f"{info_line('Mode', 'ULTIMATE', '🔥')}\n"
        f"{'█' * 20}\n"
        f"⚡ Processing nuclear attack..."
    )
    
    result = await nuclear_global_ban(client, target_id, target_name)
    
    final_msg = (
        f"{title_bar('GBAN NUCLEAR', '💀')}\n"
        f"{info_line('Target', target_name, '🎯')}\n"
        f"{info_line('ID', target_id, '🆔')}\n"
        f"{info_line('Username', f'@{target_username}' if target_username else '-', '📱')}\n"
        f"{'─' * 25}\n"
        f"📊 **NUCLEAR ATTACK RESULT:**\n"
        f"┃ ├─ Spam Report: {'✅' if result['report'] else '⚠️'}\n"
        f"┃ ├─ Impersonation: {'✅' if result['impersonation'] else '⚠️'}\n"
        f"┃ ├─ Scam Report: {'✅' if result['scam'] else '⚠️'}\n"
        f"┃ ├─ Multi Reports: {result['multi_reports']} bots\n"
        f"┃ ├─ Global Blocks: {result['blocks']} locations\n"
        f"┃ └─ Global Mutes: {result['mutes']} groups\n"
        f"{'─' * 25}\n"
        f"💀 **TARGET TERHANCURKAN!**\n"
        f"🔇 **TANPA PEMBERITAHUAN!**\n"
        f"💀 Target tidak akan pernah tahu!\n"
        f"{BRAND} v{VERSION} 💀"
    )
    
    await status_msg.edit(final_msg)
    
    try:
        await message.delete()
    except:
        pass

async def cmd_ungban(client, message):
    """Melepas user dari GBAN NUCLEAR"""
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
        await message.reply("❌ `.ungban @username` atau reply ke pesan user")
        return
    
    if target_id not in GBAN_USERS:
        await message.reply(f"⚠️ {target_name} gak ada di GBAN NUCLEAR list!")
        return
    
    GBAN_USERS.discard(target_id)
    save_gban_list(GBAN_USERS)
    
    try:
        await client.unblock_user(target_id)
    except:
        pass
    
    await message.reply(
        f"{title_bar('UNGBAN', '✅')}\n"
        f"{info_line('User', target_name, '👤')}\n"
        f"{info_line('Status', 'Removed from GBAN NUCLEAR', '📌')}\n"
        f"✅ User telah dibebaskan!\n"
        f"⚠️ Efek report mungkin masih ada dari Telegram!\n"
        f"{BRAND} 💀"
    )

async def cmd_listgban(client, message):
    """Lihat daftar korban GBAN NUCLEAR"""
    if not GBAN_USERS:
        await message.reply(
            f"{title_bar('GBAN LIST', '📋')}\n"
            f"✅ Belum ada user yang kena GBAN NUCLEAR.\n"
            f"💀 Gunakan `.gban @user` untuk mulai menghancurkan!"
        )
        return
    
    user_list = []
    for uid in list(GBAN_USERS)[:30]:
        try:
            user = await client.get_users(uid)
            name = user.first_name
            username = f"@{user.username}" if user.username else "-"
            user_list.append(f"┃ ▸ {name} ({username})")
        except:
            user_list.append(f"┃ ▸ User ID: {uid}")
    
    await message.reply(
        f"{title_bar('GBAN NUCLEAR LIST', '📋')}\n"
        f"{info_line('Total', f'{len(GBAN_USERS)} users', '🔥')}\n"
        f"{'─' * 25}\n"
        + "\n".join(user_list) + 
        f"\n{'─' * 25}\n"
        f"💀 Mereka semua sudah terhancurkan tanpa sadar!\n"
        f"{BRAND} 💀"
    )

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
        await message.reply("❌ `.acc @username` atau reply ke pesan")
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
# ULTRA BRUTAL HANDLER (AUTO MUTE + GBAN CHECK)
# =============================================
async def ultra_brutal_handler(client, message):
    global is_afk, afk_pending_users, afk_approved_users, WHITELIST_GROUPS, BLOCKED_GROUPS, GBAN_USERS, SUPERBRUTAL_GROUPS, AUTOMUTE_GROUPS
    
    if message.text and message.text.startswith('.'):
        return
    
    if not message.from_user or message.from_user.is_bot or message.chat.type == ChatType.CHANNEL or message.sender_chat:
        return
    
    me = await client.get_me()
    if message.from_user.id == me.id:
        return
    
    if message.from_user.id in GBAN_USERS:
        try:
            await client.block_user(message.from_user.id)
        except:
            pass
        return
    
    chat_type = message.chat.type
    chat_id = message.chat.id
    
    # AUTO MUTE NSFW/PROMO/SPAM (DI GRUP!)
    if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        user_name = message.from_user.first_name or message.from_user.username or str(message.from_user.id)
        await check_and_auto_mute(client, chat_id, message.from_user.id, user_name, message)
    
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
                    await message.reply("💀 SPAM! You have been blocked!")
                except:
                    pass
            return
        
        if count >= 3 and not afk_pending_users[user_id].get("warned", False):
            afk_pending_users[user_id]["warned"] = True
            await message.reply("⚠️ WARNING! Don't spam!")
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
        if chat_id in SUPERBRUTAL_GROUPS:
            await message.reply(get_brutal_reply())
            return
        
        if chat_id in WHITELIST_GROUPS:
            await message.reply(get_simple_reply())
            return
        
        if chat_id in BLOCKED_GROUPS:
            return

# =============================================
# FLASK ROUTES
# =============================================
@app_flask.route("/", methods=["GET"])
def index():
    return "💀 THE TAMERS NUCLEAR v7.0 - RUNNING  💀", 200

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
    
    BLOCKED_GROUPS = load_blacklist()
    WHITELIST_GROUPS = load_whitelist()
    SUPERBRUTAL_GROUPS = load_superbrutal_groups()
    AUTOMUTE_GROUPS = load_automute_groups()
    settings = load_settings()
    GBAN_USERS = load_gban_list()
    
    print("=" * 60)
    print("💀 THE TAMERS v7.0 - GBAN NUCLEAR + AUTO MUTE 💀")
    print("=" * 60)
    print(f"📋 GBAN Nuclear: {len(GBAN_USERS)} victims")
    print(f"🚫 Blacklist: {len(BLOCKED_GROUPS)} groups")
    print(f"✅ Whitelist: {len(WHITELIST_GROUPS)} groups")
    print(f"🔥 Super Brutal: {len(SUPERBRUTAL_GROUPS)} groups")
    print(f"🔇 Auto Mute: {len(AUTOMUTE_GROUPS)} groups")
    print("💀 GBAN Mode: NUCLEAR (SILENT & BRUTAL)")
    print("🔞 NSFW Detector: ACTIVE")
    print("📢 Promo Detector: ACTIVE")
    print("")
    
    session_string = os.getenv("SESSION_STRING")
    
    if session_string:
        print("🔑 Using String Session...")
        client = Client("userbot", session_string=session_string, api_id=API_ID, api_hash=API_HASH)
    else:
        print("❌ SESSION_STRING not found!")
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
        
        @client.on_message(filters.me & filters.command("afklist", prefixes="."))
        async def _(c, m): await cmd_afklist(c, m)
        
        @client.on_message(filters.me & filters.command("unblock", prefixes="."))
        async def _(c, m): await cmd_unblock_user(c, m)
        
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
        
        @client.on_message(filters.me & filters.command("gcast", prefixes="."))
        async def _(c, m): await cmd_gcast(c, m)
        
        @client.on_message(filters.me & filters.command("ucast_all", prefixes="."))
        async def _(c, m): await cmd_ucast_all(c, m)
        
        @client.on_message(filters.me & filters.command("spam", prefixes="."))
        async def _(c, m): await cmd_spam(c, m)
        
        @client.on_message(filters.me & filters.command("gban", prefixes="."))
        async def _(c, m): await cmd_gban(c, m)
        
        @client.on_message(filters.me & filters.command("ungban", prefixes="."))
        async def _(c, m): await cmd_ungban(c, m)
        
        @client.on_message(filters.me & filters.command("listgban", prefixes="."))
        async def _(c, m): await cmd_listgban(c, m)
        
        @client.on_message(filters.me & filters.command("superbrutal on", prefixes="."))
        async def _(c, m): await cmd_superbrutal_on(c, m)
        
        @client.on_message(filters.me & filters.command("superbrutal off", prefixes="."))
        async def _(c, m): await cmd_superbrutal_off(c, m)
        
        @client.on_message(filters.me & filters.command("listsuperbrutal", prefixes="."))
        async def _(c, m): await cmd_list_superbrutal(c, m)
        
        @client.on_message(filters.me & filters.command("automute on", prefixes="."))
        async def _(c, m): await cmd_automute_on(c, m)
        
        @client.on_message(filters.me & filters.command("automute off", prefixes="."))
        async def _(c, m): await cmd_automute_off(c, m)
        
        @client.on_message(filters.me & filters.command("listautomute", prefixes="."))
        async def _(c, m): await cmd_list_automute(c, m)
        
        @client.on_message(filters.incoming & ~filters.me)
        async def auto_reply(c, m):
            await ultra_brutal_handler(c, m)
        
        print("📌 ALL COMMANDS LOADED!")
        print("💀 GBAN NUCLEAR MODE: ACTIVE!")
        print("🔇 AUTO MUTE NSFW/PROMO/SPAM: ACTIVE!")
        print("🔇 SILENT MODE: ON (target tidak tahu)")
        print("")
        print(f"📌 Bot is RUNNING on Railway!")
        print(f"📌 Press Ctrl+C to stop...")
        print("")
        
        while True:
            await asyncio.sleep(60)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 💀 THE TAMERS NUCLEAR STILL ACTIVE! 💀")
            print(f"   📋 GBAN Victims: {len(GBAN_USERS)}")
            print(f"   🔇 Auto Mute Groups: {len(AUTOMUTE_GROUPS)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

# =============================================
# RUN
# =============================================
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n💀 THE TAMERS NUCLEAR HAS RISEN... Goodbye! 💀")
