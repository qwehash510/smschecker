import logging
import asyncio
from telethon import TelegramClient, events

# --- AYARLAR ---
API_ID = 33188452
API_HASH = 'ac4afbd122081956a173b16590c02609'
BOT_TOKEN = '8692735722:AAFJ7u253A9tzqVDNetCzfsEgfzVaOoWwmA'

BOT_NAME = "VATİKAN YIKICI CP"
OWNER = 8620961678

client = TelegramClient('cp_destroyer', API_ID, API_HASH)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Aktif spam durumu
spam_tasks = {}  # {user_id: {"target": chat, "media": [], "running": True, "delay": 0.6}}

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        f"🔥 **{BOT_NAME}** aktif - En yıkıcı mod.\n\n"
        f"Kullanım:\n"
        f"`/cp @targetgrup 999`\n"
        f"Sonra istediğin kadar medya at.\n"
        f"`/dur` yazınca spam kesilir.\n\n"
        f"Developer: @primalamazsin"
    )

@client.on(events.NewMessage(pattern='/cp'))
async def start_cp(event):
    if event.sender_id != OWNER or not event.is_private:
        return

    args = event.message.text.split()
    if len(args) < 3:
        await event.respond("❗️ Kullanım: `/cp @targetgrup 999`")
        return

    target = args[1]
    try:
        count = int(args[2])
    except:
        count = 999  # Sonsuz loop için büyük sayı

    try:
        chat = await client.get_entity(target)
    except Exception as e:
        await event.respond(f"❌ Grup bulunamadı: {e}")
        return

    spam_tasks[event.sender_id] = {
        "target": chat,
        "media": [],
        "count": count,
        "running": True,
        "delay": 0.6   # Çok hızlı yıkım
    }

    await event.respond(
        f"🚀 **Yıkım Modu Aktif**\n"
        f"Hedef: **{chat.title}**\n"
        f"Loop: {'Sonsuz' if count > 500 else count}\n\n"
        f"Şimdi istediğin kadar CP (foto, video, gif) at.\n"
        f"Bittiğinde `tamam` yaz, spam otomatik başlar."
    )

@client.on(events.NewMessage())
async def handle_media(event):
    if event.sender_id != OWNER or not event.is_private:
        return
    if event.sender_id not in spam_tasks:
        return

    data = spam_tasks[event.sender_id]

    if event.text and event.text.lower() == "tamam":
        if not data["media"]:
            await event.respond("❌ Henüz medya yüklemedin.")
            return
        await start_spamming(event.sender_id)
        return

    if event.text and event.text.lower() == "/dur":
        await stop_spamming(event.sender_id)
        return

    # Medya geldi
    if event.photo or event.video or event.document or event.gif:
        data["media"].append(event.media)
        current = len(data["media"])
        await event.respond(f"✅ Medya alındı ({current} yüklendi)")

        # Eğer istenen sayı kadar yüklendiyse otomatik başlasın
        if current >= data["count"] and data["count"] < 500:
            await start_spamming(event.sender_id)

async def start_spamming(user_id):
    data = spam_tasks[user_id]
    if not data.get("running"):
        return

    await client.send_message(user_id, f"💥 **Yıkım başlıyor...**\nHedef: **{data['target'].title}**\n3 saniyede bir değil, **0.6 saniyede bir** atılıyor.")

    task = asyncio.create_task(spam_loop(user_id))
    spam_tasks[user_id]["task"] = task

async def spam_loop(user_id):
    data = spam_tasks[user_id]
    target = data["target"]
    media_list = data["media"][:data["count"]]

    while data.get("running"):
        for media in media_list:
            if not data.get("running"):
                break
            try:
                await client.send_file(target, media, silent=True)
                await asyncio.sleep(0.6)  # Çok hızlı yıkım
            except Exception as e:
                logging.error(f"Yıkım hatası: {e}")
                await asyncio.sleep(2)

        # Sonsuz loop için tekrar başa dön
        if data["count"] > 500:
            await asyncio.sleep(1)  # Kısa mola
        else:
            break  # Normal modda bir kere atıp bitsin

    if data.get("running"):
        await client.send_message(user_id, "✅ **Yıkım tamamlandı (loop bitti).**")
    if user_id in spam_tasks:
        del spam_tasks[user_id]

async def stop_spamming(user_id):
    if user_id in spam_tasks:
        spam_tasks[user_id]["running"] = False
        if "task" in spam_tasks[user_id]:
            spam_tasks[user_id]["task"].cancel()
        await client.send_message(user_id, "⛔ **Yıkım durduruldu.**")
        del spam_tasks[user_id]

async def main():
    await client.start(bot_token=BOT_TOKEN)
    print(f"🚀 {BOT_NAME} çalışıyor... En yıkıcı CP spam modu aktif (0.6s aralık + loop)")
    await client.run_until_disconnected()

asyncio.run(main())
