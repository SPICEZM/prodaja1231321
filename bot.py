import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message

# Настройки токена
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000)) # Порт, который требует Render

if not TOKEN:
    print("ВНИМАНИЕ: TELEGRAM_BOT_TOKEN не задан в переменных окружения!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Базы данных в памяти
users_db = {}
referrals_db = {} 

ROLES = ["пацык", "реферал", "принцеска", "админ", "слуга", "владелец", "босс"]

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name
    
    args = message.text.split()
    if len(args) > 1:
        ref_arg = args[1]
        if ref_arg.isdigit():
            referrer_id = int(ref_arg)
            if referrer_id != user_id and user_id not in referrals_db:
                referrals_db[user_id] = referrer_id
                
                if referrer_id in users_db:
                    users_db[referrer_id]["refs_count"] += 1
                    count = users_db[referrer_id]["refs_count"]
                    
                    notification = f"🎉 К нам поступил новый гость! Его пригласил @{username} (Прогресс: {count}/10)"
                    await message.answer(notification)
                    
                    if count == 10:
                        await message.answer(f"🔥 @{username} выполнил норму 10/10 и заработал бонус 50 рублей! Свяжитесь с админом для выплаты.")

    if user_id not in users_db:
        users_db[user_id] = {
            "username": username,
            "refs_count": 0,
            "role": "пацык"
        }

    await message.answer(
        f"Здарова, {username}! Добро пожаловать в наше сообщество.\n\n"
        f"Твой текущий тег: <b>{users_db[user_id]['role']}</b>\n\n"
        f"Используй команду /ref, чтобы получить свою реферальную ссылку и приглашать друзей (награда: 50 руб за 10 человек)!"
    )

@dp.message(Command("ref"))
async def cmd_ref(message: Message):
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    count = users_db.get(user_id, {}).get("refs_count", 0)
    
    await message.answer(
        f"🔗 <b>Твоя персональная реферальная ссылка:</b>\n{ref_link}\n\n"
        f"👥 Приглашено гостей: <b>{count}/10</b>\n"
        f"🎁 Приз за 10 приглашенных: <b>50 рублей!</b>"
    )

@dp.message(Command("setrole"))
async def cmd_setrole(message: Message):
    user_id = message.from_user.id
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(f"Укажи роль из списка: {', '.join(ROLES)}")
        return
        
    new_role = args[1].lower()
    if new_role in ROLES:
        if user_id in users_db:
            users_db[user_id]["role"] = new_role
        else:
            users_db[user_id] = {"username": message.from_user.username, "refs_count": 0, "role": new_role}
        await message.answer(f"✅ Твой тег успешно изменен на: <b>{new_role}</b>")
    else:
        await message.answer(f"❌ Нет такого тега! Выбери из списка: {', '.join(ROLES)}")

# Заглушка веб-сервера для Render, чтобы он видел открытый порт
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    print(f"Веб-сервер запущен на порту {PORT}")

async def main():
    # Запускаем и веб-сервер для порта, и поллинг бота одновременно
    await start_web_server()
    print("Бот запущен и слушает сообщения...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
