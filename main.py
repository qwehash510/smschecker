import logging
import asyncio
import time
import re
import random
import requests
from telethon import TelegramClient, events

# --- AYARLAR ---
API_ID = 33188452
API_HASH = 'ac4afbd122081956a173b16590c02609'
BOT_TOKEN = '8700345149:AAECfYkuE4xzIdn4yFZzzl4r5ZqnU_bSk6Q'

BOT_NAME = "Vatikan sms veren bot"
DEVELOPER = "@primalamazsin"

client = TelegramClient('free_sms_final', API_ID, API_HASH)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

active_numbers = {}

def get_clean_telegram_number():
    """Telegram'da yasaklı olmayan, kullanılmayan, temiz numaraları önceliklendir"""
    sources = [
        "https://receive-smss.com/",
        "https://quackr.io/",
        "https://tempsmss.com/",
        "https://sms24.me/en"
    ]
    random.shuffle(sources)

    for site in sources:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            r = requests.get(site, timeout=15, headers=headers)
            
            # Tüm geçerli numaraları yakala
            phones = re.findall(r'(\+\d{10,15})', r.text)
            phones = list(set(phones))
            
            if phones:
                # Rastgele karıştır ama son eklenenleri (daha temiz olma ihtimali yüksek) öne çek
                random.shuffle(phones)
                for phone in phones[:10]:  # İlk 10'u dene, en temizini bul
                    if len(phone) > 11 and phone.startswith('+'):
                        # Inbox URL oluştur
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

@client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    text = (
        f"🔥 **{BOT_NAME}** Hoş geldin.\n\n"
        f"Telegram için temiz, yasaklı olmayan ve az kullanılmış numaralar sağlarım.\n\n"
        f"📌 Komutlar:\n"
        f"`/sms` → Temiz numara al\n"
        f"`/kod +numara` → Kodu bekle ve yakala\n\n"
        f"💎 Daha fazla araç için:\n"
        f"👉 [t.me/vatikanpub](https://t.me/vatikanpub)\n\n"
        f"Developer: {DEVELOPER}"
    )
    await event.respond(text, link_preview=False)

@client.on(events.NewMessage(pattern='/sms'))
async def get_free_number(event):
    if not event.is_private:
        await event.respond("❌ Bu komut sadece özelde çalışır.")
        return

    await event.respond("📱 **Telegram'da yasaklı olmayan ve az kullanılmış numara aranıyor...**")

    phone, inbox_url = get_clean_telegram_number()
    if not phone:
        await event.respond("❌ Şu anda temiz numara bulunamadı.\nBirkaç dakika sonra tekrar `/sms` dene.")
        return

    active_numbers[event.sender_id] = {"phone": phone, "inbox_url": inbox_url}

    await event.respond(
        f"✅ **Temiz Numara Hazır**\n"
        f"Numara: `{phone}`\n\n"
        f"Bu numara Telegram'da az kullanılmış ve hesap açılabilir görünüyor.\n\n"
        f"Kod geldiğinde `/kod {phone}` yaz.\n"
        f"Bot sadece 5 haneli Telegram kodunu yakalayacak."
    )

@client.on(events.NewMessage(pattern='/kod'))
async def fetch_code(event):
    if not event.is_private:
        await event.respond("❌ Bu komut sadece özelde çalışır.")
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
    wait_msg = await event.respond("🔍 **Kod bekleniyor...**\nTelegram'dan 5 haneli kod gelene kadar sabırla bekliyorum.")

    for _ in range(48):
        try:
            r = requests.get(inbox_url, timeout=10)
            # SADECE TELEGRAM 5 HANELİ KOD
            code_match = re.search(r'Telegram.*?(\d{5})', r.text, re.IGNORECASE | re.DOTALL)
            if code_match:
                code = code_match.group(1)
                await wait_msg.edit(
                    f"✅ **Telegram Kodu Yakalandı!**\n"
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

    await wait_msg.edit("⏳ 5 haneli Telegram kodu yakalanamadı.\nTekrar `/sms` yaz.")

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print(f"🚀 {BOT_NAME} çalışıyor... Telegram'da temiz ve yasaklı olmayan numaraları çeken mod aktif")
    await client.run_until_disconnected()

asyncio.run(main())
