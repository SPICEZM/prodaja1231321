import os
import json
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
PORT = int(os.environ.get("PORT", 10000))
CHANNEL_USERNAME = "@spaysettik"
CHANNEL_LINK = "https://t.me/spaysettik"

# Твой личный Telegram ID для получения отчетов о рефералах в ЛС
ADMIN_CHAT_ID = 8381183474

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

async def check_subscription(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            return True
    except Exception as e:
        print(f"Ошибка проверки подписки: {e}")
    return False

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_id_str = str(message.from_user.id)
    username = message.from_user.username or message.from_user.first_name
    
    args = message.text.split()
    pending_referrer = None
    
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
                    pending_referrer = referrer_id_str

    if user_id_str not in users_db:
        users_db[user_id_str] = {
            "username": username,
            "refs_count": 0,
            "role": "пацык",
            "invited": [],
            "pending_ref": pending_referrer
        }
        save_db()
    else:
        if pending_referrer and not users_db[user_id_str].get("invited_by"):
            users_db[user_id_str]["pending_ref"] = pending_referrer
            save_db()

    is_subscribed = await check_subscription(message.from_user.id)
    
    if is_subscribed and users_db[user_id_str].get("pending_ref"):
        ref_id = users_db[user_id_str]["pending_ref"]
        if ref_id in users_db and user_id_str not in users_db[ref_id]["invited"]:
            users_db[ref_id]["invited"].append(user_id_str)
            users_db[ref_id]["refs_count"] += 1
            count = users_db[ref_id]["refs_count"]
            users_db[user_id_str]["pending_ref"] = None
            users_db[user_id_str]["invited_by"] = ref_id
            save_db()
            
            referrer_name = users_db[ref_id].get("username", "друган")
            
            success_text = (
                f"🎉 <b>Новый реферал подтвержден!</b>\n"
                f"👤 Гость: <b>@{username}</b>\n"
                f"🤝 Пригласил: <b>@{referrer_name}</b> (Прогресс: {count}/10)"
            )
            
            try:
                await bot.send_message(int(ref_id), success_text, parse_mode="HTML")
            except:
                pass
            
            # Отправка отчета тебе в ЛС
            try:
                await bot.send_message(ADMIN_CHAT_ID, success_text, parse_mode="HTML")
            except Exception as e:
                print(f"Не удалось отправить отчет админу: {e}")

            if count >= 10:
                try:
                    await bot.send_message(int(ref_id), f"🔥 Норма 10/10 выполнена! Свяжись с админом для получения 50 рублей.", parse_mode="HTML")
                except:
                    pass

    role = users_db[user_id_str]['role']
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Подписаться на ТГК", url=CHANNEL_LINK)],
        [InlineKeyboardButton(text="✅ Проверить подписку и зачесть рефку", callback_data="check_sub")]
    ])

    text = (
        f"Здарова, {username}! Добро пожаловать.\n\n"
        f"Твой текущий тег: <b>{role}</b>\n\n"
        f"⚠️ <b>Внимание (Цемент безопасности):</b> Чтобы твой друг получил балл за приглашение, тебе нужно подписаться на наш канал кнопкой ниже и нажать проверку!"
    )
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

@dp.callback_query(F.data == "check_sub")
async def process_check_sub(callback: CallbackQuery):
    user_id_str = str(callback.from_user.id)
    username = callback.from_user.username or callback.from_user.first_name
    
    is_subscribed = await check_subscription(callback.from_user.id)
    
    if not is_subscribed:
        await callback.answer("❌ Ты еще не подписался на канал! Подпишись, потом жми проверку.", show_alert=True)
        return
        
    if user_id_str in users_db and users_db[user_id_str].get("pending_ref"):
        ref_id = users_db[user_id_str]["pending_ref"]
        if ref_id in users_db and user_id_str not in users_db[ref_id]["invited"]:
            users_db[ref_id]["invited"].append(user_id_str)
            users_db[ref_id]["refs_count"] += 1
            count = users_db[ref_id]["refs_count"]
            users_db[user_id_str]["pending_ref"] = None
            users_db[user_id_str]["invited_by"] = ref_id
            save_db()
            
            referrer_name = users_db[ref_id].get("username", "друган")
            
            success_text = (
                f"🎉 <b>Новый реферал подтвержден!</b>\n"
                f"👤 Гость: <b>@{username}</b>\n"
                f"🤝 Пригласил: <b>@{referrer_name}</b> (Прогресс: {count}/10)"
            )
            
            try:
                await bot.send_message(int(ref_id), success_text, parse_mode="HTML")
            except:
                pass
                
            try:
                await bot.send_message(ADMIN_CHAT_ID, success_text, parse_mode="HTML")
            except Exception as e:
                print(f"Не удалось отправить отчет админу: {e}")
                
            if count >= 10:
                try:
                    await bot.send_message(int(ref_id), f"🔥 Норма 10/10 выполнена! Свяжись с админом для получения 50 рублей.", parse_mode="HTML")
                except:
                    pass

    await callback.message.edit_text(
        f"✅ <b>Подписка успешно подтверждена!</b> Добро в движуху оформлено.",
        parse_mode="HTML"
    )
    await callback.answer()

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
        f"🛡 <b>Защита от накрутки (Цемент):</b> Рефка засчитается только после того, как гость запустит бота и подтвердит подписку на канал!\n\n"
        f"👥 Приглашено гостей: <b>{count}/10</b>\n"
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
    print("Бот запущен с отправкой отчетов админу в ЛС...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
