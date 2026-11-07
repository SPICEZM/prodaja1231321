import asyncio
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest

BOT_TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Список запрещенных слов
BAD_WORDS = ["спам", "скам", "заработок", "крипта", "casino", "казино", "блять", "хуй"]

# 1. Приветствие новых участников
@dp.chat_member()
async def welcome_new_member(event: types.ChatMemberUpdated):
    if event.new_chat_member.status == "member" and event.old_chat_member.status == "left":
        user_name = event.new_chat_member.user.first_name
        await event.bot.send_message(
            event.chat.id,
            f"Здарова, {user_name}. Добро пожаловать в хату. Не баклань, правила чата соблюдай."
        )

# 2. Модерация текста (удаление мата/спама)
@dp.message(F.text)
async def moderate_chat(message: types.Message):
    try:
        member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in ["creator", "administrator"]:
            return
    except Exception:
        pass

    text_lower = message.text.lower()
    
    for word in BAD_WORDS:
        if word in text_lower:
            try:
                await message.delete()
                warning = await message.answer(
                    f"Эй, @{message.from_user.username or message.from_user.first_name}, завязывай базарить. Мусор почищен."
                )
                await asyncio.sleep(5)
                await warning.delete()
            except TelegramBadRequest:
                pass
            return

# 3. Бан по команде /ban (ответом на сообщение)
@dp.message(Command("ban"))
async def ban_user(message: types.Message):
    if not message.reply_to_message:
        await message.answer("Эту команду нужно использовать ответом на сообщение нарушителя!")
        return
    
    try:
        admin_check = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if admin_check.status not in ["creator", "administrator"]:
            await message.answer("Ты не админ, чтобы налево и направо бананами раскидываться.")
            return
    except Exception:
        pass

    target_user = message.reply_to_message.from_user
    try:
        await message.chat.ban(user_id=target_user.id)
        await message.answer(f"Пользователь {target_user.first_name} отлетает в бан за нарушение режима.")
    except Exception as e:
        await message.answer(f"Не получилось забанить: {e}")

# Веб-сервер для удержания порта на Render
async def handle_ping(request):
    return web.Response(text="Moderator bot is alive!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    await web_server()
    # Запускаем поллинг со сбросом старых сессий
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
