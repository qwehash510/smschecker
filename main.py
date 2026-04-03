import logging
import asyncio
import time
import re
import random
import requests
from telethon import TelegramClient, events
from telethon.errors import PhoneCodeInvalidError, FloodWaitError

# --- AYARLAR ---
API_ID = 33188452
API_HASH = 'ac4afbd122081956a173b16590c02609'
BOT_TOKEN = '8700345149:AAECfYkuE4xzIdn4yFZzzl4r5ZqnU_bSk6Q'

BOT_NAME = "Vatikan ücretsiz sms botuna"
DEVELOPER = "@primalamazsin"

client = TelegramClient('free_sms_pro', API_ID, API_HASH)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

active_numbers = {}  # {user_id: {"phone": , "inbox_url": }}

def get_fresh_number():
    sources = [
        "https://receive-smss.com/",
        "https://quackr.io/",
        "https://tempsmss.com/",
        "https://sms24.me/en",
        "https://freephonenum.com/"
    ]
    random.shuffle(sources)

    for site in sources:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            r = requests.get(site, timeout=12, headers=headers)
            phones = re.findall(r'(\+\d{10,15})', r.text)
            phones = list(set(phones))
            if phones:
                phone = random.choice(phones)
                if "receive-smss" in site:
                    inbox_url = f"https://receive-smss.com/sms/{phone.replace('+', '')}"
                elif "quackr" in site:
                    inbox_url = f"https://quackr.io/{phone.replace('+', '')}"
                else:
                    inbox_url = site
                return phone, inbox_url
        except:
            continue
    return None, None

@client.on(events.NewMessage(pattern='/start', chats=None))
async def start_handler(event):
    welcome_text = (
        f"🔥 **{BOT_NAME}** Hoş geldin.\n\n"
        f"Bu bot **tamamen ücretsiz** ve kuralsız şekilde Telegram için geçici numara sağlar.\n\n"
        f"📌 **Nasıl Kullanılır?**\n"
        f"• `/sms` → Taze numara al\n"
        f"• `/kod +numara` → Gelen kodu otomatik yakala\n\n"
        f"💎 Daha fazla araç ve ekip için:\n"
        f"👉 [t.me/vatikanpub](https://t.me/vatikanpub) grubumuza katıl.\n\n"
        f"⚡ Bot her seferinde farklı ve az kullanılan numaralar çeker.\n\n"
        f"Developer: {DEVELOPER}"
    )
    await event.respond(welcome_text, link_preview=False)

@client.on(events.NewMessage(pattern='/sms', chats=None))
async def get_free_number(event):
    if not event.is_private:
        await event.respond("❌ Bu komut sadece özel mesajda çalışır.")
        return

    await event.respond("📱 **Taze ve az kullanılan numara aranıyor...**")

    phone, inbox_url = get_fresh_number()
    if not phone:
        await event.respond("❌ Şu anda taze numara bulunamadı.\nBirkaç dakika sonra tekrar `/sms` dene.")
        return

    # Telegram kontrolü
    status = "✅ Muhtemelen yeni"
    try:
        test = TelegramClient(f'test_{int(time.time())}', API_ID, API_HASH)
        await test.connect()
        await test.send_code_request(phone)
    except Exception as e:
        if "already" in str(e).lower() or "banned" in str(e).lower():
            status = "⚠️ Bu numarada hesap olabilir"
    finally:
        try:
            await test.disconnect()
        except:
            pass

    active_numbers[event.sender_id] = {"phone": phone, "inbox_url": inbox_url}

    await event.respond(
        f"✅ **Taze Numara Hazır**\n"
        f"Numara: `{phone}`\n"
        f"Durum: {status}\n\n"
        f"Kod geldiğinde `/kod {phone}` yaz.\n"
        f"Bot inbox’u otomatik tarayıp kodu getirecek."
    )

@client.on(events.NewMessage(pattern='/kod', chats=None))
async def fetch_code(event):
    if not event.is_private:
        await event.respond("❌ Bu komut sadece özel mesajda çalışır.")
        return

    try:
        phone = event.message.text.split(maxsplit=1)[1].strip()
    except:
        await event.respond("❗️ Kullanım: `/kod +905551234567`")
        return

    if event.sender_id not in active_numbers or active_numbers[event.sender_id]["phone"] != phone:
        await event.respond("❌ Bu numara için aktif işlem yok.")
        return

    inbox_url = active_numbers[event.sender_id]["inbox_url"]
    await event.respond("🔍 **Kod taranıyor...** (her 5 saniyede kontrol)")

    for _ in range(36):
        try:
            r = requests.get(inbox_url, timeout=10)
            code_match = re.search(r'(\d{5,7})', r.text)
            if code_match:
                code = code_match.group(1)
                await event.respond(
                    f"✅ **Kod Yakalandı!**\n"
                    f"Numara: `{phone}`\n"
                    f"**Kod:** `{code}`\n\n"
                    f"Telegram'a gir ve yeni hesap aç."
                )
                if event.sender_id in active_numbers:
                    del active_numbers[event.sender_id]
                return
        except:
            pass
        await asyncio.sleep(5)

    await event.respond("⏳ Kod yakalanamadı. Numara süresi dolmuş olabilir.\nTekrar `/sms` yaz.")

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print(f"🚀 {BOT_NAME} çalışıyor... Herkese açık ücretsiz SMS modu aktif")
    await client.run_until_disconnected()

asyncio.run(main())
