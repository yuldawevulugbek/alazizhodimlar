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


BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN topilmadi")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
CHANNELS = [
    "@codingwith_ulugbek",
    "@luboykanalgr"
]
applications = []
user_step = {}
user_data = {}

FILIALS = [
    "Niyazbosh", "Olmazor", "Chinoz",
    "Kasblar", "Gulbahor", "Konditeriski", "Mevazor"
]

steps = [
    "Familya, ism, sharifingizni kiriting:",   # 1
    "Lavozimni kiriting:",                     # 2
    "Tug‘ilgan sana (kun.oy.yil):",             # 3
    "Telefon raqamingiz:",                     # 4

    "Otangiz familya, ism, sharifi:",          # 5
    "Otangiz tug‘ilgan sana (kun.oy.yil):",    # 6
    "Otangiz telefon raqami:",                 # 7

    "Onangiz familya, ism, sharifi:",          # 8
    "Onangiz tug‘ilgan sana (kun.oy.yil):",    # 9
    "Onangiz telefon raqami:",                 # 10

    "Turmush o‘rtog‘ingiz familya, ism, sharifi:",
    "Turmush o‘rtog‘ingiz tug‘ilgan sana (kun.oy.yil):",
    "Turmush o‘rtog‘ingiz telefon raqami:",

    "1-farzand familya, ism, sharifi:",
    "1-farzand tug‘ilgan sana (kun.oy.yil):",

    "2-farzand familya, ism, sharifi:",
    "2-farzand tug‘ilgan sana (kun.oy.yil):",

    "3-farzand familya, ism, sharifi:",
    "3-farzand tug‘ilgan sana (kun.oy.yil):"
]

keys = [
    "lavozim",

    "fio",
    "t_sana",
    "phone_hodim",

    "ofio",
    "o_sana",
    "phone_ota",

    "mfio",
    "m_sana",
    "phone_ona",

    "sfio",
    "s_sana",
    "phone_spouse",

    "child1_fio",
    "child1_sana",

    "child2_fio",
    "child2_sana",

    "child3_fio",
    "child3_sana"
]

def subscribe_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📢 Coding with Ulugbek", url="https://t.me/codingwith_ulugbek")],
        [InlineKeyboardButton("📢 Luboy kanal", url="https://t.me/luboykanalgr")],
        [InlineKeyboardButton("✅ Tekshirish", callback_data="check_sub")]
    ])

def filial_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f, callback_data=f"filial:{f}")]
        for f in FILIALS
    ])
async def check_subscription(user_id: int) -> bool:
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except:
            return False
    return True
@dp.message(Command("start"))
async def start(message: types.Message):
    if not await check_subscription(message.from_user.id):
        await message.answer(
            "❗ Botdan foydalanish uchun kanallarga obuna bo‘ling:",
            reply_markup=subscribe_keyboard()
        )
        return

    user_data[message.chat.id] = {}
    user_step[message.chat.id] = 0

    # 🔥 BIRINCHI SAVOL
    await message.answer(steps[0])

@dp.callback_query(lambda c: c.data == "check_sub")
async def check_sub(call: types.CallbackQuery):
    if not await check_subscription(call.from_user.id):
        await call.answer("❌ Hali obuna to‘liq emas", show_alert=True)
        return

    user_step[call.message.chat.id] = 0
    user_data[call.message.chat.id] = {}

    await call.message.edit_text("✅ Obuna tasdiqlandi\n\nFilialni tanlang:")
    await call.message.edit_reply_markup(reply_markup=filial_keyboard())
    await call.answer()
@dp.callback_query(lambda c: c.data.startswith("filial:"))
async def filial_chosen(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    filial = call.data.split(":")[1]

    user_data[chat_id]["filial"] = filial

    await call.message.edit_text(f"✅ Tanlangan filial: {filial}")
    await bot.send_message(chat_id, steps[user_step[chat_id]])
    await call.answer()

@dp.message(Command("excel"))
async def export_excel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Siz admin emassiz")
        return

    if not applications:
        await message.answer("📭 Hozircha arizalar yo‘q")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Arizalar"

    headers = [
    "№", "Filial", "Lavozim", "F.I.SH", "Tug‘ilgan sana", "Telefon",
    "Otasi F.I.SH", "Otasi sana", "Otasi telefon",
    "Onasi F.I.SH", "Onasi sana", "Onasi telefon",
    "Turmush o‘rtog‘i F.I.SH", "Turmush o‘rtog‘i sana", "Turmush o‘rtog‘i telefon",
    "1-farzand F.I.SH", "1-farzand sana",
    "2-farzand F.I.SH", "2-farzand sana",
    "3-farzand F.I.SH", "3-farzand sana"
]


    ws.append(headers)

    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.alignment = Alignment(horizontal="center")

    for i, app in enumerate(applications, 1):
       ws.append([
            i,
            app.get("filial",""),
            app.get("lavozim",""),
            app.get("fio",""),
            app.get("t_sana",""),
            app.get("phone_hodim",""),

            app.get("ofio",""),
            app.get("o_sana",""),
            app.get("phone_ota",""),

            app.get("mfio",""),
            app.get("m_sana",""),
            app.get("phone_ona",""),

            app.get("sfio",""),
            app.get("s_sana",""),
            app.get("phone_spouse",""),

            app.get("child1_fio",""),
            app.get("child1_sana",""),

            app.get("child2_fio",""),
            app.get("child2_sana",""),

            app.get("child3_fio",""),
            app.get("child3_sana","")
        ])


    file = "arizalar.xlsx"
    wb.save(file)
    await message.answer_document(FSInputFile(file))
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

    # 🔥 F.I.Sh dan keyin filial chiqaramiz
    if step == 1 and "filial" not in user_data[chat_id]:
        user_step[chat_id] = step
        await message.answer(
            "Filialni tanlang:",
            reply_markup=filial_keyboard()
        )
        return

    if step < len(steps):
        user_step[chat_id] = step
        await message.answer(steps[step])
    else:
        applications.append(user_data[chat_id])
        await message.answer("✅ Arizangiz qabul qilindi")
        user_step.pop(chat_id, None)
        user_data.pop(chat_id, None)

app = FastAPI()

@app.get("/")
async def root():
    return {"status": "bot is running"}

@app.on_event("startup")
async def startup():
    asyncio.create_task(dp.start_polling(bot))
if __name__ == "__main__":
    uvicorn.run(
        "bot:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )


