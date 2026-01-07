import os
import asyncio
import logging

from fastapi import FastAPI
import uvicorn

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font

# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi")

logging.basicConfig(level=logging.INFO)

# ================== BOT ==================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================== MAJBURIY KANALLAR ==================
CHANNELS = [
    "@codingwith_ulugbek",
    "@luboykanalgr"
]

# ================== DATA ==================
applications = []
user_step = {}
user_data = {}

FILIALS = [
    "Niyazbosh",
    "Olmazor",
    "Chinoz",
    "Kasblar",
    "Gulbahor",
    "Konditeriski",
    "Mevazor"
]

steps = [
    "Lavozimni kiriting:",
    "Familya, ism, sharifingizni kiriting:",
    "Tug‘ilgan sana (kun.oy.yil):",
    "Otangizning F.I.SH:",
    "Otangiz tug‘ilgan sana:",
    "Onangizning F.I.SH:",
    "Onangiz tug‘ilgan sana:",
    "Telefon raqam (hodim):",
    "Telefon raqam (ota):",
    "Telefon raqam (ona):"
]

keys = [
    "lavozim",
    "fio",
    "t_sana",
    "ofio",
    "o_sana",
    "mfio",
    "m_sana",
    "phone_hodim",
    "phone_ota",
    "phone_ona"
]

# ================== KEYBOARDS ==================
def subscribe_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Coding with Ulugbek",
                    url="https://t.me/codingwith_ulugbek"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Luboy kanal",
                    url="https://t.me/luboykanalgr"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Tekshirish",
                    callback_data="check_sub"
                )
            ]
        ]
    )

def filial_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f, callback_data=f"filial:{f}")]
            for f in FILIALS
        ]
    )

# ================== SUBSCRIPTION CHECK ==================
async def check_subscription(user_id: int) -> bool:
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except Exception as e:
            logging.error(f"Subscription check error ({channel}): {e}")
            return False
    return True

# ================== START ==================
@dp.message(Command("start"))
async def start(message: types.Message):
    # darhol javob (sekindek tuyulmasligi uchun)
    await message.answer("⏳ Tekshirilmoqda, iltimos kuting...")

    if not await check_subscription(message.from_user.id):
        await message.answer(
            "❗ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:",
            reply_markup=subscribe_keyboard()
        )
        return

    user_step[message.chat.id] = 0
    user_data[message.chat.id] = {}

    await message.answer(
        "✅ Obuna tasdiqlandi\n\nFilialni tanlang:",
        reply_markup=filial_keyboard()
    )

# ================== CHECK BUTTON ==================
@dp.callback_query(lambda c: c.data == "check_sub")
async def check_sub(call: types.CallbackQuery):
    if not await check_subscription(call.from_user.id):
        await call.answer(
            "❌ Hali barcha kanallarga obuna bo‘lmadingiz",
            show_alert=True
        )
        return

    user_step[call.message.chat.id] = 0
    user_data[call.message.chat.id] = {}

    await call.message.edit_text("✅ Obuna tasdiqlandi\n\nFilialni tanlang:")
    await call.message.edit_reply_markup(reply_markup=filial_keyboard())
    await call.answer()

# ================== FILIAL ==================
@dp.callback_query(lambda c: c.data.startswith("filial:"))
async def filial_chosen(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    filial = call.data.split(":")[1]

    user_data[chat_id]["filial"] = filial
    user_step[chat_id] = 0

    await call.message.edit_text(f"✅ Tanlangan filial: {filial}")
    await bot.send_message(chat_id, steps[0])
    await call.answer()

# ================== FORM ==================
@dp.message()
async def form_handler(message: types.Message):
    if message.text.startswith("/"):
        return

    chat_id = message.chat.id
    if chat_id not in user_step:
        return

    step = user_step[chat_id]
    user_data[chat_id][keys[step]] = message.text
    step += 1

    if step < len(steps):
        user_step[chat_id] = step
        await message.answer(steps[step])
    else:
        applications.append(user_data[chat_id])
        await message.answer("✅ Arizangiz qabul qilindi.")
        user_step.pop(chat_id, None)
        user_data.pop(chat_id, None)

# ================== FASTAPI ==================
app = FastAPI()

@app.get("/")
async def root():
    return {"status": "bot is running"}

@app.on_event("startup")
async def startup():
    asyncio.create_task(dp.start_polling(bot))

# ================== RUN ==================
if __name__ == "__main__":
    uvicorn.run(
        "bot:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )

