from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
from config import API_ID, API_HASH, SESSION_NAME

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)


async def start_client():
    await client.connect()

    if not await client.is_user_authorized():
        phone = input("Телефон (+7...): ")
        await client.send_code_request(phone)
        code = input("Код из Telegram: ")

        try:
            await client.sign_in(phone, code)
        except SessionPasswordNeededError:
            password = input("Пароль 2FA: ")
            await client.sign_in(password=password)