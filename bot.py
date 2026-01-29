import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from config import BOT_TOKEN
from database import (
    save_city, save_street,
    set_resources,
    get_user, get_resources, get_channels,
    add_channel, remove_channel,
    is_sent, mark_sent
)
from scheduler import check_sources
from telethon_client import client, start_client
from text_parser import match_message, is_planned

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# ================== КНОПОЧНОЕ МЕНЮ ==================

menu = ReplyKeyboardMarkup(resize_keyboard=True)
menu.add(
    KeyboardButton("🏙 Город"),
    KeyboardButton("🛣 Улица"),
)
menu.add(
    KeyboardButton("💡 Ресурсы"),
    KeyboardButton("📡 Каналы"),
)
menu.add(
    KeyboardButton("👤 Профиль"),
    KeyboardButton("🔄 Проверить"),
)

# ---------- inline меню каналов ----------

channels_menu = InlineKeyboardMarkup()
channels_menu.add(
    InlineKeyboardButton("➕ Добавить канал", callback_data="ch:add"),
    InlineKeyboardButton("➖ Удалить канал", callback_data="ch:remove"),
)

# ---------- ресурсы ----------

resources_kb = InlineKeyboardMarkup(row_width=2)
resources_kb.add(
    InlineKeyboardButton("💧 Вода", callback_data="res:вода"),
    InlineKeyboardButton("🔥 Горячая вода", callback_data="res:горячая вода"),
    InlineKeyboardButton("⚡ Свет", callback_data="res:свет"),
    InlineKeyboardButton("🔥 Газ", callback_data="res:газ"),
    InlineKeyboardButton("🌡 Отопление", callback_data="res:отопление"),
    InlineKeyboardButton("🌐 Интернет", callback_data="res:интернет"),
)
resources_kb.add(
    InlineKeyboardButton("✅ Сохранить", callback_data="res:save")
)

user_resources_tmp = {}

# ================== FSM ==================

class Form(StatesGroup):
    city = State()
    street = State()
    add_channel = State()

# ================== START ==================

@dp.message_handler(commands="start")
async def start(msg: types.Message):
    await msg.answer(
        "Добро пожаловать в Бот-коммунальщик👷\n\nЯ буду оповещать вас о плановых и аварийных отключениях коммунальных и инфраструктурных услуг!\n"
        "Для работы со мной используйте кнопки ниже ⬇️",
        reply_markup=menu
    )

# ================== ГОРОД ==================

@dp.message_handler(lambda m: m.text == "🏙 Город")
async def city(msg: types.Message):
    await msg.answer("Введите город или `-` чтобы очистить")
    await Form.city.set()

@dp.message_handler(state=Form.city)
async def city_save(msg: types.Message, state):
    save_city(msg.from_user.id, None if msg.text.strip() == "-" else msg.text.strip())
    await msg.answer("Город сохранён✅", reply_markup=menu)
    await state.finish()

# ================== УЛИЦА ==================

@dp.message_handler(lambda m: m.text == "🛣 Улица")
async def street(msg: types.Message):
    await msg.answer("Введите улицу или `-` чтобы очистить")
    await Form.street.set()

@dp.message_handler(state=Form.street)
async def street_save(msg: types.Message, state):
    save_street(msg.from_user.id, None if msg.text.strip() == "-" else msg.text.strip())
    await msg.answer("Улица сохранена✅", reply_markup=menu)
    await state.finish()

# ================== РЕСУРСЫ ==================

@dp.message_handler(lambda m: m.text == "💡 Ресурсы")
async def resources(msg: types.Message):
    user_resources_tmp[msg.from_user.id] = set()
    await msg.answer("Выберите ресурсы c помощью нажатия:", reply_markup=resources_kb)

@dp.callback_query_handler(lambda c: c.data.startswith("res:"))
async def res_cb(call: types.CallbackQuery):
    uid = call.from_user.id
    action = call.data.split(":", 1)[1]

    if action == "save":
        set_resources(uid, list(user_resources_tmp.get(uid, [])))
        await call.message.edit_text("Ресурсы сохранены✅")
        return

    user_resources_tmp.setdefault(uid, set()).add(action)
    await call.answer(f"Добавлено: {action}")

# ================== КАНАЛЫ ==================

@dp.message_handler(lambda m: m.text == "📡 Каналы")
async def channels(msg: types.Message):
    await msg.answer("Управление каналами:", reply_markup=channels_menu)

@dp.callback_query_handler(lambda c: c.data == "ch:add")
async def ch_add_start(call: types.CallbackQuery):
    await call.message.edit_text("➕ Введите канал (@ или https://t.me/...)")
    await Form.add_channel.set()

@dp.message_handler(state=Form.add_channel)
async def ch_add_finish(msg: types.Message, state):
    add_channel(msg.from_user.id, msg.text.strip())
    await msg.answer("✅ Канал добавлен", reply_markup=menu)
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == "ch:remove")
async def ch_remove_menu(call: types.CallbackQuery):
    channels = get_channels(call.from_user.id)
    if not channels:
        await call.message.edit_text("❌ Каналов нет")
        return

    kb = InlineKeyboardMarkup()
    for ch in channels:
        kb.add(InlineKeyboardButton(f"❌ {ch}", callback_data=f"ch:del:{ch}"))

    await call.message.edit_text("➖ Выберите канал:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith("ch:del:"))
async def ch_remove(call: types.CallbackQuery):
    ch = call.data.split(":", 2)[2]
    remove_channel(call.from_user.id, ch)
    await call.message.edit_text(f"🗑 Удалён:\n{ch}")

# ================== ПРОФИЛЬ ==================

@dp.message_handler(lambda m: m.text == "👤 Профиль")
async def profile(msg: types.Message):
    city, street = get_user(msg.from_user.id) or (None, None)
    await msg.answer(
        f"👤 Мой профиль\n\n"
        f"🏙 Город: {city or '—'}\n"
        f"🛣 Улица: {street or '—'}\n"
        f"💡 Ресурсы: {', '.join(get_resources(msg.from_user.id)) or '—'}\n"
        f"📡 Каналы: {', '.join(get_channels(msg.from_user.id)) or '—'}",
        reply_markup=menu
    )

# ================== ПРОВЕРИТЬ СЕЙЧАС ==================

async def check_sources_once(uid):
    await start_client()

    city, street = get_user(uid)
    resources = get_resources(uid)
    channels = get_channels(uid)

    if not resources or not channels:
        return

    for ch in channels:
        async for msg in client.iter_messages(ch, limit=20):
            if not msg.text:
                continue

            if match_message(msg.text, city, street, resources):
                await bot.send_message(uid, msg.text)

@dp.message_handler(lambda m: m.text == "🔄 Проверить")
async def check_now(msg: types.Message):
    await msg.answer("🔄 Проверяю…")
    await check_sources_once(msg.from_user.id)
    await msg.answer("✅ Готово", reply_markup=menu)

# ================== STARTUP ==================

async def on_startup(dp):
    asyncio.create_task(check_sources(bot))

if __name__ == "__main__":
    executor.start_polling(dp, on_startup=on_startup)
