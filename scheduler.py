import asyncio
from telethon_client import client, start_client
from database import (
    all_users, get_user, get_resources,
    get_channels, is_sent, mark_sent
)
from text_parser import match_message, is_planned
from config import CHECK_INTERVAL_SECONDS


# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------

def normalize_channel(ch: str) -> str:
    ch = ch.strip()

    if ch.startswith("https://t.me/"):
        return ch.replace("https://t.me/", "").strip("/")

    if ch.startswith("t.me/"):
        return ch.replace("t.me/", "").strip("/")

    return ch.lstrip("@")


def extract_text(msg):
    # обычный текст или подпись к фото/видео
    return msg.text or msg.message


# ---------- ОСНОВНОЙ ЦИКЛ ----------

async def check_sources(bot):
    await start_client()
    print("✅ Telethon готов")

    while True:
        print("🔄 Проверка каналов...")
        for user_id in all_users():
            city, street = get_user(user_id)
            resources = get_resources(user_id)
            channels = get_channels(user_id)

            print(f"\n👤 USER {user_id}")
            print("   CITY:", city)
            print("   STREET:", street)
            print("   RESOURCES:", resources)
            print("   CHANNELS:", channels)

            if not city or not resources or not channels:
                print("   ⛔ пропуск: нет данных")
                continue

            for ch in channels:
                # защита от мусора
                if not ch or ch.strip() in {",", ";"}:
                    print("   ⛔ мусорный канал:", repr(ch))
                    continue

                channel = normalize_channel(ch)

                if not channel:
                    print("   ⛔ пустой канал после normalize")
                    continue

                print(f"   📡 Чтение канала: {channel}")

                try:
                    async for msg in client.iter_messages(channel, limit=50):
                        text = extract_text(msg)

                        if not text:
                            print("      ⏭ пустое сообщение")
                            continue

                        print("      📝 ТЕКСТ:", text[:120].replace("\n", " "))

                        key = f"{channel}:{msg.id}"
                        if is_sent(user_id, key):
                            print("      ⏭ уже отправлено")
                            continue

                        matched = match_message(text, city, street, resources)
                        print("      🔍 MATCH:", matched)

                        if not matched:
                            continue

                        label = "🛠 Плановое" if is_planned(text) else "🚨 Аварийное"

                        await bot.send_message(
                            user_id,
                            f"{label} отключение\n\n"
                            f"{text}\n\n"
                            f"https://t.me/{channel}/{msg.id}"
                        )

                        mark_sent(user_id, key)
                        print("      ✅ УВЕДОМЛЕНИЕ ОТПРАВЛЕНО")

                except Exception as e:
                    print(f"⚠ Ошибка канала {channel}: {e}")

        print(f"⏱ Ожидание {CHECK_INTERVAL_SECONDS} секунд...\n")
        await asyncio.sleep(CHECK_INTERVAL_SECONDS)
