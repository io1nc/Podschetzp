import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# ВСТАВЬ СЮДА СВОЙ ТОКЕН БОТА
BOT_TOKEN = "8162178154:AAFI4dyxnCt3DRThA7JfeY9ucPRUYMlgu7g"

dp = Dispatcher(storage=MemoryStorage())

# Состояния ввода
class SalaryForm(StatesGroup):
    level = State()
    shift_10 = State()
    shift_12 = State()
    training = State()
    conv = State()
    engage = State()
    revenue = State()

# Коэффициенты бонусов
JSE_COEFS = {
    (111, float("inf")): 1.25, (110, 110): 1.25, (109, 109): 1.225, (108, 108): 1.2, (107, 107): 1.175,
    (106, 106): 1.15, (105, 105): 1.125, (104, 104): 1.1, (103, 103): 1.075, (102, 102): 1.05,
    (101, 101): 1.025, (100, 100): 1.0, (90, 99): 0.9, (80, 89): 0.8, (0, 79): 0.0,
}
SE_COEFS = {
    (111, float("inf")): 1.25, (110, 110): 1.25, (109, 109): 1.225, (108, 108): 1.2, (107, 107): 1.175,
    (106, 106): 1.15, (105, 105): 1.125, (104, 104): 1.1, (103, 103): 1.075, (102, 102): 1.05,
    (101, 101): 1.025, (100, 100): 1.0, (90, 99): 0.8, (80, 89): 0.6, (0, 79): 0.0,
}

# Ставки
RATES = {
    "JSE": {"fix": 265, "bonus": 177},
    "SE": {"fix": 311, "bonus": 207},
    "SSE": {"fix": 374, "bonus": 249}
}

def get_bonus_coef(pct: int, level: str) -> float:
    table = JSE_COEFS if level == "JSE" else SE_COEFS
    for (min_val, max_val), coef in table.items():
        if min_val <= pct <= max_val:
            return coef
    return 0.0

@dp.message(F.text == "/start")
async def start(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="JSE"), KeyboardButton(text="SE"), KeyboardButton(text="SSE")]
    ], resize_keyboard=True)
    await message.answer("Выбери уровень:", reply_markup=kb)
    await state.set_state(SalaryForm.level)

@dp.message(SalaryForm.level)
async def shift_10_step(message: types.Message, state: FSMContext):
    await state.update_data(level=message.text)
    await message.answer("Сколько смен с 10:00 до 22:00 (обед 1.5 ч)?")
    await state.set_state(SalaryForm.shift_10)

@dp.message(SalaryForm.shift_10)
async def shift_12_step(message: types.Message, state: FSMContext):
    await state.update_data(shift_10=int(message.text))
    await message.answer("Сколько смен с 12:00 до 22:00 (обед 1 ч)?")
    await state.set_state(SalaryForm.shift_12)

@dp.message(SalaryForm.shift_12)
async def training_step(message: types.Message, state: FSMContext):
    await state.update_data(shift_12=int(message.text))
    await message.answer("Сколько часов обучения?")
    await state.set_state(SalaryForm.training)

@dp.message(SalaryForm.training)
async def conv_step(message: types.Message, state: FSMContext):
    await state.update_data(training=float(message.text))
    await message.answer("Процент выполнения Conversion?")
    await state.set_state(SalaryForm.conv)

@dp.message(SalaryForm.conv)
async def engage_step(message: types.Message, state: FSMContext):
    await state.update_data(conv=int(message.text))
    await message.answer("Процент выполнения Engage?")
    await state.set_state(SalaryForm.engage)

@dp.message(SalaryForm.engage)
async def revenue_step(message: types.Message, state: FSMContext):
    await state.update_data(engage=int(message.text))
    await message.answer("Процент выполнения Revenue?")
    await state.set_state(SalaryForm.revenue)

@dp.message(SalaryForm.revenue)
async def calculate(message: types.Message, state: FSMContext):
    await state.update_data(revenue=int(message.text))
    data = await state.get_data()

    level = data["level"]
    shift_10 = data["shift_10"]
    shift_12 = data["shift_12"]
    training = data["training"]
    conv = data["conv"]
    engage = data["engage"]
    revenue = data["revenue"]

    fix = RATES[level]["fix"]
    bonus = RATES[level]["bonus"]

    total_hours = shift_10 * 10.5 + shift_12 * 9 + training

    conv_coef = get_bonus_coef(conv, level)
    engage_coef = get_bonus_coef(engage, level)
    revenue_coef = get_bonus_coef(revenue, level)

    bonus_coef = conv_coef * engage_coef * revenue_coef
    salary = total_hours * (fix + bonus * bonus_coef)
    salary = round(salary, 2)

    await message.answer(f"Итоговая зарплата: {salary} ₽")
    await state.clear()

async def main():
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())