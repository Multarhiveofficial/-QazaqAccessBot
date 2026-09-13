import asyncio
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# =========================================================
# ⚙️ БАПТАУЛАР
# =========================================================

# ⚠️ ОСЫ ЖЕРГЕ BOTFATHER-ДАН АЛҒАН ЖАҢА ТОКЕНДІ ӨЗІҢ ҚОЙ
BOT_TOKEN = "Your token here"

# Алғашқы іске қосқанда 0 қалдыр
# Кейін боттан /id арқылы өз ID-іңді алып, осында жаз
ADMIN_ID = 1486782145

# Сен берген жеке арна сілтемесі
CHANNEL_INVITE_LINK = "https://t.me/+qhBLbsg-rM4wOTQy"


# =========================================================
# 💾 DATABASE
# =========================================================

db = sqlite3.connect("qazaq_access.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    telegram_id INTEGER PRIMARY KEY,
    username TEXT,
    full_name TEXT,
    age INTEGER,
    status TEXT DEFAULT 'new',
    created_at TEXT,
    reviewed_at TEXT
)
""")

db.commit()


def get_user(telegram_id):
    cursor.execute(
        "SELECT * FROM users WHERE telegram_id = ?",
        (telegram_id,)
    )
    return cursor.fetchone()


def save_user(telegram_id, username, full_name, age):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO users
        (telegram_id, username, full_name, age, status, created_at)
        VALUES (?, ?, ?, ?, 'new', ?)

        ON CONFLICT(telegram_id)
        DO UPDATE SET
            username = excluded.username,
            full_name = excluded.full_name,
            age = excluded.age,
            status = 'new'
    """, (
        telegram_id,
        username,
        full_name,
        age,
        now
    ))

    db.commit()


def change_status(telegram_id, status):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        UPDATE users
        SET status = ?, reviewed_at = ?
        WHERE telegram_id = ?
    """, (
        status,
        now,
        telegram_id
    ))

    db.commit()


# =========================================================
# 🤖 BOT
# =========================================================

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)

dp = Dispatcher(storage=MemoryStorage())


# =========================================================
# 📝 STATES
# =========================================================

class Registration(StatesGroup):
    waiting_name = State()
    waiting_age = State()


# =========================================================
# 🔘 KEYBOARDS
# =========================================================

def check_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 ТЕКСЕРУГЕ ЖІБЕРУ",
                    callback_data="send_check"
                )
            ]
        ]
    )


def admin_keyboard(user_id):

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="✅ РҰҚСАТ БЕРУ",
                    callback_data=f"approve_{user_id}"
                )
            ],

            [
                InlineKeyboardButton(
                    text="❌ ҚАБЫЛДАМАУ",
                    callback_data=f"reject_{user_id}"
                )
            ]

        ]
    )


def channel_keyboard():

    return InlineKeyboardMarkup(
        inline_keyboard=[

            [
                InlineKeyboardButton(
                    text="📢 АРНАҒА КІРУ",
                    url=CHANNEL_INVITE_LINK
                )
            ]

        ]
    )


# =========================================================
# 🚀 START
# =========================================================

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):

    await state.clear()

    await message.answer(
        "👋 <b>Сәлеметсіз бе!</b>\n\n"

        "🇰🇿 <b>Qazaq Access</b> жүйесіне қош келдіңіз!\n\n"

        "Жеке арнаға кіру үшін қысқаша "
        "өтініш толтыру қажет.\n\n"

        "⏳ Өтінішіңіз админ тарапынан қаралады.\n"
        "Нәтиже осы бот арқылы жіберіледі.\n\n"

        "👤 <b>Атыңызды жазыңыз:</b>"
    )

    await state.set_state(
        Registration.waiting_name
    )


# =========================================================
# 👤 NAME
# =========================================================

@dp.message(Registration.waiting_name)
async def receive_name(
    message: Message,
    state: FSMContext
):

    if not message.text:

        await message.answer(
            "❗ Атыңызды мәтін түрінде жазыңыз."
        )

        return

    name = message.text.strip()

    if len(name) < 2:

        await message.answer(
            "❗ Атыңызды дұрыс енгізіңіз."
        )

        return

    if len(name) > 100:

        await message.answer(
            "❗ Атыңыз тым ұзын."
        )

        return

    await state.update_data(
        full_name=name
    )

    await message.answer(
        "🎂 <b>Жасыңызды жазыңыз:</b>\n\n"
        "Мысалы: <b>18</b>"
    )

    await state.set_state(
        Registration.waiting_age
    )


# =========================================================
# 🎂 AGE
# =========================================================

@dp.message(Registration.waiting_age)
async def receive_age(
    message: Message,
    state: FSMContext
):

    if not message.text:

        await message.answer(
            "❗ Жасыңызды санмен енгізіңіз."
        )

        return

    try:

        age = int(message.text.strip())

    except ValueError:

        await message.answer(
            "❗ Жасыңызды тек санмен жазыңыз.\n\n"
            "Мысалы: <b>18</b>"
        )

        return

    if age < 13 or age > 100:

        await message.answer(
            "❗ Жасыңызды дұрыс енгізіңіз."
        )

        return

    data = await state.get_data()

    full_name = data["full_name"]

    telegram_id = message.from_user.id

    if message.from_user.username:

        username = "@" + message.from_user.username

    else:

        username = "Username жоқ"

    save_user(
        telegram_id,
        username,
        full_name,
        age
    )

    await state.clear()

    await message.answer(
        "🔐 <b>Өтініш дайын!</b>\n\n"

        "👤 Аты: <b>" + full_name + "</b>\n"
        "🎂 Жасы: <b>" + str(age) + "</b>\n\n"

        "Төмендегі батырманы басып, "
        "өтінішті админге жіберіңіз.\n\n"

        "⏳ Өтініш қолмен тексеріледі."
        ,
        reply_markup=check_keyboard()
    )


# =========================================================
# 📤 SEND TO ADMIN
# =========================================================

@dp.callback_query(F.data == "send_check")
async def send_check(callback: CallbackQuery):

    user_id = callback.from_user.id

    user = get_user(user_id)

    if not user:

        await callback.answer(
            "Алдымен /start басыңыз.",
            show_alert=True
        )

        return

    if ADMIN_ID == 0:

        await callback.answer(
            "⚠️ ADMIN_ID әлі орнатылмаған.",
            show_alert=True
        )

        return

    telegram_id = user[0]
    username = user[1]
    full_name = user[2]
    age = user[3]
    status = user[4]

    if status == "pending":

        await callback.answer(
            "⏳ Өтінішіңіз қазір тексерілуде.",
            show_alert=True
        )

        return

    change_status(
        telegram_id,
        "pending"
    )

    admin_text = (
        "🔔 <b>ЖАҢА ӨТІНІШ</b>\n\n"

        "━━━━━━━━━━━━━━\n"

        f"👤 <b>Аты:</b> {full_name}\n"
        f"🎂 <b>Жасы:</b> {age}\n"
        f"📱 <b>Username:</b> {username}\n"
        f"🆔 <b>Telegram ID:</b> "
        f"<code>{telegram_id}</code>\n"

        "━━━━━━━━━━━━━━\n\n"

        "Пайдаланушының өтінішін "
        "қарап шығыңыз."
    )

    await bot.send_message(
        ADMIN_ID,
        admin_text,
        reply_markup=admin_keyboard(
            telegram_id
        )
    )

    await callback.message.edit_text(
        "✅ <b>ӨТІНІШ ЖІБЕРІЛДІ!</b>\n\n"

        "Сіздің өтінішіңіз админге "
        "жіберілді.\n\n"

        "⏳ Тексеру аяқталғаннан кейін "
        "нәтиже осы бот арқылы келеді."
    )

    await callback.answer(
        "Өтініш жіберілді!"
    )


# =========================================================
# ✅ APPROVE
# =========================================================

@dp.callback_query(F.data.startswith("approve_"))
async def approve_user(
    callback: CallbackQuery
):

    if callback.from_user.id != ADMIN_ID:

        await callback.answer(
            "⛔ Бұл батырма админге арналған.",
            show_alert=True
        )

        return

    user_id = int(
        callback.data.split("_")[1]
    )

    user = get_user(user_id)

    if not user:

        await callback.answer(
            "Пайдаланушы табылмады.",
            show_alert=True
        )

        return

    change_status(
        user_id,
        "approved"
    )

    await bot.send_message(

        user_id,

        "🎉 <b>ТЕКСЕРУ СӘТТІ ӨТТІ!</b>\n\n"

        "Сіздің өтінішіңіз мақұлданды. ✅\n\n"

        "Енді жеке арнаға төмендегі "
        "батырма арқылы кіре аласыз:",

        reply_markup=channel_keyboard()
    )

    await callback.message.edit_text(

        callback.message.text
        + "\n\n"
        "━━━━━━━━━━━━━━\n"
        "✅ <b>МӘРТЕБЕ: МАҚҰЛДАНДЫ</b>"
    )

    await callback.answer(
        "Рұқсат берілді! ✅"
    )


# =========================================================
# ❌ REJECT
# =========================================================

@dp.callback_query(F.data.startswith("reject_"))
async def reject_user(
    callback: CallbackQuery
):

    if callback.from_user.id != ADMIN_ID:

        await callback.answer(
            "⛔ Бұл батырма админге арналған.",
            show_alert=True
        )

        return

    user_id = int(
        callback.data.split("_")[1]
    )

    user = get_user(user_id)

    if not user:

        await callback.answer(
            "Пайдаланушы табылмады.",
            show_alert=True
        )

        return

    change_status(
        user_id,
        "rejected"
    )

    await bot.send_message(

        user_id,

        "❌ <b>ӨТІНІШ ҚАБЫЛДАНБАДЫ</b>\n\n"

        "Кешіріңіз, бұл жолы өтінішіңіз "
        "мақұлданбады.\n\n"

        "Қажет болса, мәліметтеріңізді "
        "қайта енгізіп, жаңа өтініш "
        "жібере аласыз.",

        reply_markup=check_keyboard()
    )

    await callback.message.edit_text(

        callback.message.text
        + "\n\n"
        "━━━━━━━━━━━━━━\n"
        "❌ <b>МӘРТЕБЕ: ҚАБЫЛДАНБАДЫ</b>"
    )

    await callback.answer(
        "Өтініш қабылданбады."
    )


# =========================================================
# 🆔 GET ID
# =========================================================

@dp.message(Command("id"))
async def get_id(message: Message):

    await message.answer(

        "🆔 <b>Сіздің Telegram ID:</b>\n\n"

        f"<code>{message.from_user.id}</code>\n\n"

        "Осы санды кодтағы "
        "<code>ADMIN_ID</code> орнына қойыңыз."
    )


# =========================================================
# 📊 STATISTICS
# =========================================================

@dp.message(Command("stats"))
async def statistics(message: Message):

    if message.from_user.id != ADMIN_ID:

        return

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    total = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM users "
        "WHERE status='pending'"
    )

    pending = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM users "
        "WHERE status='approved'"
    )

    approved = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM users "
        "WHERE status='rejected'"
    )

    rejected = cursor.fetchone()[0]

    await message.answer(

        "📊 <b>QAZAQ ACCESS</b>\n\n"

        f"👥 Барлығы: <b>{total}</b>\n"
        f"⏳ Тексерілуде: <b>{pending}</b>\n"
        f"✅ Мақұлданды: <b>{approved}</b>\n"
        f"❌ Қабылданбады: <b>{rejected}</b>"
    )


# =========================================================
# ℹ️ UNKNOWN
# =========================================================

@dp.message()
async def unknown(message: Message):

    await message.answer(

        "ℹ️ Ботты пайдалану үшін "
        "<b>/start</b> командасын басыңыз."
    )


# =========================================================
# ▶️ RUN
# =========================================================

async def main():

    print("================================")
    print("🤖 QazaqAccessBot іске қосылды!")
    print("================================")

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())
