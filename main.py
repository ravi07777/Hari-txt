import os
import re
import sys
import m3u8
import json
import time
import pytz
import asyncio
import requests
import subprocess
import urllib
import urllib.parse
import yt_dlp
import tgcrypto
import cloudscraper
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from base64 import b64encode, b64decode
from logs import logging
from bs4 import BeautifulSoup
import saini as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN
from aiohttp import ClientSession
from subprocess import getstatusoutput
from aiohttp import web
import random
from pyromod import listen
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import aiohttp
import aiofiles
import zipfile
import shutil
import ffmpeg
import saini

# Decrypt helper import
from saini import decrypt_file_txt

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

cookies_file_path = os.getenv("cookies_file_path", "youtube_cookies.txt")
api_url = "http://master-api-v3.vercel.app/"
api_token = os.environ.get("API_TOKEN", "")   # moved to env var
token_cp  = os.environ.get("TOKEN_CP", "")    # moved to env var
adda_token = os.environ.get("ADDA_TOKEN", "") # moved to env var

photologo = 'https://tinypic.host/images/2025/02/07/DeWatermark.ai_1738952933236-1.png'
photoyt   = 'https://tinypic.host/images/2025/03/18/YouTube-Logo.wine.png'
photocp   = 'https://tinypic.host/images/2025/03/28/IMG_20250328_133126.jpg'
photozip  = 'https://envs.sh/cD_.jpg'

async def show_random_emojis(message):
    emojis = ['🐼','🐶','🐅','⚡️','🚀','✨','💥','☠️','🥂','🍾','📬','👻','👀','🌹','💀','🐇','⏳','🔮','🦔','📖','🦁','🐱','🐻‍❄️','☁️','🚹','🚺','🐠','🦋']
    emoji_message = await message.reply_text(' '.join(random.choices(emojis, k=1)))
    return emoji_message

# Inline keyboards
BUTTONSCONTACT = InlineKeyboardMarkup([[InlineKeyboardButton(text="📞 Contact", url="https://t.me/saini_contact_bot")]])
keyboard = InlineKeyboardMarkup(
    [[
        InlineKeyboardButton(text="📞 Contact", url="https://t.me/saini_contact_bot"),
        InlineKeyboardButton(text="🛠️ Help",    url="https://t.me/+3k-1zcJxINYwNGZl"),
    ]]
)

image_urls = [
    "https://tinypic.host/images/2025/02/07/IMG_20250207_224444_975.jpg",
    "https://tinypic.host/images/2025/02/07/DeWatermark.ai_1738952933236-1.png",
]

# ─────────────────────────────────────────────
# /cookies  – update youtube cookies file
# ─────────────────────────────────────────────
@bot.on_message(filters.command("cookies") & filters.private)
async def cookies_handler(client: Client, m: Message):
    await m.reply_text("Please upload the cookies file (.txt format).", quote=True)
    try:
        input_message: Message = await client.listen(m.chat.id)
        if not input_message.document or not input_message.document.file_name.endswith(".txt"):
            await m.reply_text("Invalid file type. Please upload a .txt file.")
            return
        downloaded_path = await input_message.download()
        with open(downloaded_path, "r") as uploaded_file:
            cookies_content = uploaded_file.read()
        with open(cookies_file_path, "w") as target_file:
            target_file.write(cookies_content)
        await input_message.reply_text("✅ Cookies updated successfully.\n📂 Saved in `youtube_cookies.txt`.")
    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")

# ─────────────────────────────────────────────
# /t2t  – text → .txt file
# ─────────────────────────────────────────────
@bot.on_message(filters.command(["t2t"]))
async def text_to_txt(client, message: Message):
    editable = await message.reply_text("<blockquote>Welcome to the Text to .txt Converter!\nSend the **text** for convert into a `.txt` file.</blockquote>")
    input_message: Message = await bot.listen(message.chat.id)
    if not input_message.text:
        await message.reply_text("🚨 **error**: Send valid text data")
        return
    text_data = input_message.text.strip()
    await input_message.delete()
    await editable.edit("**🔄 Send file name or send /d for filename**")
    inputn: Message = await bot.listen(message.chat.id)
    raw_textn = inputn.text
    await inputn.delete()
    await editable.delete()
    custom_file_name = 'txt_file' if raw_textn == '/d' else raw_textn
    txt_file = os.path.join("downloads", f'{custom_file_name}.txt')
    os.makedirs(os.path.dirname(txt_file), exist_ok=True)
    with open(txt_file, 'w') as f:
        f.write(text_data)
    await message.reply_document(document=txt_file, caption=f"`{custom_file_name}.txt`\n\nYou can now download your content! 📥")
    os.remove(txt_file)

# ─────────────────────────────────────────────
# /y2t  – YouTube playlist/video → .txt file
# ─────────────────────────────────────────────
@bot.on_message(filters.command(["y2t"]))
async def youtube_to_txt(client, message: Message):
    editable = await message.reply_text("Send YouTube Website/Playlist link for convert in .txt file")
    input_message: Message = await bot.listen(message.chat.id)
    youtube_link = input_message.text.strip()
    await input_message.delete(True)
    await editable.delete(True)
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'force_generic_extractor': True,
        'forcejson': True,
        'cookies': 'youtube_cookies.txt'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(youtube_link, download=False)
            title = result.get('title', 'youtube_playlist') if 'entries' in result else result.get('title', 'youtube_video')
        except yt_dlp.utils.DownloadError as e:
            await message.reply_text(f"<pre><code>🚨 Error occurred {str(e)}</code></pre>")
            return
    videos = []
    if 'entries' in result:
        for entry in result['entries']:
            videos.append(f"{entry.get('title','No title')}: {entry['url']}")
    else:
        videos.append(f"{result.get('title','No title')}: {result['url']}")
    txt_file = os.path.join("downloads", f'{title}.txt')
    os.makedirs(os.path.dirname(txt_file), exist_ok=True)
    with open(txt_file, 'w') as f:
        f.write('\n'.join(videos))
    await message.reply_document(document=txt_file, caption=f'<a href="{youtube_link}">__**Click Here to Open Link**__</a>\n<pre><code>{title}.txt</code></pre>\n')
    os.remove(txt_file)

# ─────────────────────────────────────────────
# /getcookies  – send cookies file to owner
# ─────────────────────────────────────────────
m_file_path = "main.py"

@bot.on_message(filters.command("getcookies") & filters.private)
async def getcookies_handler(client: Client, m: Message):
    try:
        await client.send_document(chat_id=m.chat.id, document=cookies_file_path, caption="Here is the `youtube_cookies.txt` file.")
    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")

@bot.on_message(filters.command("mfile") & filters.private)
async def mfile_handler(client: Client, m: Message):
    try:
        await client.send_document(chat_id=m.chat.id, document=m_file_path, caption="Here is the `main.py` file.")
    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")

# ─────────────────────────────────────────────
# /stop  – restart the bot process
# ─────────────────────────────────────────────
@bot.on_message(filters.command(["stop"]))
async def restart_handler(_, m):
    await m.reply_text("**ˢᵗᵒᵖᵖᵉᵈ ᵇᵃᵇʸ**", True)
    os.execl(sys.executable, sys.executable, *sys.argv)

# ─────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────
@bot.on_message(filters.command(["start"]))
async def start_command(bot: Client, message: Message):
    random_image_url = random.choice(image_urls)
    caption = (
        "𝐇𝐞𝐥𝐥𝐨 𝐃𝐞𝐚𝐫 👋!\n\n➠ 𝐈 𝐚𝐦 𝐚 𝐓𝐞𝐱𝐭 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐞𝐫 𝐁𝐨𝐭\n\n"
        "➠ Can Extract Videos & PDFs From Your Text File and Upload to Telegram!\n\n"
        "➠ For Guide Use Command /help 📖\n\n➠ 𝐌𝐚𝐝𝐞 𝐁𝐲 : 𝙎𝘼𝙄𝙉𝙄 𝘽𝙊𝙏𝙎 🦁"
    )
    await bot.send_photo(chat_id=message.chat.id, photo=random_image_url, caption=caption, reply_markup=keyboard)

# ─────────────────────────────────────────────
# /id
# ─────────────────────────────────────────────
@bot.on_message(filters.command(["id"]))
async def id_command(client, message: Message):
    await message.reply_text(f"<blockquote>The ID of this chat is:</blockquote>\n`{message.chat.id}`")

# ─────────────────────────────────────────────
# /info
# ─────────────────────────────────────────────
@bot.on_message(filters.private & filters.command(["info"]))
async def info(bot: Client, update: Message):
    text = (
        f"╭────────────────╮\n"
        f"│✨ **__Your Telegram Info__**✨ \n"
        f"├────────────────\n"
        f"├🔹**Name :** `{update.from_user.first_name} {update.from_user.last_name if update.from_user.last_name else 'None'}`\n"
        f"├🔹**User ID :** @{update.from_user.username}\n"
        f"├🔹**TG ID :** `{update.from_user.id}`\n"
        f"├🔹**Profile :** {update.from_user.mention}\n"
        f"╰────────────────╯"
    )
    await update.reply_text(text=text, disable_web_page_preview=True, reply_markup=BUTTONSCONTACT)

# ─────────────────────────────────────────────
# /help
# ─────────────────────────────────────────────
@bot.on_message(filters.command(["help"]))
async def help_handler(client: Client, m: Message):
    await bot.send_message(m.chat.id, text=(
        "🎉Congrats! You are using 𝙎𝘼𝙄𝙉𝙄 𝘽𝙊𝙏𝙎:\n\n"
        "✦**Available Commands Here**✦\n\n"
        "┣⪼01. /start - To Alive Check Bot \n"
        "┣⪼02. /drm - for extract txt file\n"
        "┣⪼03. /y2t - YouTube to .txt Convert\n"
        "┣⪼04. /t2t - text to .txt Convert\n"
        "┣⪼05. /logs - To see Bot Working Logs\n"
        "┣⪼06. /cookies - To update YT cookies.\n"
        "┣⪼07. /id - Know chat/group/channel ID.\n"
        "┣⪼08. /info - Your information.\n"
        "┣⪼09. /stop - Stop the Running Task. 🚫\n"
        "╰⪼🔗  Direct Send Link For Extract (with https://)\n\n"
        "**If you have any questions, feel free to ask [𝙎𝘼𝙄𝙉𝙄 𝘽𝙊𝙏𝙎🐦](https://t.me/+MdZ2996M2G43MWFl)! 💬**\n"
    ))

# ─────────────────────────────────────────────
# /logs
# ─────────────────────────────────────────────
@bot.on_message(filters.command(["logs"]))
async def send_logs(client: Client, m: Message):
    try:
        with open("logs.txt", "rb") as file:
            sent = await m.reply_text("**📤 Sending you ....**")
            await m.reply_document(document=file)
            await sent.delete()
    except Exception as e:
        await m.reply_text(f"Error sending logs: {e}")

# ─────────────────────────────────────────────
# /drm  – main txt downloader
# ─────────────────────────────────────────────
@bot.on_message(filters.command(["drm"]))
async def drm_handler(bot: Client, m: Message):
    editable = await m.reply_text("`🔹Hi I am Powerful TXT Downloader📥 Bot.\n🔹Send me the txt file and wait.`")
    input_msg: Message = await bot.listen(editable.chat.id)
    y = await input_msg.download()
    await input_msg.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(y))

    if file_name.endswith("_helper"):
        x = decrypt_file_txt(y)
    else:
        x = y

    path = f"./downloads/{m.chat.id}"
    pdf_count = img_count = zip_count = other_count = 0

    try:
        with open(x, "r") as f:
            content = f.read()
        content = content.split("\n")
        links = []
        for i in content:
            if "://" in i:
                url = i.split("://", 1)[1]
                links.append(i.split("://", 1))
                if ".pdf" in url:
                    pdf_count += 1
                elif url.endswith((".png", ".jpeg", ".jpg")):
                    img_count += 1
                elif ".zip" in url:
                    zip_count += 1
                else:
                    other_count += 1
        os.remove(x)
    except Exception:
        await m.reply_text("<pre><code>🔹Invalid file input.</code></pre>")
        if os.path.exists(x):
            os.remove(x)
        return

    await editable.edit(f"`🔹Total 🔗 links found are {len(links)}\n\n🔹Img : {img_count}  🔹PDF : {pdf_count}\n🔹ZIP : {zip_count}  🔹Other : {other_count}\n\n🔹Send From where you want to download.`")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)

    await editable.edit("`🔹Enter Your Batch Name\n🔹Send 1 for use default.`")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    b_name = file_name.replace('_', ' ') if raw_text0 == '1' else raw_text0

    await editable.edit("╭━━━━❰ᴇɴᴛᴇʀ ʀᴇꜱᴏʟᴜᴛɪᴏɴ❱━━➣ \n┣━━⪼ send `144`  for 144p\n┣━━⪼ send `240`  for 240p\n┣━━⪼ send `360`  for 360p\n┣━━⪼ send `480`  for 480p\n┣━━⪼ send `720`  for 720p\n┣━━⪼ send `1080` for 1080p\n╰━━⌈⚡[`🦋🇸‌🇦‌🇮‌🇳‌🇮‌🦋`]⚡⌋━━➣")
    input2: Message = await bot.listen(editable.chat.id)
    raw_text2 = input2.text
    quality = f"{raw_text2}p"
    await input2.delete(True)
    res_map = {"144": "256x144", "240": "426x240", "360": "640x360", "480": "854x480", "720": "1280x720", "1080": "1920x1080"}
    res = res_map.get(raw_text2, "UN")

    await editable.edit("`🔹Enter Your Name\n🔹Send 1 for use default`")
    input3: Message = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    CR = '[𝙎𝘼𝙄𝙉𝙄 𝘽𝙊𝙏𝙎🐦](https://t.me/+MdZ2996M2G43MWFl)' if raw_text3 == '1' else raw_text3

    await editable.edit("__**🔹Enter Your PW Token For 𝐌𝐏𝐃 𝐔𝐑𝐋, for default Send anything**__")
    input4: Message = await bot.listen(editable.chat.id)
    raw_text4 = input4.text
    await input4.delete(True)

    await editable.edit("Send the Video Thumb URL (e.g., https://envs.sh/GV0.jpg) for default thumbnail /d\n\n<i>You can direct upload thumb\nFor document format send : No</i>", disable_web_page_preview=True)
    input6: Message = await bot.listen(editable.chat.id)
    raw_text6 = input6.text if input6.text else ""
    await input6.delete(True)

    if input6.photo:
        thumb = await input6.download()
    elif raw_text6.startswith("http://") or raw_text6.startswith("https://"):
        getstatusoutput(f"wget '{raw_text6}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = raw_text6

    await editable.delete()
    await m.reply_text(f"`🎯Target Batch : {b_name}`")

    failed_count = 0
    count = int(raw_text)
    arg = int(raw_text)

    try:
        for i in range(arg - 1, len(links)):
            Vxy = (links[i][1]
                   .replace("file/d/", "uc?export=download&id=")
                   .replace("www.youtube-nocookie.com/embed", "youtu.be")
                   .replace("?modestbranding=1", "")
                   .replace("/view?usp=sharing", ""))
            url   = "https://" + Vxy
            link0 = "https://" + Vxy

            name1 = (links[i][0]
                     .replace("(", "[").replace(")", "]").replace("_", "")
                     .replace("\t", "").replace(":", "").replace("/", "")
                     .replace("+", "").replace("#", "").replace("|", "")
                     .replace("@", "").replace("*", "").replace(".", "")
                     .replace("https", "").replace("http", "").strip())
            name = f'{name1[:60]}'

            # ── Special URL rewrites ──────────────────────────────
            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Referer': 'http://www.visionias.in/',
                        'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36',
                    }) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            keys_string = ""
            mpd = url

            if "acecwply" in url:
                cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={raw_text2}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'

            elif "https://cpvod.testbook.com/" in url:
                url = url.replace("https://cpvod.testbook.com/", "https://media-cdn.classplusapp.com/drm/")
                url = 'https://dragoapi.vercel.app/classplus?link=' + url
                mpd, keys = helper.get_mps_and_keys(url)
                url = mpd
                keys_string = " ".join([f"--key {key}" for key in keys])

            elif "classplusapp.com/drm/" in url:
                url = 'https://dragoapi.vercel.app/classplus?link=' + url
                mpd, keys = helper.get_mps_and_keys(url)
                url = mpd
                keys_string = " ".join([f"--key {key}" for key in keys])

            elif "tencdn.classplusapp" in url:
                headers = {
                    'Host': 'api.classplusapp.com', 'x-access-token': token_cp,
                    'user-agent': 'Mobile-Android', 'app-version': '1.4.37.1',
                    'api-version': '18', 'device-id': '5d0d17ac8b3c9f51',
                    'device-details': '2848b866799971ca_2848b8667a33216c_SDK-30',
                    'accept-encoding': 'gzip'
                }
                params = (('url', url))
                response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
                url = response.json()['url']

            elif 'videos.classplusapp' in url or "webvideos.classplusapp.com" in url:
                url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': token_cp}).json()['url']

            elif 'media-cdn.classplusapp.com' in url or 'media-cdn-alisg.classplusapp.com' in url or 'media-cdn-a.classplusapp.com' in url:
                headers = {'x-access-token': token_cp, "X-CDN-Tag": "empty"}
                response = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers=headers)
                url = response.json()['url']

            elif "d1d34p8vz63oiq" in url or "sec1.pw.live" in url:
                url = f"https://anonymouspwplayer-b99f57957198.herokuapp.com/pw?url={url}?token={raw_text4}"

            if "pdf*" in url:
                url = f"https://dragoapi.vercel.app/pdf/{url}"
            if ".zip" in url:
                url = f"https://video.pablocoder.eu.org/appx-zip?url={url}"
            elif 'encrypted.m' in url:
                appxkey = url.split('*')[1]
                url = url.split('*')[0]

            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            elif "embed" in url:
                ytf = f"bestvideo[height<={raw_text2}]+bestaudio/best[height<={raw_text2}]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"

            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'
            elif "webvideos.classplusapp." in url:
                cmd = f'yt-dlp --add-header "referer:https://web.classplusapp.com/" --add-header "x-cdn-tag:empty" -f "{ytf}" "{url}" -o "{name}.mp4"'
            elif "youtube.com" in url or "youtu.be" in url:
                cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}".mp4'
            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            # ── Progress message builder ──────────────────────────
            def build_show(count, links, name, quality, CR, b_name, link0, url):
                remaining = len(links) - count
                progress  = (count / len(links)) * 100
                return (
                    f"🚀𝐏𝐫𝐨𝐠𝐫𝐞𝐬𝐬 » {progress:.2f}%\n┃\n"
                    f"┣🔗𝐈𝐧𝐝𝐞𝐱 » {count}/{len(links)}\n┃\n"
                    f"╰━🖇️𝐑𝐞𝐦𝐚𝐢𝐧 𝐋𝐢𝐧𝐤𝐬 » {remaining}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"**⚡Dᴏᴡɴʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ...⏳**\n┃\n"
                    f"┣💃𝐂𝐫𝐞𝐝𝐢𝐭 » {CR}\n┃\n"
                    f"╰━📚𝐁𝐚𝐭𝐜𝐡 𝐍𝐚𝐦𝐞 » `{b_name}`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📚𝐓𝐢𝐭𝐥𝐞 » `{name}`\n┃\n"
                    f"┣🍁𝐐𝐮𝐚𝐥𝐢𝐭𝐲 » {quality}\n┃\n"
                    f'┣━🔗𝐋𝐢𝐧𝐤 » <a href="{link0}">__**Original Link**__</a>\n┃\n'
                    f'╰━━🖇️𝐔𝐫𝐥 » <a href="{url}">__**Api Link**__</a>\n'
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🛑**Send** /stop **to stop process**\n┃\n"
                    f"╰━✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ [𝙎𝘼𝙄𝙉𝙄 𝘽𝙊𝙏𝙎🐦](https://t.me/+MdZ2996M2G43MWFl)"
                )

            try:
                cc     = f'**——— ✦ {str(count).zfill(3)} ✦ ———**\n\n**🎞️ Title :** `{name1} [{res}] .mkv`\n\n**📚 Course :** `{b_name}`\n\n**🌟 Extracted By :** {CR}'
                cc1    = f'**——— ✦ {str(count).zfill(3)} ✦ ———**\n\n**📁 Title :** `{name1} .pdf`\n\n**📚 Course :** `{b_name}`\n\n**🌟 Extracted By :** {CR}'
                cczip  = f'**——— ✦ {str(count).zfill(3)} ✦ ———**\n\n**📁 Title :** `{name1} .zip`\n\n**📚 Course :** `{b_name}`\n\n**🌟 Extracted By :** {CR}'
                ccimg  = f'**——— ✦ {str(count).zfill(3)} ✦ ———**\n\n**🖼️ Title :** `{name1} .jpg`\n\n**📚 Course :** `{b_name}`\n\n**🌟 Extracted By :** {CR}'
                ccm    = f'**——— ✦ {str(count).zfill(3)} ✦ ———**\n\n**🎵 Title :** `{name1} .mp3`\n\n**📚 Course :** `{b_name}`\n\n**🌟 Extracted By :** {CR}'
                cchtml = f'**——— ✦ {str(count).zfill(3)} ✦ ———**\n\n**🌐 Title :** `{name1} .html`\n\n**📚 Course :** `{b_name}`\n\n**🌟 Extracted By :** {CR}'

                # ── Google Drive ──────────────────────────────────
                if "drive" in url:
                    ka = await helper.download(url, name)
                    await bot.send_document(chat_id=m.chat.id, document=ka, caption=cc1)
                    count += 1
                    os.remove(ka)
                    time.sleep(1)
                    continue

                # ── PDF* (yt-dlp) ─────────────────────────────────
                elif ".pdf*" in url:
                    try:
                        cmd_pdf = f'yt-dlp -o "{name}.pdf" "{url}"'
                        download_cmd = f"{cmd_pdf} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    except FloodWait as fw:
                        await m.reply_text(str(fw))
                        await asyncio.sleep(fw.value)
                        count += 1
                        continue

                # ── Plain PDF ─────────────────────────────────────
                elif ".pdf" in url and ".pdf*" not in url:
                    try:
                        await asyncio.sleep(4)
                        url = url.replace(" ", "%20")
                        scraper = cloudscraper.create_scraper()
                        response = scraper.get(url)
                        if response.status_code == 200:
                            with open(f'{name}.pdf', 'wb') as file:
                                file.write(response.content)
                            await asyncio.sleep(4)
                            await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                            count += 1
                            os.remove(f'{name}.pdf')
                        else:
                            await m.reply_text(f"Failed to download PDF: {response.status_code} {response.reason}")
                    except FloodWait as fw:
                        await m.reply_text(str(fw))
                        await asyncio.sleep(fw.value)
                        count += 1
                        continue

                # ── .ws files ─────────────────────────────────────
                elif ".ws" in url and url.endswith(".ws"):
                    await helper.pdf_download(f"{api_url}utkash-ws?url={url}&authorization={api_token}", f"{name}.html")
                    time.sleep(1)
                    await bot.send_document(chat_id=m.chat.id, document=f"{name}.html", caption=cchtml)
                    if os.path.exists(f'{name}.html'):
                        os.remove(f'{name}.html')
                    count += 1
                    time.sleep(5)
                    continue

                # ── ZIP ───────────────────────────────────────────
                elif ".zip" in url:
                    BUTTONSZIP = InlineKeyboardMarkup([[InlineKeyboardButton(text="🎥 ZIP STREAM IN PLAYER", url=url)]])
                    await bot.send_photo(chat_id=m.chat.id, photo=photozip, caption=cczip, reply_markup=BUTTONSZIP)
                    count += 1
                    time.sleep(1)
                    continue

                # ── Images ────────────────────────────────────────
                elif any(ext in url for ext in [".jpg", ".jpeg", ".png"]):
                    ext = url.split('.')[-1]
                    download_cmd = f'yt-dlp -o "{name}.{ext}" "{url}" -R 25 --fragment-retries 25'
                    os.system(download_cmd)
                    # BUG FIX: was m.chat.d → corrected to m.chat.id
                    await bot.send_photo(chat_id=m.chat.id, photo=f'{name}.{ext}', caption=ccimg)
                    count += 1
                    if os.path.exists(f'{name}.{ext}'):
                        os.remove(f'{name}.{ext}')
                    # BUG FIX: removed dangling time.sleep(e.x) that caused NameError
                    continue

                # ── Audio ─────────────────────────────────────────
                elif any(ext in url for ext in [".mp3", ".wav", ".m4a"]):
                    ext = url.split('.')[-1]
                    download_cmd = f'yt-dlp -o "{name}.{ext}" "{url}" -R 25 --fragment-retries 25'
                    os.system(download_cmd)
                    await bot.send_document(chat_id=m.chat.id, document=f'{name}.{ext}', caption=ccm)
                    count += 1
                    if os.path.exists(f'{name}.{ext}'):
                        os.remove(f'{name}.{ext}')
                    # BUG FIX: removed dangling time.sleep(e.x) that caused NameError
                    continue

                # ── Encrypted M3U8 ────────────────────────────────
                elif 'encrypted.m' in url:
                    emoji_message = await show_random_emojis(m)
                    Show = build_show(count, links, name, quality, CR, b_name, link0, url)
                    prog = await m.reply_text(Show, disable_web_page_preview=True)
                    res_file = await helper.download_and_decrypt_video(url, cmd, name, appxkey)
                    filename = res_file
                    await emoji_message.delete()
                    await prog.delete(True)
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                    count += 1
                    await asyncio.sleep(1)
                    continue

                # ── DRM / WV ──────────────────────────────────────
                elif 'drmcdni' in url or 'drm/wv' in url:
                    emoji_message = await show_random_emojis(m)
                    Show = build_show(count, links, name, quality, CR, b_name, link0, url)
                    prog = await m.reply_text(Show, disable_web_page_preview=True)
                    res_file = await helper.decrypt_and_merge_video(mpd, keys_string, path, name, raw_text2)
                    filename = res_file
                    await emoji_message.delete()
                    await prog.delete(True)
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                    count += 1
                    await asyncio.sleep(1)
                    continue

                # ── Everything else (normal video) ────────────────
                else:
                    emoji_message = await show_random_emojis(m)
                    Show = build_show(count, links, name, quality, CR, b_name, link0, url)
                    prog = await m.reply_text(Show, disable_web_page_preview=True)
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    await emoji_message.delete()
                    await prog.delete(True)
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                    count += 1
                    time.sleep(1)

            except Exception as e:
                await m.reply_text(
                    f'⚠️**Downloading Failed**⚠️\n**Name** =>> `{str(count).zfill(3)} {name1}`\n**Url** =>> {link0}',
                    disable_web_page_preview=True
                )
                count += 1
                failed_count += 1
                continue

    except Exception as e:
        await m.reply_text(str(e))
        time.sleep(2)

    await m.reply_text(f"⋅ ─ Total failed links is {failed_count} ─ ⋅")
    await m.reply_text(
        f"⋅ ─ list index ({raw_text}-{len(links)}) out of range ─ ⋅\n\n"
        f"✨ BATCH » `{b_name}✨`\n\n⋅ ─ DOWNLOADING ✩ COMPLETED ─ ⋅"
    )

bot.run()
