import os
import asyncio
import logging

from fastapi import FastAPI
import uvicorn

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile

from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Alignment, Font

# ================== ENV ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi")

logging.basicConfig(level=logging.INFO)

# ================== BOT ==================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

bot_task: asyncio.Task | None = None

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

# ======== SAVOLLAR (SANA BITTA QILIB) ========
steps = [
    "Lavozimni kiriting:",
    "Familya, ism, sharifingizni kiriting:",
    "Tug‘ilgan sana (kun.oy.yil):",
    "Otangizning familya, ism, sharifini kiriting:",
    "Otangiz tug‘ilgan sana (kun.oy.yil):",
    "Onangizning familya, ism, sharifini kiriting:",
    "Onangiz tug‘ilgan sana (kun.oy.yil):",
    "Telefon raqam (hodimniki):",
    "Telefon raqam (otasiniki):",
    "Telefon raqam (onasiniki):"
]

# ======== KEYLAR ========
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

# ================== KLAWITURA ==================
def filial_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f, callback_data=f"filial:{f}")]
            for f in FILIALS
        ]
    )

# ================== START ==================
@dp.message(Command("start"))
async def start(message: types.Message):
    user_step[message.chat.id] = 0
    user_data[message.chat.id] = {}
    await message.answer("Filialni tanlang:", reply_markup=filial_keyboard())

# ================== EXCEL ==================
@dp.message(Command("excel"))
async def export_excel(message: types.Message):
    if message.chat.id != ADMIN_ID:
        await message.answer("⛔ Siz admin emassiz")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Arizalar"

    headers = [
        "№", "Filial", "Lavozim", "F.I.SH",
        "Tug‘ilgan sana",
        "Otasi F.I.SH", "Otasi tug‘ilgan sana",
        "Onasi F.I.SH", "Onasi tug‘ilgan sana",
        "Telefon (hodim)",
        "Telefon (ota)",
        "Telefon (ona)"
    ]

    ws.append(headers)

    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    for i, app in enumerate(applications, 1):
        ws.append([
            i,
            app.get("filial", ""),
            app.get("lavozim", ""),
            app.get("fio", ""),
            app.get("t_sana", ""),
            app.get("ofio", ""),
            app.get("o_sana", ""),
            app.get("mfio", ""),
            app.get("m_sana", ""),
            app.get("phone_hodim", ""),
            app.get("phone_ota", ""),
            app.get("phone_ona", "")
        ])

    for col in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            if cell.value:
                max_length = max(max_length, len(str(cell.value)))
            cell.alignment = Alignment(wrap_text=True, vertical="center")
        ws.column_dimensions[col_letter].width = max_length + 4

    file_name = "arizalar.xlsx"
    wb.save(file_name)

    await message.answer_document(FSInputFile(file_name))

# ================== FILIAL ==================
@dp.callback_query(lambda c: c.data.startswith("filial:"))
async def filial_chosen(callback: types.CallbackQuery):
    chat_id = callback.message.chat.id
    filial = callback.data.split(":")[1]

    user_data[chat_id]["filial"] = filial
    user_step[chat_id] = 0

    await callback.message.edit_text(f"✅ Tanlangan filial: {filial}")
    await bot.send_message(chat_id, steps[0])
    await callback.answer()

# ================== FORMA ==================
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
        del user_step[chat_id]
        del user_data[chat_id]

# ================== FASTAPI ==================
app = FastAPI()

@app.get("/")
def root():
    return {"status": "bot is running"}

async def start_bot():
    await dp.start_polling(bot)

@app.on_event("startup")
async def on_startup():
    global bot_task
    bot_task = asyncio.create_task(start_bot())

# ================== RESTART ==================
@dp.message(Command("restart"))
async def restart_bot(message: types.Message):
    if message.chat.id != ADMIN_ID:
        await message.answer("⛔ Siz admin emassiz")
        return

    applications.clear()
    user_step.clear()
    user_data.clear()

    await message.answer(
        "♻️ Bot to‘liq reset qilindi.\n"
        "✅ Barcha formalar tozalandi\n"
        "✅ Excel ma’lumotlari o‘chirildi\n"
        "🚀 Bot boshidan ishlayapti"
    )

# ================== RUN ==================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("bot:app", host="0.0.0.0", port=port)
