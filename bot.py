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
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

if not BOT_TOKEN:
    raise RuntimeError("❌ BOT_TOKEN topilmadi")

logging.basicConfig(level=logging.INFO)

# ================== BOT ==================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ================== CHANNELS ==================
CHANNELS = [
    "@codingwith_ulugbek",
    "@luboykanalgr"
]

# ================== DATA ==================
applications = []
user_step = {}
user_data = {}

FILIALS = [
    "Niyazbosh", "Olmazor", "Chinoz",
    "Kasblar", "Gulbahor", "Konditeriski", "Mevazor"
]

# ================== STEPS ==================
steps = [
    "Familya, ism, sharifingizni kiriting:",   # 0
    "Lavozimni kiriting:",                     # 1
    "Tug‘ilgan sana (kun.oy.yil):",            # 2
    "Telefon raqamingiz:",                    # 3

    "Otangiz familya, ism, sharifi:",         # 4
    "Otangiz tug‘ilgan sana (kun.oy.yil):",   # 5
    "Otangiz telefon raqami:",                # 6

    "Onangiz familya, ism, sharifi:",         # 7
    "Onangiz tug‘ilgan sana (kun.oy.yil):",   # 8
    "Onangiz telefon raqami:",                # 9

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
    "fio", "lavozim", "t_sana", "phone_hodim",
    "ofio", "o_sana", "phone_ota",
    "mfio", "m_sana", "phone_ona",
    "sfio", "s_sana", "phone_spouse",
    "child1_fio", "child1_sana",
    "child2_fio", "child2_sana",
    "child3_fio", "child3_sana"
]

# ================== KEYBOARDS ==================
def subscribe_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Coding with Ulugbek", url="https://t.me/codingwith_ulugbek")],
        [InlineKeyboardButton(text="📢 Luboy kanal", url="https://t.me/luboykanalgr")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ])

def filial_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f, callback_data=f"filial:{f}")]
        for f in FILIALS
    ])

# ================== SUB CHECK ==================
async def check_subscription(user_id: int) -> bool:
    for channel in CHANNELS:
        try:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ("member", "administrator", "creator"):
                return False
        except:
            return False
    return True

# ================== START ==================
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

    await message.answer(steps[0])

# ================== CHECK SUB ==================
@dp.callback_query(lambda c: c.data == "check_sub")
async def check_sub(call: types.CallbackQuery):
    if not await check_subscription(call.from_user.id):
        await call.answer("❌ Hali obuna to‘liq emas", show_alert=True)
        return

    user_data[call.message.chat.id] = {}
    user_step[call.message.chat.id] = 0

    await call.message.edit_text("Obuna tasdiqlandi ✅\n\n" + steps[0])
    await call.answer()

# ================== FILIAL ==================
@dp.callback_query(lambda c: c.data.startswith("filial:"))
async def filial_chosen(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    filial = call.data.split(":")[1]

    user_data[chat_id]["filial"] = filial

    await call.message.edit_text(f"✅ Tanlangan filial: {filial}")
    await bot.send_message(chat_id, steps[user_step[chat_id]])
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

    # F.I.Sh dan keyin FILIAL
    if step == 1 and "filial" not in user_data[chat_id]:
        user_step[chat_id] = step
        await message.answer("Filialni tanlang:", reply_markup=filial_keyboard())
        return

    if step < len(steps):
        user_step[chat_id] = step
        await message.answer(steps[step])
    else:
        applications.append(user_data[chat_id])
        await message.answer("✅ Arizangiz qabul qilindi")
        user_step.pop(chat_id)
        user_data.pop(chat_id)

# ================== EXCEL ==================
@dp.message(Command("excel"))
async def export_excel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Siz admin emassiz")
        return

    if not applications:
        await message.answer("📭 Arizalar yo‘q")
        return

    wb = Workbook()
    ws = wb.active
    ws.title = "Arizalar"

    headers = [
        "№","Filial","Lavozim","F.I.SH","Tug‘ilgan sana","Telefon",
        "Otasi F.I.SH","Otasi sana","Otasi telefon",
        "Onasi F.I.SH","Onasi sana","Onasi telefon",
        "Turmush o‘rtog‘i F.I.SH","Turmush o‘rtog‘i sana","Turmush o‘rtog‘i telefon",
        "1-farzand F.I.SH","1-farzand sana",
        "2-farzand F.I.SH","2-farzand sana",
        "3-farzand F.I.SH","3-farzand sana"
    ]

    ws.append(headers)
    for c in ws[1]:
        c.font = Font(bold=True)
        c.alignment = Alignment(horizontal="center")

    for i, a in enumerate(applications, 1):
        ws.append([
            i, a.get("filial"), a.get("lavozim"), a.get("fio"),
            a.get("t_sana"), a.get("phone_hodim"),
            a.get("ofio"), a.get("o_sana"), a.get("phone_ota"),
            a.get("mfio"), a.get("m_sana"), a.get("phone_ona"),
            a.get("sfio"), a.get("s_sana"), a.get("phone_spouse"),
            a.get("child1_fio"), a.get("child1_sana"),
            a.get("child2_fio"), a.get("child2_sana"),
            a.get("child3_fio"), a.get("child3_sana")
        ])

    file = "arizalar.xlsx"
    wb.save(file)
    await message.answer_document(FSInputFile(file))

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
    uvicorn.run("bot:app", host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
