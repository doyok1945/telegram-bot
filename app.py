"""
THE TAMERS USERBOT v13.0 - PREMIUM CLEAN EDITION
Tampilan keren tanpa garis kiri dan emoji dobel
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
import subprocess
import signal
import urllib.request
from datetime import datetime, timedelta
from typing import Set, Dict, List, Tuple
from flask import Flask, request
from concurrent.futures import ThreadPoolExecutor

from pyrogram import Client, filters
from pyrogram.errors import FloodWait, UserIsBlocked, PeerIdInvalid, SessionRevoked, RPCError
from pyrogram.types import Message, ChatPermissions, User
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
executor = ThreadPoolExecutor(max_workers=50)

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
BRAND = "THE TAMERS"
VERSION = "13.0.0"

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
# KEEP ALIVE
# =============================================
def keep_alive():
    port = int(os.environ.get("PORT", 8080))
    url = f"http://localhost:{port}/ping"
    while True:
        try:
            urllib.request.urlopen(url, timeout=5)
        except:
            pass
        time.sleep(180)

keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
keep_alive_thread.start()

# =============================================
# FUNGSI NORMALISASI TEKS
# =============================================
CHAR_MAP = {
    '0': 'o', '1': 'i', '3': 'e', '4': 'a', '5': 's', '7': 't', '8': 'b',
    'ᥱ': 'e', '⍴': 'p', 'о': 'o', '𝗇': 'n', 'α': 'a', 'ძ': 'd', 'і': 'i',
    '𝗇': 'n', '𝗎': 'u', '𝗅': 'l', '𝗄': 'k', '𝗆': 'm', '𝗁': 'h',
    '𝗌': 's', '𝗉': 'p', '𝗍': 't', '𝗐': 'w', '𝗒': 'y', '𝗑': 'x',
    '𝗓': 'z', '𝗰': 'c', '𝗏': 'v', '𝗯': 'b', '𝗴': 'g', '𝗷': 'j',
    '𝗾': 'q', '𝗿': 'r', '𝗳': 'f', '𝗱': 'd', '𝗲': 'e',
    'ᴘ': 'p', 'ʀ': 'r', 'ᴏ': 'o', 'ꜰ': 'f', 'ɪ': 'i', 'ʟ': 'l',
    'ᴇ': 'e', 'ᴄ': 'c', 'ᴋ': 'k', 'ᴠ': 'v', 'ʙ': 'b',
}

def normalize_unicode_text(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    for old, new in CHAR_MAP.items():
        text = text.replace(old, new)
    text = re.sub(r'[^a-z0-9\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'(.)\1{3,}', r'\1\1', text)
    return text

def ultra_detect(text: str) -> Tuple[bool, str]:
    if not text:
        return False, None
    
    normalized = normalize_unicode_text(text)
    
    nsfw_patterns = [
        r'𝚝𝚊𝚕𝚎𝚗𝚝', r'talent', r'vcs\s*ridi', r'vc\s*ridi', r'ridi',
        r'vvip', r'vip', r'sung\s*order', r'ngab',
        r'srbu', r'pciessss', r'prmowwwwwww', r'yugs\s*bub',
        r'snge', r'openvcees', r'colii', r'αძα', r'⍴rоmо',
        r'bohcil', r'fresh', r'cwokk', r'hyprr', r'viceess', r'angee',
        r'ngewe', r'ngentot', r'sex', r'seks', r'porn', r'bokep',
        r'memek', r'kontol', r'pepek', r'pap', r'nudes', r'18\+', r'hot',
    ]
    
    for pattern in nsfw_patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            return True, "nsfw"
        if re.search(pattern, text, re.IGNORECASE):
            return True, "nsfw"
    
    promo_patterns = [
        r'promosi', r'promo', r'iklan', r'jual', r'beli', r'toko',
        r'murmer', r'murah', r'diskon', r'followers', r'shopee',
    ]
    
    for pattern in promo_patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            return True, "promo"
    
    spam_patterns = [
        r'y+u+u+u?\s*c+h+a+t+t?', r'1c+w+o+o+o?', r'v+i+c+e+e+s+',
        r'l+i+m+i+t+t+', r'h+y+p+r+r+', r'd+m+', r'p+m+', r'sayang',
        r'mampir', r'talent', r'ridi', r'sung',
    ]
    
    for pattern in spam_patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            return True, "spam"
    
    if re.search(r'\d+[a-z]{3,}', normalized) and len(normalized) < 35:
        return True, "spam"
    if re.search(r'(chat|chatt|dm|pm|pc).*(yuk|yuu|ayoo)', normalized):
        return True, "spam"
    
    return False, None

# =============================================
# REPLIES
# =============================================
BRUTAL_REPLIES = ["💀 SPAM DETECTED", "💀 THE TAMERS DON'T TOLERATE SPAM"]
NSFW_REPLIES = ["💀 KONTEN DEWASA TERDETEKSI - MUTE 1 MINGGU", "🔞 NSFW DETECTED - MUTED 1 WEEK"]
PROMO_REPLIES = ["💀 PROMOSI DILARANG - MUTE 30 MENIT"]
MENTION_REPLIES_BRUTAL = ["💀 MENTION SPAM DETECTED - MUTE 1 MENIT"]
SIMPLE_REPLIES = ["💀 hmm", "💀 ya", "💀 Y", "💀 iyaaa", "💀 oke"]
MENTION_REPLIES = ["💀 hmm?", "💀 ya?", "💀 iyeee?", "💀 ada apa?"]
AFK_REPLY = "💀 THE TAMERS lagi AFK, sabar ya"

def get_brutal_reply(): return random.choice(BRUTAL_REPLIES)
def get_nsfw_reply(): return random.choice(NSFW_REPLIES)
def get_promo_reply(): return random.choice(PROMO_REPLIES)
def get_mention_spam_reply(): return random.choice(MENTION_REPLIES_BRUTAL)
def get_simple_reply(): return random.choice(SIMPLE_REPLIES)
def get_mention_reply(): return random.choice(MENTION_REPLIES)

# =============================================
# FUNGSI BANTUAN (TANPA GARIS KIRI)
# =============================================
def title_bar(text, icon="💀"):
    return f"{icon} {text}"

def progress_bar(current, total, width=20):
    if total == 0:
        return f"[{'░'*width}] 0%"
    persen = int(current / total * 100)
    filled = int(width * current / total)
    bar = "█" * filled + "░" * (width - filled)
    return f"[{bar}] {persen}%"

def get_uptime():
    elapsed = time.time() - BOT_START_TIME
    days = int(elapsed // 86400)
    hours = int((elapsed % 86400) // 3600)
    mins = int((elapsed % 3600) // 60)
    secs = int(elapsed % 60)
    if days > 0:
        return f"{days} days {hours} hours"
    elif hours > 0:
        return f"{hours} hours {mins} minutes"
    elif mins > 0:
        return f"{mins} minutes {secs} seconds"
    return f"{secs} seconds"

def get_system_stats():
    """Ambil statistik sistem real-time"""
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.5)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        return cpu, ram, disk
    except:
        return 0, 0, 0

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
                data = json.load(f)
                groups = set(data.get("automute_groups", []))
                groups = {int(g) for g in groups if isinstance(g, int) or str(g).isdigit()}
                return groups
        except:
            pass
    return set()

def save_automute_groups(groups):
    try:
        temp_file = f"{AUTOMUTE_FILE}.temp"
        with open(temp_file, "w") as f:
            json.dump({"automute_groups": list(groups)}, f, indent=4)
        os.replace(temp_file, AUTOMUTE_FILE)
        return True
    except:
        return False

def verify_automute_persistence():
    global AUTOMUTE_GROUPS
    if os.path.exists(AUTOMUTE_FILE):
        try:
            with open(AUTOMUTE_FILE, "r") as f:
                data = json.load(f)
                saved_groups = set(data.get("automute_groups", []))
                if saved_groups != AUTOMUTE_GROUPS:
                    AUTOMUTE_GROUPS = saved_groups
        except:
            pass

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
# AUTO MUTE FUNCTIONS
# =============================================
async def is_admin_group(client, chat_id, user_id):
    try:
        member = await client.get_chat_member(chat_id, user_id)
        status = str(member.status).lower() if member.status else ""
        if "administrator" in status or "owner" in status:
            return True
        return False
    except:
        return False

async def can_restrict_members(client, chat_id):
    try:
        me = await client.get_me()
        member = await client.get_chat_member(chat_id, me.id)
        if member.status == ChatMemberStatus.OWNER:
            return True
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            if member.privileges:
                return member.privileges.can_restrict_members
        return False
    except:
        return False

async def mute_user_group(client, chat_id, user_id, duration=300):
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
    if chat_id not in AUTOMUTE_GROUPS:
        return False
    
    if await is_admin_group(client, chat_id, user_id):
        return False
    
    if not await can_restrict_members(client, chat_id):
        return False
    
    text = message.text or message.caption or ""
    me = await client.get_me()
    
    is_forbidden, content_type = ultra_detect(text)
    
    mention_pattern = r'@[a-zA-Z0-9_]{3,}'
    mentions = re.findall(mention_pattern, text)
    bot_username = me.username if me.username else ""
    
    is_mention_spam = False
    if mentions:
        for mention in mentions:
            clean_mention = mention.replace('@', '')
            if clean_mention.lower() != bot_username.lower():
                is_mention_spam = True
                break
    
    if is_forbidden or is_mention_spam:
        if content_type == "nsfw":
            duration = 604800
            reply = get_nsfw_reply()
            mute_text = "1 MINGGU"
        elif content_type == "promo":
            duration = 1800
            reply = get_promo_reply()
            mute_text = "30 MENIT"
        elif is_mention_spam:
            duration = 60
            reply = get_mention_spam_reply()
            mute_text = "1 MENIT"
        else:
            duration = 600
            reply = get_brutal_reply()
            mute_text = "10 MENIT"
        
        try:
            await message.delete()
        except:
            pass
        
        if await mute_user_group(client, chat_id, user_id, duration):
            try:
                await message.reply(f"{reply}\n\n🔇 MUTED {mute_text}!")
            except:
                pass
            return True
    
    return False

# =============================================
# COMMAND: PING (REAL-TIME + KEREN)
# =============================================
async def cmd_ping(client, message):
    start = time.time()
    await asyncio.sleep(0.05)
    ping = int((time.time() - start) * 1000)
    me = await client.get_me()
    
    if ping < 50:
        status = "SUPER FAST 🚀"
        grade = "🌟"
    elif ping < 150:
        status = "GOOD ✅"
        grade = "⭐"
    elif ping < 300:
        status = "SLOW ⚠️"
        grade = "💫"
    else:
        status = "DEAD 💀"
        grade = "❌"
    
    cpu, ram, disk = get_system_stats()
    
    await message.reply(f"""
💀 𝐏𝐈𝐍𝐆 𝐑𝐄𝐒𝐔𝐋𝐓

📡 𝐑𝐞𝐬𝐩𝐨𝐧𝐬𝐞: {ping} ms
📊 𝐒𝐭𝐚𝐭𝐮𝐬: {status}
🎯 𝐆𝐫𝐚𝐝𝐞: {grade}
⏱️ 𝐔𝐩𝐭𝐢𝐦𝐞: {get_uptime()}

🖥️ 𝐒𝐲𝐬𝐭𝐞𝐦 𝐑𝐞𝐚𝐥-𝐓𝐢𝐦𝐞
• CPU Usage: {cpu}%
• RAM Usage: {ram}%
• Disk Usage: {disk}%

👤 𝐎𝐰𝐧𝐞𝐫: {me.first_name}
🆔 𝐈𝐃: {me.id}

{BRAND} 𝐯{𝐕𝐄𝐑𝐒𝐈𝐎𝐍} 💀
""")

# =============================================
# COMMAND: INFO (KEREN)
# =============================================
async def cmd_info(client, message):
    target_user = None
    
    if message.reply_to_message and message.reply_to_message.from_user:
        target_user = message.reply_to_message.from_user
    elif len(message.command) > 1:
        inp = message.command[1]
        try:
            target_user = await client.get_users(int(inp))
        except:
            if not inp.startswith('@'):
                inp = '@' + inp
            try:
                target_user = await client.get_users(inp)
            except:
                pass
    
    if not target_user:
        target_user = await client.get_me()
    
    first_name = target_user.first_name or "-"
    last_name = target_user.last_name or "-"
    username = f"@{target_user.username}" if target_user.username else "-"
    user_id = target_user.id
    is_premium = "✅ Yes" if getattr(target_user, 'is_premium', False) else "❌ No"
    is_bot = "✅ Yes" if target_user.is_bot else "❌ No"
    
    try:
        dc_id = target_user.dc_id if hasattr(target_user, 'dc_id') else "Unknown"
    except:
        dc_id = "Unknown"
    
    await message.reply(f"""
👤 𝐔𝐒𝐄𝐑 𝐈𝐍𝐅𝐎𝐑𝐌𝐀𝐓𝐈𝐎𝐍

📛 𝐍𝐚𝐦𝐞: {first_name} {last_name}
📱 𝐔𝐬𝐞𝐫𝐧𝐚𝐦𝐞: {username}
🆔 𝐔𝐬𝐞𝐫 𝐈𝐃: {user_id}
💎 𝐏𝐫𝐞𝐦𝐢𝐮𝐦: {is_premium}
🤖 𝐁𝐨𝐭: {is_bot}
🌐 𝐃𝐚𝐭𝐚 𝐂𝐞𝐧𝐭𝐞𝐫: {dc_id}

🔗 𝐏𝐫𝐨𝐟𝐢𝐥𝐞 𝐋𝐢𝐧𝐤: [Click Here](tg://user?id={user_id})

{BRAND} 𝐯{𝐕𝐄𝐑𝐒𝐈𝐎𝐍} 💀
""")

# =============================================
# COMMAND: STATUS (KEREN)
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
    
    cpu, ram, disk = get_system_stats()
    
    await message.reply(f"""
💀 𝐁𝐎𝐓 𝐒𝐓𝐀𝐓𝐔𝐒

👑 𝐎𝐰𝐧𝐞𝐫: {me.first_name}
🆔 𝐈𝐃: {me.id}
⏱️ 𝐔𝐩𝐭𝐢𝐦𝐞: {get_uptime()}

📊 𝐂𝐡𝐚𝐭 𝐒𝐭𝐚𝐭𝐢𝐬𝐭𝐢𝐜𝐬
• Private Chats: {total_users}
• Groups: {total_groups}
• Channels: {total_channels}

🎯 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬
• GBAN Victims: {len(GBAN_USERS)}
• Auto Mute: {len(AUTOMUTE_GROUPS)} groups
• Super Brutal: {len(SUPERBRUTAL_GROUPS)} groups
• Auto Reply: {len(WHITELIST_GROUPS)} groups
• Blacklist: {len(BLOCKED_GROUPS)} groups

🖥️ 𝐒𝐲𝐬𝐭𝐞𝐦
• CPU: {cpu}%
• RAM: {ram}%
• Disk: {disk}%

{BRAND} 𝐯{𝐕𝐄𝐑𝐒𝐈𝐎𝐍} 💀
""")

# =============================================
# COMMAND: DOWNLOAD ONCE MEDIA
# =============================================
async def cmd_download_once(client, message):
    if not message.reply_to_message:
        await message.reply("📸 Reply ke pesan foto/video sekali lihat")
        return
    
    replied = message.reply_to_message
    
    if not replied.photo and not replied.video:
        await message.reply("❌ Tidak ada foto/video yang bisa di-download")
        return
    
    try:
        status = await message.reply("📥 Downloading...")
        file_path = await replied.download()
        
        if replied.photo:
            await client.send_document(message.chat.id, file_path, caption=f"📸 Photo Once\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        elif replied.video:
            await client.send_video(message.chat.id, file_path, caption=f"🎬 Video Once\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        os.remove(file_path)
        await status.delete()
    except Exception as e:
        await message.reply(f"❌ Gagal: {e}")

# =============================================
# COMMAND: AFK & UNAFK
# =============================================
async def cmd_afk(client, message):
    global is_afk
    is_afk = True
    await message.reply(f"😴 𝐀𝐅𝐊 𝐌𝐎𝐃𝐄\n💀 Away! Type .unafk to back")

async def cmd_unafk(client, message):
    global is_afk
    is_afk = False
    await message.reply(f"✅ 𝐀𝐅𝐊 𝐌𝐎𝐃𝐄\n👋 Back!")

# =============================================
# COMMAND: SUPER BRUTAL
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
    await message.reply(f"🔥 𝐒𝐔𝐏𝐄𝐑 𝐁𝐑𝐔𝐓𝐀𝐋\n✅ {chat_title} - EVERY MESSAGE WILL BE REPLIED!")

async def cmd_superbrutal_off(client, message):
    global SUPERBRUTAL_GROUPS
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Ketik di grup!")
        return
    
    chat_id = message.chat.id
    chat_title = message.chat.title or "Grup"
    SUPERBRUTAL_GROUPS.discard(chat_id)
    save_superbrutal_groups(SUPERBRUTAL_GROUPS)
    await message.reply(f"❌ 𝐒𝐔𝐏𝐄𝐑 𝐁𝐑𝐔𝐓𝐀𝐋\nSuper Brutal DISABLED in {chat_title}")

async def cmd_list_superbrutal(client, message):
    if not SUPERBRUTAL_GROUPS:
        await message.reply("📋 No active super brutal groups")
        return
    lines = []
    for gid in list(SUPERBRUTAL_GROUPS)[:30]:
        try:
            chat = await client.get_chat(gid)
            lines.append(f"• {chat.title}")
        except:
            lines.append(f"• ID: {gid}")
    await message.reply(f"📋 𝐒𝐔𝐏𝐄𝐑 𝐁𝐑𝐔𝐓𝐀𝐋 𝐋𝐈𝐒𝐓\nTotal: {len(SUPERBRUTAL_GROUPS)}\n" + "\n".join(lines))

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
    
    try:
        member = await client.get_chat_member(chat_id, me.id)
        status = str(member.status).lower() if member.status else ""
        
        if "administrator" not in status and "owner" not in status:
            await message.reply(f"""
❌ 𝐀𝐔𝐓𝐎 𝐌𝐔𝐓𝐄
Group: {chat_title}
Status: FAILED

💀 USERBOT HARUS JADI ADMIN DULU!
📌 Jadikan @{me.username} sebagai admin dengan hak "Restrict Members"
""")
            return
        
        can_restrict = False
        if member.privileges:
            can_restrict = member.privileges.can_restrict_members
        
        if not can_restrict:
            await message.reply(f"""
⚠️ 𝐀𝐔𝐓𝐎 𝐌𝐔𝐓𝐄
Group: {chat_title}
Status: LIMITED

💀 USERBOT ADMIN TAPI GAK PUNYA HAK RESTRICT MEMBERS!
📌 Centang "Restrict Members" pada admin @{me.username}
""")
            return
        
    except Exception as e:
        await message.reply(f"❌ Error cek admin: {e}")
        return
    
    AUTOMUTE_GROUPS.add(chat_id)
    save_automute_groups(AUTOMUTE_GROUPS)
    
    await message.reply(f"""
🔇 𝐀𝐔𝐓𝐎 𝐌𝐔𝐓𝐄
Group: {chat_title}
Status: ENABLED

✅ AUTO MUTE ACTIVATED!
• NSFW → MUTE 1 MINGGU
• PROMO → MUTE 30 MENIT
• SPAM → MUTE 10 MENIT
• MENTION SPAM → MUTE 1 MENIT
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
    await message.reply(f"❌ 𝐀𝐔𝐓𝐎 𝐌𝐔𝐓𝐄\nAuto Mute DISABLED in {chat_title}")

async def cmd_list_automute(client, message):
    if not AUTOMUTE_GROUPS:
        await message.reply("📋 No active auto mute groups")
        return
    lines = []
    for gid in list(AUTOMUTE_GROUPS)[:30]:
        try:
            chat = await client.get_chat(gid)
            lines.append(f"• {chat.title}")
        except:
            lines.append(f"• ID: {gid}")
    await message.reply(f"📋 𝐀𝐔𝐓𝐎 𝐌𝐔𝐓𝐄 𝐋𝐈𝐒𝐓\nTotal: {len(AUTOMUTE_GROUPS)}\n" + "\n".join(lines))

async def cmd_check_automute(client, message):
    global AUTOMUTE_GROUPS
    reloaded = load_automute_groups()
    AUTOMUTE_GROUPS = reloaded
    
    groups_list = []
    for gid in list(AUTOMUTE_GROUPS)[:20]:
        try:
            chat = await client.get_chat(gid)
            groups_list.append(f"• {chat.title}")
        except:
            groups_list.append(f"• ID: {gid}")
    
    await message.reply(f"""
🔍 𝐀𝐔𝐓𝐎 𝐌𝐔𝐓𝐄 𝐒𝐓𝐀𝐓𝐔𝐒
• File: {'✅ OK' if os.path.exists(AUTOMUTE_FILE) else '❌ MISSING'}
• Memory: {len(AUTOMUTE_GROUPS)} groups
• File: {len(reloaded)} groups
• Active: {chr(10).join(groups_list) if groups_list else 'None'}
""")

# =============================================
# COMMAND: GCAST
# =============================================
async def cmd_gcast(client, message):
    pesan = None
    
    if message.reply_to_message:
        pesan = message.reply_to_message.text or message.reply_to_message.caption
    elif len(message.command) > 1:
        pesan = message.text.split(maxsplit=1)[1]
    else:
        await message.reply(f"""
❌ 𝐆𝐂𝐀𝐒𝐓
📌 .gcast <pesan> atau reply ke pesan
""")
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
        f"📢 𝐆𝐂𝐀𝐒𝐓\nTask: #{task_id}\nTarget: {total} groups\n{progress_bar(0, total)}\nProcessing..."
    )
    
    berhasil, gagal, processed = 0, 0, 0
    
    async for dialog in client.get_dialogs():
        chat = dialog.chat
        if chat.type in [ChatType.GROUP, ChatType.SUPERGROUP] and chat.id not in BLOCKED_GROUPS:
            try:
                await client.send_message(chat.id, pesan)
                berhasil += 1
            except:
                gagal += 1
            
            processed += 1
            if processed % 5 == 0 or processed == total:
                await status_msg.edit(
                    f"📢 𝐆𝐂𝐀𝐒𝐓\nTask: #{task_id}\nTarget: {total} groups\n{progress_bar(processed, total)}\n✅ {berhasil} | ❌ {gagal}\n{processed}/{total}"
                )
            await asyncio.sleep(0.2)
    
    elapsed = int(time.time() - start_time)
    success_rate = int(berhasil / total * 100) if total > 0 else 0
    
    await status_msg.edit(
        f"✅ 𝐆𝐂𝐀𝐒𝐓 𝐃𝐎𝐍𝐄\nTask: #{task_id}\nDuration: {elapsed}s\n✅ {berhasil} | ❌ {gagal} | Rate: {success_rate}%"
    )

# =============================================
# COMMAND: UCAST_ALL
# =============================================
async def cmd_ucast_all(client, message):
    pesan = None
    
    if message.reply_to_message:
        pesan = message.reply_to_message.text or message.reply_to_message.caption
    elif len(message.command) > 1:
        pesan = message.text.split(maxsplit=1)[1]
    else:
        await message.reply(f"""
❌ 𝐔𝐂𝐀𝐒𝐓
📌 .ucast_all <pesan> atau reply ke pesan
""")
        return
    
    if not pesan:
        await message.reply("❌ Pesan kosong!")
        return
    
    try:
        await message.delete()
    except:
        pass
    
    total = 0
    me = await client.get_me()
    async for dialog in client.get_dialogs():
        if dialog.chat.type == ChatType.PRIVATE and dialog.chat.id > 0 and dialog.chat.id != me.id:
            total += 1
    
    if total == 0:
        await client.send_message(message.chat.id, "❌ Gak ada private chat!")
        return
    
    task_id = random.randint(1000, 9999)
    start_time = time.time()
    
    status_msg = await client.send_message(
        message.chat.id,
        f"📨 𝐔𝐂𝐀𝐒𝐓\nTask: #{task_id}\nTarget: {total} users\n{progress_bar(0, total)}\nProcessing..."
    )
    
    berhasil, gagal, diblokir, processed = 0, 0, 0, 0
    
    async for dialog in client.get_dialogs():
        if dialog.chat.type == ChatType.PRIVATE and dialog.chat.id > 0 and dialog.chat.id != me.id:
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
                    f"📨 𝐔𝐂𝐀𝐒𝐓\nTask: #{task_id}\nTarget: {total} users\n{progress_bar(processed, total)}\n✅ {berhasil} | ❌ {gagal} | 🚫 {diblokir}\n{processed}/{total}"
                )
            await asyncio.sleep(0.3)
    
    elapsed = int(time.time() - start_time)
    success_rate = int(berhasil / total * 100) if total > 0 else 0
    
    await status_msg.edit(
        f"✅ 𝐔𝐂𝐀𝐒𝐓 𝐃𝐎𝐍𝐄\nTask: #{task_id}\nDuration: {elapsed}s\n✅ {berhasil} | ❌ {gagal} | 🚫 {diblokir} | Rate: {success_rate}%"
    )

# =============================================
# COMMAND: SPAM
# =============================================
async def cmd_spam(client, message):
    if len(message.command) < 3 and not message.reply_to_message:
        await message.reply(f"❌ 𝐒𝐏𝐀𝐌\n📌 .spam <jumlah> <pesan> atau reply ke pesan")
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
    
    status = await message.reply(f"🔄 𝐒𝐏𝐀𝐌\nSpamming {count} messages...\n{progress_bar(0, count)}")
    await message.delete()
    
    for i in range(count):
        await client.send_message(message.chat.id, teks)
        await asyncio.sleep(0.1)
        
        if (i + 1) % 10 == 0 or (i + 1) == count:
            await status.edit(f"🔄 𝐒𝐏𝐀𝐌\nSpamming {count} messages...\n{progress_bar(i + 1, count)}")
    
    await status.edit(f"✅ 𝐒𝐏𝐀𝐌 𝐃𝐎𝐍𝐄\nSent {count} messages!")

# =============================================
# COMMAND: GBAN
# =============================================
async def nuclear_global_ban(client, user_id):
    try:
        await client.send_message("SpamBot", f"/report {user_id} spam")
        await asyncio.sleep(0.3)
        report_ok = True
    except:
        report_ok = False
    
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
        await message.reply("❌ Mau gban diri sendiri?")
        return
    
    if target_id in GBAN_USERS:
        await message.reply(f"⚠️ {target_name} udah kena GBAN!")
        return
    
    status_msg = await message.reply(f"💀 𝐆𝐁𝐀𝐍\nTarget: {target_name}\nProcessing...")
    result = await nuclear_global_ban(client, target_id)
    await status_msg.edit(f"✅ 𝐆𝐁𝐀𝐍 𝐃𝐎𝐍𝐄\nTarget: {target_name}\nReport: {'✅' if result['report'] else '⚠️'}\nBlocks: {result['blocks']}\n💀 TARGET TIDAK TAHU!")
    
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
    await message.reply(f"✅ 𝐔𝐍𝐆𝐁𝐀𝐍\nUser {target_name} removed from GBAN!")

async def cmd_listgban(client, message):
    if not GBAN_USERS:
        await message.reply("📋 No GBAN victims yet")
        return
    user_list = []
    for uid in list(GBAN_USERS)[:30]:
        try:
            user = await client.get_users(uid)
            user_list.append(f"• {user.first_name} (@{user.username})")
        except:
            user_list.append(f"• ID: {uid}")
    await message.reply(f"📋 𝐆𝐁𝐀𝐍 𝐋𝐈𝐒𝐓\nTotal: {len(GBAN_USERS)}\n" + "\n".join(user_list))

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
    await message.reply(f"✅ 𝐀𝐔𝐓𝐎 𝐑𝐄𝐏𝐋𝐘\nAuto reply ENABLED in {title}")

async def cmd_grup_off(client, message):
    global WHITELIST_GROUPS
    if message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await message.reply("❌ Ketik di grup!")
        return
    cid, title = message.chat.id, message.chat.title or "Grup"
    WHITELIST_GROUPS.discard(cid)
    save_whitelist(WHITELIST_GROUPS)
    await message.reply(f"❌ 𝐀𝐔𝐓𝐎 𝐑𝐄𝐏𝐋𝐘\nAuto reply DISABLED in {title}")

async def cmd_list_whitelist(client, message):
    if not WHITELIST_GROUPS:
        await message.reply("📋 No groups with auto reply enabled")
        return
    lines = []
    for gid in list(WHITELIST_GROUPS)[:30]:
        try:
            chat = await client.get_chat(gid)
            lines.append(f"• {chat.title}")
        except:
            lines.append(f"• ID: {gid}")
    await message.reply(f"📋 𝐀𝐔𝐓𝐎 𝐑𝐄𝐏𝐋𝐘 𝐆𝐑𝐎𝐔𝐏𝐒\nTotal: {len(WHITELIST_GROUPS)}\n" + "\n".join(lines))

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
    await message.reply(f"🚫 𝐁𝐋𝐀𝐂𝐊𝐋𝐈𝐒𝐓𝐄𝐃\n{title} added to blacklist!")

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
    await message.reply(f"✅ 𝐑𝐄𝐌𝐎𝐕𝐄𝐃\n{title} removed from blacklist!")

async def cmd_listbl(client, message):
    if not BLOCKED_GROUPS:
        await message.reply("📋 No blacklisted groups")
        return
    lines = []
    for gid in list(BLOCKED_GROUPS)[:20]:
        try:
            chat = await client.get_chat(gid)
            lines.append(f"• {chat.title}")
        except:
            lines.append(f"• ID: {gid}")
    await message.reply(f"📋 𝐁𝐋𝐀𝐂𝐊𝐋𝐈𝐒𝐓\nTotal: {len(BLOCKED_GROUPS)}\n" + "\n".join(lines))

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
🔍 𝐓𝐄𝐒𝐓 𝐑𝐄𝐒𝐔𝐋𝐓
Original: {text[:100]}
Normalized: {normalized[:100]}
Status: 🚫 DETECTED
Type: {content_type.upper()}
Action: WILL BE MUTED!
""")
    else:
        await message.reply(f"""
🔍 𝐓𝐄𝐒𝐓 𝐑𝐄𝐒𝐔𝐋𝐓
Original: {text[:100]}
Normalized: {normalized[:100]}
Status: ✅ NOT DETECTED
""")

# =============================================
# COMMAND: REFRESH BOT
# =============================================
async def cmd_refresh(client, message):
    await message.reply(f"🔄 𝐑𝐄𝐅𝐑𝐄𝐒𝐇\n💀 Bot akan di-restart dalam 3 detik!")
    
    save_automute_groups(AUTOMUTE_GROUPS)
    save_superbrutal_groups(SUPERBRUTAL_GROUPS)
    save_whitelist(WHITELIST_GROUPS)
    save_blacklist(BLOCKED_GROUPS)
    save_gban_list(GBAN_USERS)
    save_settings(settings)
    
    await asyncio.sleep(3)
    os._exit(99)

# =============================================
# COMMAND: BOT STATUS
# =============================================
async def cmd_botstatus(client, message):
    me = await client.get_me()
    await message.reply(f"""
💀 𝐁𝐎𝐓 𝐒𝐓𝐀𝐓𝐔𝐒
• Bot: @{me.username}
• Uptime: {get_uptime()}
• Handler: ACTIVE

📊 𝐅𝐞𝐚𝐭𝐮𝐫𝐞𝐬
• Auto Mute: {len(AUTOMUTE_GROUPS)} groups
• Super Brutal: {len(SUPERBRUTAL_GROUPS)} groups
• Auto Reply: {len(WHITELIST_GROUPS)} groups
• Blacklist: {len(BLOCKED_GROUPS)} groups
• GBAN Victims: {len(GBAN_USERS)}
""")

# =============================================
# COMMAND: HELP (SIMPEL TAPI KEREN)
# =============================================
async def cmd_help(client, message):
    help_text = f"""
💀 𝐓𝐇𝐄 𝐓𝐀𝐌𝐄𝐑𝐒 𝐂𝐎𝐌𝐌𝐀𝐍𝐃𝐒

⚡ 𝐁𝐀𝐒𝐈𝐂
• .ping - Cek kecepatan & sistem
• .status - Status bot lengkap
• .info - Info akun sendiri
• .info @user - Info user lain
• .info (reply) - Info user yang di-reply
• .botstatus - Status bot realtime
• .afk / .unafk - Mode AFK
• .refresh - Restart bot

🔇 𝐀𝐔𝐓𝐎 𝐌𝐔𝐓𝐄
• .automute on - Aktifkan auto mute di grup
• .automute off - Nonaktifkan auto mute
• .listautomute - Lihat grup auto mute
• .checkautomute - Cek status auto mute
• .testdetect - Test deteksi pesan

🔥 𝐒𝐔𝐏𝐄𝐑 𝐁𝐑𝐔𝐓𝐀𝐋
• .superbrutal on - Balas SEMUA pesan di grup
• .superbrutal off - Nonaktifkan super brutal
• .listsuperbrutal - Lihat grup super brutal

🤖 𝐀𝐔𝐓𝐎 𝐑𝐄𝐏𝐋𝐘
• .grup on - Auto reply di grup
• .grup off - Nonaktifkan auto reply grup
• .private on - Auto reply private chat
• .private off - Nonaktifkan private reply
• .listgrup - Lihat grup auto reply

🚫 𝐁𝐋𝐀𝐂𝐊𝐋𝐈𝐒𝐓
• .addbl - Blacklist grup ini
• .rmbl - Hapus grup dari blacklist
• .listbl - Lihat daftar blacklist

📢 𝐁𝐑𝐎𝐀𝐃𝐂𝐀𝐒𝐓
• .gcast <pesan> - Broadcast ke semua grup
• .gcast (reply) - Broadcast pesan yang di-reply
• .ucast_all <pesan> - Broadcast ke semua private chat
• .ucast_all (reply) - Broadcast pesan yang di-reply
• .spam <jml> <pesan> - Spam ke grup

💀 𝐆𝐁𝐀𝐍
• .gban @user/reply - GBAN user (silent)
• .ungban @user/reply - Hapus dari GBAN
• .listgban - Lihat korban GBAN

📸 𝐌𝐄𝐃𝐈𝐀
• .downloadonce (reply) - Download foto/video sekali lihat

🎯 𝐃𝐄𝐓𝐄𝐂𝐓𝐈𝐎𝐍 𝐑𝐔𝐋𝐄𝐒
• 🔞 NSFW → MUTE 1 MINGGU
• 📢 PROMO → MUTE 30 MENIT
• 💀 SPAM → MUTE 10 MENIT
• 👤 MENTION SPAM → MUTE 1 MENIT

{BRAND} 𝐯{𝐕𝐄𝐑𝐒𝐈𝐎𝐍} 💀
"""
    await message.reply(help_text)

# =============================================
# COMMAND: AFK APPROVAL
# =============================================
async def cmd_approve(client, message):
    global afk_pending_users, afk_approved_users
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
        await message.reply("❌ `.acc @username` atau reply")
        return
    
    afk_approved_users.add(target_id)
    afk_pending_users.pop(target_id, None)
    try:
        await client.unblock_user(target_id)
    except:
        pass
    await message.reply(f"✅ 𝐀𝐏𝐏𝐑𝐎𝐕𝐄𝐃\nUser {target_name} approved!")

async def cmd_reject(client, message):
    global afk_pending_users, afk_approved_users
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
        await message.reply("❌ `.reject @username` atau reply")
        return
    
    try:
        await client.block_user(target_id)
    except:
        pass
    
    afk_pending_users.pop(target_id, None)
    afk_approved_users.discard(target_id)
    await message.reply(f"🚫 𝐑𝐄𝐉𝐄𝐂𝐓𝐄𝐃\nUser {target_name} blocked!")

async def cmd_afklist(client, message):
    if not afk_pending_users:
        await message.reply("📋 No pending users")
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
    await message.reply(f"📋 𝐀𝐅𝐊 𝐏𝐄𝐍𝐃𝐈𝐍𝐆\n" + "\n".join(lines))

async def cmd_unblock_user(client, message):
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
        await message.reply("❌ `.unblock @username` atau reply")
        return
    
    try:
        await client.unblock_user(target_id)
        await message.reply(f"✅ 𝐔𝐍𝐁𝐋𝐎𝐂𝐊𝐄𝐃\nUser {target_name} unblocked!")
        afk_pending_users.pop(target_id, None)
        afk_approved_users.discard(target_id)
    except Exception as e:
        await message.reply(f"❌ Gagal: {e}")

# =============================================
# ULTRA BRUTAL HANDLER
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
    
    if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        user_name = message.from_user.first_name or message.from_user.username or str(message.from_user.id)
        await check_and_auto_mute(client, chat_id, message.from_user.id, user_name, message)
    
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
    
    if chat_type == ChatType.PRIVATE:
        settings_local = load_settings()
        if settings_local.get("auto_reply_private", True):
            await message.reply(get_brutal_reply())
        return
    
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
    return "THE TAMERS v13.0 - RUNNING", 200

@app_flask.route("/ping", methods=["GET"])
def ping():
    return "pong", 200

@app_flask.route("/health", methods=["GET"])
def health():
    return "OK", 200

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
    print("💀 THE TAMERS v13.0 - PREMIUM CLEAN EDITION 💀")
    print("=" * 60)
    print(f"GBAN: {len(GBAN_USERS)} victims")
    print(f"Super Brutal: {len(SUPERBRUTAL_GROUPS)} groups")
    print(f"Auto Mute: {len(AUTOMUTE_GROUPS)} groups")
    print("")
    
    session_string = os.getenv("SESSION_STRING")
    
    if session_string:
        print("Using String Session...")
        client = Client("userbot", session_string=session_string, api_id=API_ID, api_hash=API_HASH)
    else:
        print("SESSION_STRING not found!")
        return
    
    try:
        await client.start()
        me = await client.get_me()
        print(f"Login: {me.first_name} (@{me.username if me.username else '-'})")
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
        
        @client.on_message(filters.me & filters.command("refresh", prefixes="."))
        async def _(c, m): await cmd_refresh(c, m)
        
        @client.on_message(filters.me & filters.command("downloadonce", prefixes="."))
        async def _(c, m): await cmd_download_once(c, m)
        
        @client.on_message(filters.me & filters.command("botstatus", prefixes="."))
        async def _(c, m): await cmd_botstatus(c, m)
        
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
        
        @client.on_message(filters.me & filters.command("checkautomute", prefixes="."))
        async def _(c, m): await cmd_check_automute(c, m)
        
        @client.on_message(filters.me & filters.command("testdetect", prefixes="."))
        async def _(c, m): await cmd_test_detect(c, m)
        
        @client.on_message(filters.me & filters.command("help", prefixes="."))
        async def _(c, m): await cmd_help(c, m)
        
        @client.on_message(filters.incoming & ~filters.me)
        async def auto_reply(c, m):
            await ultra_brutal_handler(c, m)
        
        print("ALL COMMANDS LOADED!")
        print("BOT RUNNING!")
        print("")
        
        while True:
            await asyncio.sleep(60)
            verify_automute_persistence()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] THE TAMERS ACTIVE - Auto Mute: {len(AUTOMUTE_GROUPS)} groups")
            
    except Exception as e:
        print(f"Error: {e}")
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
        print("\nTHE TAMERS HAS RISEN... Goodbye!")
    except SystemExit as e:
        if e.code == 99:
            print("\nREFRESHING BOT... RESTARTING...")
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            raise
