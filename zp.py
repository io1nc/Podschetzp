from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    ContextTypes,
)

GRADE, SHIFT_10_22, SHIFT_12_22, REVENUE, KD, ENGAGE, TRAINING = range(7)

grades = {
    "JSE": {"fix": 265, "bonus": 177},
    "SE": {"fix": 311, "bonus": 207},
    "SSE": {"fix": 374, "bonus": 249},
}

def get_bonus_coefficient(pct: int) -> float:
    if pct >= 110:
        return 1.25
    elif pct == 109:
        return 1.225
    elif pct == 108:
        return 1.2
    elif pct == 107:
        return 1.175
    elif pct == 106:
        return 1.15
    elif pct == 105:
        return 1.225
    elif pct == 104:
        return 1.1
    elif pct == 103:
        return 1.075
    elif pct == 102:
        return 1.05
    elif pct == 101:
        return 1.025
    elif pct == 100:
        return 1
    elif 90 <= pct < 100:
        return 0.9
    elif 80 <= pct < 90:
        return 0.8
    else:
        return 0

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reply_markup = ReplyKeyboardMarkup([["Рассчитать зарплату"]], resize_keyboard=True)
    await update.message.reply_text("Привет! Нажми кнопку ниже, чтобы начать:", reply_markup=reply_markup)

async def begin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [KeyboardButton("JSE"), KeyboardButton("SE"), KeyboardButton("SSE")]
    ]
    reply_markup = ReplyKeyboardMarkup(buttons, one_time_keyboard=True, resize_keyboard=True)
    await update.message.reply_text("Выберите грейд:", reply_markup=reply_markup)
    return GRADE

async def set_grade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    grade = update.message.text.strip().upper()
    if grade not in grades:
        await update.message.reply_text(
            "Некорректный грейд. Пожалуйста, выберите из кнопок: JSE, SE или SSE."
        )
        return GRADE
    context.user_data["grade"] = grade
    await update.message.reply_text(
        "Сколько смен с 10:00 до 22:00?", reply_markup=ReplyKeyboardRemove()
    )
    return SHIFT_10_22

async def set_shift_10_22(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        shift_10_22 = int(update.message.text.strip())
        if shift_10_22 < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число смен (0 или больше).")
        return SHIFT_10_22
    context.user_data["shift_10_22"] = shift_10_22
    await update.message.reply_text("Сколько смен с 12:00 до 22:00?")
    return SHIFT_12_22

async def set_shift_12_22(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        shift_12_22 = int(update.message.text.strip())
        if shift_12_22 < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное число смен (0 или больше).")
        return SHIFT_12_22
    context.user_data["shift_12_22"] = shift_12_22
    await update.message.reply_text("Процент выполнения Revenue?")
    return REVENUE

async def set_revenue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        revenue = int(update.message.text.strip())
        if not (0 <= revenue <= 200):
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Введите корректный процент (от 0 до 200).")
        return REVENUE
    context.user_data["revenue"] = revenue
    await update.message.reply_text("Процент выполнения КД?")
    return KD

async def set_kd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        kd = int(update.message.text.strip())
        if not (0 <= kd <= 200):
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Введите корректный процент (от 0 до 200).")
        return KD
    context.user_data["kd"] = kd
    await update.message.reply_text("Процент выполнения Engage?")
    return ENGAGE

async def set_engage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        engage = int(update.message.text.strip())
        if not (0 <= engage <= 200):
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Введите корректный процент (от 0 до 200).")
        return ENGAGE
    context.user_data["engage"] = engage
    await update.message.reply_text("Сколько часов обучения?")
    return TRAINING

async def set_training(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        training = int(update.message.text.strip())
        if training < 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text("Пожалуйста, введите корректное количество часов (0 или больше).")
        return TRAINING
    context.user_data["training"] = training

    grade = context.user_data["grade"]
    fix_rate = grades[grade]["fix"]
    bonus_rate = grades[grade]["bonus"]

    # Часы
    h1 = context.user_data["shift_10_22"] * 10.5
    h2 = context.user_data["shift_12_22"] * 9
    total_hours = h1 + h2
    fix = total_hours * fix_rate

    # Обед
    lunch_hours = context.user_data["shift_10_22"] * 1.5 + context.user_data["shift_12_22"] * 1
    lunch_pay = lunch_hours * fix_rate

    # Обучение
    training_pay = training * fix_rate

    # Бонусы
    revenue_bonus = bonus_rate * 0.4
    kd_bonus = bonus_rate * 0.3
    engage_bonus = bonus_rate * 0.3

    rb = revenue_bonus * get_bonus_coefficient(context.user_data["revenue"])
    kb = kd_bonus * get_bonus_coefficient(context.user_data["kd"])
    eb = engage_bonus * get_bonus_coefficient(context.user_data["engage"])
    total_bonus_hour = rb + kb + eb
    total_bonus = total_bonus_hour * total_hours

    salary = fix + lunch_pay + training_pay + total_bonus

    await update.message.reply_text(
        f"Итоговая зарплата: {round(salary, 2)} руб.\n\n"
        f"Детали:\n"
        f"Фиксированная часть: {round(fix, 2)} руб.\n"
        f"Оплата обеда: {round(lunch_pay, 2)} руб.\n"
        f"Оплата обучения: {round(training_pay, 2)} руб.\n"
        f"Бонусы: {round(total_bonus, 2)} руб.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token("7390659901:AAHGDuJ3bASOSb5_ZXwinSwR3xEONOD2YDo").build()

    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("Рассчитать зарплату"), begin)],
        states={
            GRADE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_grade)],
            SHIFT_10_22: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_shift_10_22)],
            SHIFT_12_22: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_shift_12_22)],
            REVENUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_revenue)],
            KD: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_kd)],
            ENGAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_engage)],
            TRAINING: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_training)],
        },
        fallbacks=[],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv)

    app.run_polling()

if __name__ == "__main__":
    main()
