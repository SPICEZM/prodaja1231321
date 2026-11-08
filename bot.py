import os
import json
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
CHANNEL_LINK = "https://t.me/spaysettik"

# Сюда можно вписать ID твоего чата (например, -100xxxxxxxxxx), куда будут лететь уведомления. 
# Если оставить 0, то уведомление прилетит только пригласившему в ЛС.
CHAT_ID_FOR_ALERTS = 0 

if not TOKEN:
    print("ВНИМАНИЕ: TELEGRAM_BOT_TOKEN не задан!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_FILE = "users_data.json"

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_db():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(users_db, f, ensure_ascii=False, indent=4)

users_db = load_db()
ROLES = ["пацык", "реферал", "принцеска", "админ", "слуга", "владелец", "босс"]

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id_str = str(message.from_user.id)
    username = message.from_user.username or message.from_user.first_name
    
    args = message.text.split()
    if len(args) > 1:
        ref_arg = args[1]
        if ref_arg.isdigit():
            referrer_id_str = ref_arg
            
            if referrer_id_str != user_id_str and referrer_id_str in users_db:
                already_referred = False
                for uid, data in users_db.items():
                    if "invited" in data and user_id_str in data["invited"]:
                        already_referred = True
                        break
                
                if not already_referred:
                    if "invited" not in users_db[referrer_id_str]:
                        users_db[referrer_id_str]["invited"] = []
                    
                    users_db[referrer_id_str]["invited"].append(user_id_str)
                    users_db[referrer_id_str]["refs_count"] += 1
                    count = users_db[referrer_id_str]["refs_count"]
                    save_db()
                    
                    # Узнаем юзернейм того, кто пригласил
                    referrer_name = users_db[referrer_id_str].get("username", "друган")
                    
                    # Текст уведомления: кто зашел и кто пригласил
                    alert_text = (
                        f"🚨 <b>Новый гость в движухе!</b>\n"
                        f"👤 К нам зашел: <b>@{username}</b>\n"
                        f"🤝 Его пригласил: <b>@{referrer_name}</b>\n"
                        f"🔒 <i>Цемент безопасности:</i> зачтется окончательно через 3 дня. (Прогресс пригласившего: {count}/10)"
                    )
                    
                    # Шлем уведомление пригласившему в ЛС
                    try:
                        await bot.send_message(int(referrer_id_str), alert_text, parse_mode="HTML")
                    except:
                        pass
                    
                    # Если указан ID общего чата, дублируем туда
                    if CHAT_ID_FOR_ALERTS != 0:
                        try:
                            await bot.send_message(CHAT_ID_FOR_ALERTS, alert_text, parse_mode="HTML")
                        except:
                            pass
                    
                    if count >= 10:
                        try:
                            await bot.send_message(
                                int(referrer_id_str), 
                                f"🔥 Ты выполнил норму 10/10 и заработал бонус 50 рублей! Свяжись с админом.",
                                parse_mode="HTML"
                            )
                        except:
                            pass

    if user_id_str not in users_db:
        users_db[user_id_str] = {
            "username": username,
            "refs_count": 0,
            "role": "пацык",
            "invited": []
        }
        save_db()

    role = users_db[user_id_str]['role']
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Залететь в наш ТГК", url=CHANNEL_LINK)]
    ])

    text = (
        f"Здарова, {username}! Добро пожаловать в систему.\n\n"
        f"Твой текущий тег: <b>{role}</b>\n\n"
        f"Жми кнопку ниже, чтобы перейти в закрытый канал 👇"
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@dp.message(Command("ref"))
async def cmd_ref(message: Message):
    user_id_str = str(message.from_user.id)
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    
    ref_link = f"https://t.me/{bot_username}?start={user_id_str}"
    
    if user_id_str not in users_db:
        users_db[user_id_str] = {"username": message.from_user.username or "тип", "refs_count": 0, "role": "пацык", "invited": []}
        save_db()
        
    count = users_db[user_id_str]["refs_count"]
    
    text = (
        f"🔗 <b>Твоя персональная реферальная ссылка:</b>\n{ref_link}\n\n"
        f"📌 Кидай эту ссылку друганам. Чтобы засчиталось, они должны запустить бота по ней!\n\n"
        f"👥 Приглашено гостей: <b>{count}/10</b>\n"
        f"🛡 <i>Цемент безопасности:</i> Срок удержания — 3 дня.\n"
        f"🎁 Приз за 10 человек: <b>50 рублей!</b>"
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

@dp.message(Command("setrole"))
async def cmd_setrole(message: Message):
    user_id_str = str(message.from_user.id)
    args = message.text.split(maxsplit=1)
    
    if len(args) < 2:
        await message.answer(f"Укажи роль из списка: {', '.join(ROLES)}")
        return
        
    new_role = args[1].lower()
    if new_role in ROLES:
        if user_id_str not in users_db:
            users_db[user_id_str] = {"username": message.from_user.username, "refs_count": 0, "role": new_role, "invited": []}
        else:
            users_db[user_id_str]["role"] = new_role
        save_db()
        await message.answer(f"✅ Твой тег успешно изменен на: <b>{new_role}</b>", parse_mode="HTML")
    else:
        await message.answer(f"❌ Нет такого тега! Выбери из списка: {', '.join(ROLES)}")

async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

async def main():
    await start_web_server()
    print("Бот запущен с именными уведомлениями о рефералах...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
