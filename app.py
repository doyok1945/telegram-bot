"""
THE TAMERS USERBOT v8.0 - ULTRA NSFW DETECTOR + ZERO DELAY
Deteksi semua variasi NSFW, promo, spam dengan simbol dan karakter aneh!
Zero delay untuk superbrutal!
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
from typing import Set, Dict, List, Tuple
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
executor = ThreadPoolExecutor(max_workers=50)  # DIKITIN BIAR LEBIH CEPET

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
VERSION = "8.0.0"

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

# =============================================
# FUNGSI NORMALISASI TEKS (UNIVERSAL!)
# =============================================

def normalize_unicode_text(text: str) -> str:
    """Normalisasi teks yang mengandung karakter aneh, simbol, angka, dll"""
    if not text:
        return ""
    
    # Ubah ke lowercase
    text = text.lower()
    
    # Mapping karakter aneh ke huruf normal
    char_map = {
        '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '8': 'b',
        'ᥱ': 'e', '⍴': 'p', 'о': 'o', '𝗇': 'n', 'α': 'a', 'ძ': 'd', 'і': 'i',
        '𝗇': 'n', '𝗎': 'u', '𝗅': 'l', '𝗄': 'k', '𝗆': 'm', '𝗁': 'h',
        '𝗌': 's', '𝗉': 'p', '𝗍': 't', '𝗐': 'w', '𝗒': 'y', '𝗑': 'x',
        '𝗓': 'z', '𝗰': 'c', '𝗏': 'v', '𝗯': 'b', '𝗴': 'g', '𝗷': 'j',
        '𝗾': 'q', '𝗿': 'r', '𝗳': 'f', '𝗱': 'd', '𝗲': 'e',
        'ᴘ': 'p', 'ʀ': 'r', 'ᴏ': 'o', 'ꜰ': 'f', 'ɪ': 'i', 'ʟ': 'l',
        'ᴇ': 'e', 'ᴄ': 'c', 'ᴋ': 'k', 'ᴠ': 'v', 'ʙ': 'b',
    }
    
    for old, new in char_map.items():
        text = text.replace(old, new)
    
    # Hapus spasi berlebih
    text = re.sub(r'\s+', ' ', text)
    
    # Hapus karakter berulang (bohcilll -> bohcil, freshh -> fresh)
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    
    return text

def ultra_detect(text: str) -> Tuple[bool, str]:
    """Deteksi ultra sensitif untuk semua jenis spam/nsfw/promo"""
    if not text:
        return False, None
    
    # Normalisasi teks
    normalized = normalize_unicode_text(text)
    
    # ==========================================
    # POLA NSFW / PORNOGRAFI (WAJIB MUTE!)
    # ==========================================
    nsfw_patterns = [
        # Pola dari contoh lo
        r'bh0+c+i+l+', r'bohc+i+l+', r'b0hci+l+', r'bohcil',
        r'f+r+e+s+h+', r'fresh',
        r't+b+r+u+', r'tribru', r'tbr+u+',
        r'd+i+b+i+y+o+h+', r'dibiiyoh', r'dbyo+o+h', r'dbyooh',
        r'v+i+d+', r'vid',
        r'v+i+p+', r'vip',
        r'c+w+o+k+', r'cwo+k+', r'cwok+', r'cwoo',
        r'h+y+p+r+r+', r'hyprr', r'hyper',
        r'd+m+', r'dm',
        r'c+o+w+o+', r'cowoo', r'cowo',
        r'o+m+e+k+', r'omek',
        r'b+y+o+h+', r'byoh',
        r'm+e+d+i+a+', r'media',
        r'k+l+o+k+e+s+i+', r'klokesi',
        r'p+e+r+i+b+a+d+i+', r'peribadi',
        r'o+n+k+e+m+', r'onkem',
        r'h+o+r+n+', r'horn',
        r'p+r+o+m+o+', r'promo',
        r'v+e+c+e+e+s+', r'vecees',
        r'p+u+l+u+x+o+d+y+', r'pulu xody', r'pullxbody',
        r'v+i+a+i+p+i+', r'viaipi',
        r'c+e+t+t+', r'cett',
        
        # Kata kunci NSFW umum
        r'ngewe', r'ngentot', r'sex', r'seks', r'porn', r'porno',
        r'bokep', r'bokeb', r'blue', r'film\s*dewasa', r'video\s*dewasa',
        r'ml', r'melayani', r'ngocok', r'coli', r'toket', r'tete',
        r'memek', r'kontol', r'pepek', r'peler', r'pantat',
        r'temenin\s*mandi', r'temenin\s*os', r'os\s*os', r'mandi\s*bareng',
        r'pap', r'nudes', r'nude', r'telanjang', r'buka\s*baju', r'open\s*baju',
        
        # 18+ dan dewasa
        r'18\+', r'18\s?\+', r'dewasa', r'hot', r'panas',
    ]
    
    for pattern in nsfw_patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            return True, "nsfw"
        if re.search(pattern, text, re.IGNORECASE):
            return True, "nsfw"
    
    # ==========================================
    # POLA PROMOSI / IKLAN
    # ==========================================
    promo_patterns = [
        r'pro?m?o?s?i?', r'promosi', r'promo',
        r'jual', r'beli', r'toko', r'shop', r'dagang',
        r'v+v+i+p+', r'vvip', r'vip',
        r'm+u+r+a+h+', r'murah', r'd+i+s+k+o+n+', r'diskon',
        r'b+e+l+i+', r'beli', r'f+o+l+l+o+w+e+r+s+', r'followers',
        r'l+i+k+e+', r'like', r's+h+o+p+e+e+', r'shopee',
        r't+o+k+o+p+e+d+i+a+', r'tokopedia', r'l+a+z+a+d+a+', r'lazada',
    ]
    
    for pattern in promo_patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            return True, "promo"
        if re.search(pattern, text, re.IGNORECASE):
            return True, "promo"
    
    # ==========================================
    # POLA SPAM UMUM
    # ==========================================
    spam_patterns = [
        r'y+u+u+u?\s*c+h+a+t+t?', r'chatt\s*yuuu',
        r'1c+w+o+o+o?', r'c+w+o+o+', r'c+w+o+k+',
        r'v+i+c+e+e+s+', r'v+i+c+e+s+',
        r'a+n+g+e+e?', r'a+n+g+e+',
        r'l+i+m+i+t+t+', r'l+i+m+i+t+',
        r'h+y+p+r+r+', r'h+y+p+e+r+',
        r'd+m+', r'p+m+', r'p+c+',
        r'-?\s*1\s*c+o+w+o+', r'c+o+w+o+',
        r'b+h+0+0+0+c+i+l+l+d+', r'bohcil',
        r'd+b+y+o+o+h+', r'dbyooh',
        r's+a+y+a+n+g+', r'sayang',
        r'm+a+m+p+i+r+', r'mampir',
        r's+i+n+i+', r'sini',
        r'a+d+a+', r'ada',
        r'y+a+n+g+', r'yang',
        r'l+g+', r'lg',
        r'm+a+c+a+m+', r'macam',
        r'k+a+y+a+', r'kaya',
        r'g+i+t+u+', r'gitu',
        r'l+o+h+', r'loh',
        r's+o+a+l+n+y+a+', r'soalnya',
        r'b+a+b+y+', r'baboy',
        r'm+a+c+a+m+', r'macam',
    ]
    
    for pattern in spam_patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            return True, "spam"
        if re.search(pattern, text, re.IGNORECASE):
            return True, "spam"
    
    # Deteksi kombinasi huruf & angka mencurigakan
    if re.search(r'\d+[a-z]{3,}', normalized) and len(normalized) < 30:
        return True, "spam"
    
    # Deteksi karakter berulang berlebihan
    if re.search(r'([a-z]{2,})\1{2,}', normalized) and len(normalized) < 40:
        return True, "spam"
    
    # Deteksi kata "sayang" + chat
    if re.search(r'sayang.*chat', normalized):
        return True, "spam"
    
    return False, None

def contains_forbidden_keywords(text: str) -> Tuple[bool, str]:
    """Wrapper untuk ultra_detect"""
    return ultra_detect(text)

# =============================================
# BRUTAL REPLIES (ZERO EMOJI VARIASI)
# =============================================
BRUTAL_REPLIES = [
    "💀 SPAM DETECTED! 💀",
    "💀 THE TAMERS DON'T TOLERATE SPAM! 💀",
    "💀 YOUR MESSAGE IS TRASH! 💀",
]

NSFW_REPLIES = [
    "💀 KONTEN DEWASA TERDETEKSI! MUTE 1 JAM! 💀",
    "🔞 NSFW DETECTED! AUTOMATIC MUTE! 🔞",
]

PROMO_REPLIES = [
    "💀 PROMOSI DILARANG! MUTE 30 MENIT! 💀",
]

SIMPLE_REPLIES = ["hmm 💀", "ya 💀", "Y 💀", "oke 💀"]
MENTION_REPLIES = ["hmm? 💀", "ya? 💀"]
AFK_REPLY = "💀 THE TAMERS lagi AFK, sabar ya! 💀"

def get_brutal_reply(): return random.choice(BRUTAL_REPLIES)
def get_nsfw_reply(): return random.choice(NSFW_REPLIES)
def get_promo_reply(): return random.choice(PROMO_REPLIES)
def get_simple_reply(): return random.choice(SIMPLE_REPLIES)
def get_mention_reply(): return random.choice(MENTION_REPLIES)

# =============================================
# FUNGSI BANTUAN
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
# MANAJEMEN DATA (SINGKAT)
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
# AUTO MUTE FUNCTIONS (CEK ADMIN BENER!)
# =============================================

async def is_admin_group(client, chat_id, user_id):
    """Cek apakah user adalah admin di grup"""
    try:
        member = await client.get_chat_member(chat_id, user_id)
        status = str(member.status).lower() if member.status else ""
        if "administrator" in status or "owner" in status:
            return True
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return True
        return False
    except:
        return False

async def can_restrict_members(client, chat_id):
    """Cek apakah userbot punya hak restrict members"""
    try:
        me = await client.get_me()
        member = await client.get_chat_member(chat_id, me.id)
        
        if member.status == ChatMemberStatus.OWNER:
            return True
        
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            if member.privileges:
                return member.privileges.can_restrict_members
            # Test mute ke diri sendiri
            try:
                await client.restrict_chat_member(
                    chat_id, me.id,
                    ChatPermissions(can_send_messages=False),
                    datetime.now() + timedelta(seconds=3)
                )
                await client.restrict_chat_member(
                    chat_id, me.id,
                    ChatPermissions(can_send_messages=True)
                )
                return True
            except:
                return False
        return False
    except:
        return False

async def mute_user_group(client, chat_id, user_id, duration=300):
    """Mute user dengan durasi tertentu (detik)"""
    try:
        await client.restrict_chat_member(
            chat_id, user_id,
            ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False
            ),
            datetime.now() + timedelta(seconds=duration)
        )
        return True
    except:
        return False

async def check_and_auto_mute(client, chat_id, user_id, user_name, message):
    """Cek pesan dan mute otomatis - ZERO DELAY!"""
    
    if chat_id not in AUTOMUTE_GROUPS:
        return False
    
    # Cek admin (gak bisa mute admin)
    if await is_admin_group(client, chat_id, user_id):
        return False
    
    # Cek userbot bisa mute
    if not await can_restrict_members(client, chat_id):
        return False
    
    # Ambil teks
    text = message.text or message.caption or ""
    
    # DETEKSI LANGSUNG!
    is_forbidden, content_type = ultra_detect(text)
    
    if is_forbidden:
        if content_type == "nsfw":
            duration = 3600
            reply = get_nsfw_reply()
        elif content_type == "promo":
            duration = 1800
            reply = get_promo_reply()
        else:
            duration = 600
            reply = get_brutal_reply()
        
        # MUTE LANGSUNG!
        if await mute_user_group(client, chat_id, user_id, duration):
            try:
                await message.reply(f"{reply}\n\n🔇 MUTED {duration//60} MINUTES!")
            except:
                pass
            return True
    
    return False

# =============================================
# GBAN NUCLEAR FUNCTIONS (SINGKAT)
# =============================================
REPORT_BOTS = ["SpamBot", "notoscam", "BotFather"]
REPORT_REASONS = ["spam", "abuse", "harassment", "impersonation", "scam", "fraud"]

async def nuclear_global_ban(client, user_id, user_name=None):
    """GBAN NUCLEAR - Multi-layer attack"""
    # Report ke SpamBot
    try:
        await client.send_message("SpamBot", f"/report {user_id} spam impersonation")
        await asyncio.sleep(0.3)
        report_ok = True
    except:
        report_ok = False
    
    # Block everywhere
    block_count = 0
    try:
        await client.block_user(user_id)
        block_count += 1
        async for dialog in client.get_dialogs():
            if dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
                try:
                    await dialog.chat.ban_member(user_id)
                    block_count += 1
                    await asyncio.sleep(0.05)
                except:
                    pass
    except:
        pass
    
    GBAN_USERS.add(user_id)
    save_gban_list(GBAN_USERS)
    
    return {"report": report_ok, "blocks": block_count}

# =============================================
# COMMAND: PING, STATUS, INFO (SINGKAT)
# =============================================
async def cmd_ping(client, message):
    start = time.time()
    await asyncio.sleep(0.01)
    ping = int((time.time() - start) * 1000)
    await message.reply(f"{title_bar('PING', '💀')}\nResponse: {ping}ms\nUptime: {get_uptime()}\n{BRAND} 💀")

async def cmd_status(client, message):
    me = await client.get_me()
    await message.reply(f"""
{title_bar("STATUS", "💀")}
Owner: {me.first_name}
ID: {me.id}
Uptime: {get_uptime()}
GBAN: {len(GBAN_USERS)} victims
Auto Mute: {len(AUTOMUTE_GROUPS)} groups
{BRAND} v{VERSION} 💀
""")

async def cmd_info(client, message):
    me = await client.get_me()
    await message.reply(f"{title_bar('USER INFO', '👤')}\nName: {me.first_name}\nUsername: @{me.username if me.username else '-'}\nID: {me.id}\n{BRAND} 💀")

async def cmd_afk(client, message):
    global is_afk
    is_afk = True
    await message.reply(f"{title_bar('AFK MODE', '😴')}\nAway! Type .unafk to back\n{BRAND} 💀")

async def cmd_unafk(client, message):
    global is_afk
    is_afk = False
    await message.reply(f"{title_bar('AFK MODE', '✅')}\nBack!\n{BRAND} 💀")

# =============================================
# COMMAND: SUPER BRUTAL (ZERO DELAY!)
# =============================================
async def cmd_superbrutal_on(client, message):
    global SUPERBRUTAL_GROUPS
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Ketik di grup!")
        return
    
    chat_id = message.chat.id
    chat_title = message.chat.title or "Grup"
    SUPERBRUTAL_GROUPS.add(chat_id)
    save_superbrutal_groups(SUPERBRUTAL_GROUPS)
    await message.reply(f"{title_bar('SUPER BRUTAL', '🔥')}\n{chat_title} - EVERY MESSAGE WILL BE REPLIED INSTANTLY!\n{BRAND} 💀")

async def cmd_superbrutal_off(client, message):
    global SUPERBRUTAL_GROUPS
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Ketik di grup!")
        return
    
    chat_id = message.chat.id
    chat_title = message.chat.title or "Grup"
    SUPERBRUTAL_GROUPS.discard(chat_id)
    save_superbrutal_groups(SUPERBRUTAL_GROUPS)
    await message.reply(f"{title_bar('SUPER BRUTAL', '❌')}\nSuper Brutal DISABLED in {chat_title}\n{BRAND} 💀")

async def cmd_list_superbrutal(client, message):
    if not SUPERBRUTAL_GROUPS:
        await message.reply(f"{title_bar('SUPER BRUTAL LIST', '📋')}\nNo active groups")
        return
    lines = []
    for gid in list(SUPERBRUTAL_GROUPS)[:30]:
        try:
            chat = await client.get_chat(gid)
            lines.append(f"▸ {chat.title}")
        except:
            lines.append(f"▸ ID: {gid}")
    await message.reply(f"{title_bar('SUPER BRUTAL LIST', '📋')}\nTotal: {len(SUPERBRUTAL_GROUPS)}\n" + "\n".join(lines))

# =============================================
# COMMAND: AUTO MUTE
# =============================================
async def cmd_automute_on(client, message):
    global AUTOMUTE_GROUPS
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Ketik di grup!")
        return
    
    chat_id = message.chat.id
    chat_title = message.chat.title or "Grup"
    me = await client.get_me()
    
    # CEK ADMIN
    try:
        member = await client.get_chat_member(chat_id, me.id)
        status = str(member.status).lower() if member.status else ""
        
        if "administrator" not in status and "owner" not in status:
            await message.reply(f"""
{title_bar("AUTO MUTE", "❌")}
Group: {chat_title}
Status: FAILED

💀 USERBOT HARUS JADI ADMIN DULU!
CARA: Jadikan @{me.username} sebagai admin dengan hak "Restrict Members"

{BRAND} 💀
""")
            return
        
        can_restrict = False
        if member.privileges:
            can_restrict = member.privileges.can_restrict_members
        
        if not can_restrict:
            await message.reply(f"""
{title_bar("AUTO MUTE", "⚠️")}
Group: {chat_title}
Status: LIMITED

💀 USERBOT ADMIN TAPI GAK PUNYA HAK RESTRICT MEMBERS!
CARA: Centang "Restrict Members" pada admin @{me.username}

{BRAND} 💀
""")
            return
        
    except Exception as e:
        await message.reply(f"❌ Error cek admin: {e}")
        return
    
    AUTOMUTE_GROUPS.add(chat_id)
    save_automute_groups(AUTOMUTE_GROUPS)
    
    await message.reply(f"""
{title_bar("AUTO MUTE", "🔇")}
Group: {chat_title}
Status: ENABLED

✅ AUTO MUTE ACTIVATED!
👑 Userbot adalah ADMIN dengan hak RESTRICT!

🔞 NSFW → MUTE 1 JAM
📢 PROMO → MUTE 30 MENIT
💀 SPAM → MUTE 10 MENIT

{BRAND} 💀
""")

async def cmd_automute_off(client, message):
    global AUTOMUTE_GROUPS
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Ketik di grup!")
        return
    
    chat_id = message.chat.id
    chat_title = message.chat.title or "Grup"
    AUTOMUTE_GROUPS.discard(chat_id)
    save_automute_groups(AUTOMUTE_GROUPS)
    await message.reply(f"{title_bar('AUTO MUTE', '❌')}\nAuto Mute DISABLED in {chat_title}\n{BRAND} 💀")

async def cmd_list_automute(client, message):
    if not AUTOMUTE_GROUPS:
        await message.reply(f"{title_bar('AUTO MUTE LIST', '📋')}\nNo active groups")
        return
    lines = []
    for gid in list(AUTOMUTE_GROUPS)[:30]:
        try:
            chat = await client.get_chat(gid)
            lines.append(f"▸ {chat.title}")
        except:
            lines.append(f"▸ ID: {gid}")
    await message.reply(f"{title_bar('AUTO MUTE LIST', '📋')}\nTotal: {len(AUTOMUTE_GROUPS)}\n" + "\n".join(lines))

# =============================================
# COMMAND: GBAN
# =============================================
async def cmd_gban(client, message):
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
        await message.reply("❌ `.gban @username` atau reply")
        return
    
    me = await client.get_me()
    if target_id == me.id:
        await message.reply("❌ Mau gban diri sendiri? 💀")
        return
    
    if target_id in GBAN_USERS:
        await message.reply(f"⚠️ {target_name} udah kena GBAN!")
        return
    
    status_msg = await message.reply(f"{title_bar('GBAN', '💀')}\nTarget: {target_name}\nProcessing...")
    
    result = await nuclear_global_ban(client, target_id, target_name)
    
    await status_msg.edit(f"{title_bar('GBAN DONE', '✅')}\nTarget: {target_name}\nReport: {'✅' if result['report'] else '⚠️'}\nBlocks: {result['blocks']}\n💀 TARGET TIDAK TAHU!\n{BRAND} 💀")
    
    try:
        await message.delete()
    except:
        pass

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
    
    await message.reply(f"{title_bar('UNGBAN', '✅')}\nUser {target_name} removed from GBAN!\n{BRAND} 💀")

async def cmd_listgban(client, message):
    if not GBAN_USERS:
        await message.reply(f"{title_bar('GBAN LIST', '📋')}\nNo victims yet")
        return
    user_list = []
    for uid in list(GBAN_USERS)[:30]:
        try:
            user = await client.get_users(uid)
            user_list.append(f"▸ {user.first_name} (@{user.username})")
        except:
            user_list.append(f"▸ ID: {uid}")
    await message.reply(f"{title_bar('GBAN LIST', '📋')}\nTotal: {len(GBAN_USERS)}\n" + "\n".join(user_list))

# =============================================
# COMMAND: WHITELIST & BLACKLIST (SINGKAT)
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
# COMMAND: TEST DETEKSI
# =============================================
async def cmd_test_detect(client, message):
    if not message.reply_to_message:
        await message.reply("❌ Reply ke pesan yang mau di test!")
        return
    
    text = message.reply_to_message.text or message.reply_to_message.caption or ""
    normalized = normalize_unicode_text(text)
    is_forbidden, content_type = ultra_detect(text)
    
    if is_forbidden:
        await message.reply(f"""
🔍 TEST RESULT:
━━━━━━━━━━━━━━━━━━━━━━━━
Original: `{text[:100]}`
Normalized: `{normalized[:100]}`
Status: 🚫 TERDETEKSI!
Type: {content_type.upper()}
Action: MUTED!
━━━━━━━━━━━━━━━━━━━━━━━━
""")
    else:
        await message.reply(f"""
🔍 TEST RESULT:
━━━━━━━━━━━━━━━━━━━━━━━━
Original: `{text[:100]}`
Normalized: `{normalized[:100]}`
Status: ✅ TIDAK TERDETEKSI
━━━━━━━━━━━━━━━━━━━━━━━━
""")

# =============================================
# ULTRA BRUTAL HANDLER - ZERO DELAY!
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
    
    # CEK GBAN - LANGSUNG BLOKIR
    if message.from_user.id in GBAN_USERS:
        try:
            await client.block_user(message.from_user.id)
        except:
            pass
        return
    
    chat_type = message.chat.type
    chat_id = message.chat.id
    
    # AUTO MUTE DI GRUP (ZERO DELAY!)
    if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        user_name = message.from_user.first_name or message.from_user.username or str(message.from_user.id)
        await check_and_auto_mute(client, chat_id, message.from_user.id, user_name, message)
    
    # AFK MODE
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
                    await message.reply("💀 SPAM! Blocked!")
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
    
    # GROUP CHAT - SUPER BRUTAL (ZERO DELAY!)
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
    return "💀 THE TAMERS NUCLEAR v8.0 - RUNNING 💀", 200

@app_flask.route("/ping", methods=["GET"])
def ping():
    return "pong", 200

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port, threaded=True)

# =============================================
# COMMAND AFK APPROVAL (SINGKAT)
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
                target_id = user.id
                target_name = user.first_name
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
    await message.reply(f"{title_bar('APPROVED', '✅')}\nUser {target_name} approved!\n{BRAND} 💀")

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
                target_id = user.id
                target_name = user.first_name
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
    await message.reply(f"{title_bar('REJECTED', '🚫')}\nUser {target_name} blocked!\n{BRAND} 💀")

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
    await message.reply(f"{title_bar('AFK PENDING', '📋')}\n" + "\n".join(lines))

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
                target_id = user.id
                target_name = user.first_name
            except:
                await message.reply(f"❌ Gak nemu: {inp}")
                return
    
    if not target_id:
        await message.reply("❌ `.unblock @username` atau reply")
        return
    
    try:
        await client.unblock_user(target_id)
        await message.reply(f"{title_bar('UNBLOCKED', '✅')}\nUser {target_name} unblocked!\n{BRAND} 💀")
        afk_pending_users.pop(target_id, None)
        afk_approved_users.discard(target_id)
    except Exception as e:
        await message.reply(f"❌ Gagal: {e}")

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
    
    print("=" * 50)
    print("💀 THE TAMERS v8.0 - ULTRA NSFW DETECTOR 💀")
    print("=" * 50)
    print(f"📋 GBAN: {len(GBAN_USERS)} victims")
    print(f"🔥 Super Brutal: {len(SUPERBRUTAL_GROUPS)} groups")
    print(f"🔇 Auto Mute: {len(AUTOMUTE_GROUPS)} groups")
    print("🔞 NSFW Detector: ULTRA SENSITIVE")
    print("⚡ Mode: ZERO DELAY")
    print("")
    
    session_string = os.getenv("SESSION_STRING")
    
    if session_string:
        print("🔑 Using String Session...")
        client = Client("userbot", session_string=session_string, api_id=API_ID, api_hash=API_HASH)
    else:
        print("❌ SESSION_STRING not found!")
        return
    
    try:
        await client.start()
        me = await client.get_me()
        print(f"✅ Login: {me.first_name} (@{me.username if me.username else '-'})")
        print("")
        
        # REGISTER COMMANDS
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
        async def _(c, m): pass
        
        @client.on_message(filters.me & filters.command("ucast_all", prefixes="."))
        async def _(c, m): pass
        
        @client.on_message(filters.me & filters.command("spam", prefixes="."))
        async def _(c, m): pass
        
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
        
        @client.on_message(filters.me & filters.command("testdetect", prefixes="."))
        async def _(c, m): await cmd_test_detect(c, m)
        
        @client.on_message(filters.incoming & ~filters.me)
        async def auto_reply(c, m):
            await ultra_brutal_handler(c, m)
        
        print("📌 ALL COMMANDS LOADED!")
        print("💀 ULTRA NSFW DETECTOR: ACTIVE!")
        print("⚡ ZERO DELAY MODE: ACTIVE!")
        print("")
        print(f"📌 Bot RUNNING on Railway!")
        print(f"📌 Press Ctrl+C to stop...")
        print("")
        
        while True:
            await asyncio.sleep(60)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 💀 THE TAMERS ACTIVE! 💀")
            print(f"   🔇 Auto Mute: {len(AUTOMUTE_GROUPS)} groups")
            
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
        print("\n💀 THE TAMERS HAS RISEN... Goodbye! 💀")
