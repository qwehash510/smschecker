import logging
import asyncio
from telethon import TelegramClient, events
from telethon.errors import FloodWaitError

# --- AYARLAR ---
API_ID = 33188452
API_HASH = 'ac4afbd122081956a173b16590c02609'
BOT_TOKEN = '8689466345:AAFWhAmjXQkS04XKnH5_CMQx87H0PN8DiDs'

BOT_NAME = "VATİKAN YIKICI CP"

client = TelegramClient('cp_destroyer_safe', API_ID, API_HASH)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Yetkili kullanıcılar (sen + eklediklerin)
authorized_users = {8620961678}  # Senin ID'n otomatik ekli

spam_tasks = {}  # {user_id: {"target": chat, "media": [], "running": True}}

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    if event.sender_id not in authorized_users:
        return
    await event.respond(
        f"🔥 **{BOT_NAME}** aktif.\n\n"
        f"Kullanım:\n"
        f"`/cp @targetgrup 999`\n"
        f"Sonra medya at → `tamam` yaz\n"
        f"`/dur` yazınca durur.\n\n"
        f"Yetki komutları:\n"
        f"`/adduser @kisi` veya `/adduser 123456789`\n"
        f"`/deluser @kisi`\n"
        f"`/listuser`"
    )

# ====================== YETKİ YÖNETİMİ ======================
@client.on(events.NewMessage(pattern='/adduser'))
async def add_user(event):
    if event.sender_id != 8620961678:  # Sadece sen ekleyebilirsin
        return
    if not event.is_private:
        return

    try:
        arg = event.message.text.split(maxsplit=1)[1].strip()
        if arg.startswith('@'):
            user = await client.get_entity(arg)
            user_id = user.id
        else:
            user_id = int(arg)
        
        authorized_users.add(user_id)
        await event.respond(f"✅ Kullanıcı eklendi: `{user_id}`")
    except Exception as e:
        await event.respond(f"❌ Hata: {e}")

@client.on(events.NewMessage(pattern='/deluser'))
async def del_user(event):
    if event.sender_id != 8620961678:
        return
    if not event.is_private:
        return

    try:
        arg = event.message.text.split(maxsplit=1)[1].strip()
        if arg.startswith('@'):
            user = await client.get_entity(arg)
            user_id = user.id
        else:
            user_id = int(arg)
        
        if user_id in authorized_users:
            authorized_users.remove(user_id)
            await event.respond(f"✅ Kullanıcı silindi: `{user_id}`")
        else:
            await event.respond("❌ Bu kullanıcı zaten yetkili değil.")
    except Exception as e:
        await event.respond(f"❌ Hata: {e}")

@client.on(events.NewMessage(pattern='/listuser'))
async def list_users(event):
    if event.sender_id != 8620961678:
        return
    if not event.is_private:
        return

    users = "\n".join([f"`{uid}`" for uid in authorized_users])
    await event.respond(f"**Yetkili Kullanıcılar:**\n{users}")

# ====================== CP SPAM ======================
@client.on(events.NewMessage(pattern='/cp'))
async def start_cp(event):
    if event.sender_id not in authorized_users or not event.is_private:
        return

    args = event.message.text.split()
    if len(args) < 3:
        await event.respond("❗️ Kullanım: `/cp @targetgrup 999`")
        return

    target = args[1]
    try:
        count = int(args[2])
    except:
        count = 999

    try:
        chat = await client.get_entity(target)
    except Exception as e:
        await event.respond(f"❌ Grup bulunamadı: {e}")
        return

    spam_tasks[event.sender_id] = {
        "target": chat,
        "media": [],
        "count": count,
        "running": True
    }

    await event.respond(
        f"🚀 **Yıkım Modu Aktif**\n"
        f"Hedef: **{chat.title}**\n"
        f"Loop: {'Sonsuz' if count > 500 else count}\n\n"
        f"Şimdi istediğin kadar CP at.\n"
        f"Bittiğinde `tamam` yaz."
    )

@client.on(events.NewMessage())
async def handle_media(event):
    if event.sender_id not in authorized_users or not event.is_private:
        return
    if event.sender_id not in spam_tasks:
        return

    data = spam_tasks[event.sender_id]

    if event.text:
        text = event.text.lower()
        if text == "tamam":
            if not data["media"]:
                await event.respond("❌ Henüz medya yüklemedin.")
                return
            await start_spamming(event.sender_id)
            return
        elif text == "/dur":
            await stop_spamming(event.sender_id)
            return

    if event.photo or event.video or event.document or event.gif:
        data["media"].append(event.media)
        current = len(data["media"])
        await event.respond(f"✅ Medya alındı ({current} yüklendi)")

        if current >= data["count"] and data["count"] < 500:
            await start_spamming(event.sender_id)

async def start_spamming(user_id):
    data = spam_tasks[user_id]
    if not data.get("running"):
        return

    await client.send_message(user_id, f"💥 **Yıkım başlıyor...**\n1.8 saniye aralıkla Flood koruması aktif.")

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
                await asyncio.sleep(1.8)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 3)
            except Exception as e:
                logging.error(f"CP hatası: {e}")
                await asyncio.sleep(5)

        if data["count"] > 500:
            await asyncio.sleep(2)
        else:
            break

    if data.get("running"):
        await client.send_message(user_id, "✅ **Yıkım tamamlandı.**")
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
    print(f"🚀 {BOT_NAME} çalışıyor... Sadece sen + eklediğin kişiler kullanabilir (1.8s güvenli mod)")
    await client.run_until_disconnected()

asyncio.run(main())
