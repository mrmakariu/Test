import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = '7929022853:AAHk0a_uhkf6ARWeywMuoUWe5cjB7t7qgxM'
user_data = {}
message_ids = {}
DATA_FILE = 'user_data.json'

red_numbers = {1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36}
black_numbers = {2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35}

# Загрузка и сохранение

def load_data():
    global user_data
    try:
        with open(DATA_FILE, 'r') as f:
            user_data.update(json.load(f))
    except FileNotFoundError:
        pass

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(user_data, f, indent=2)

# Формат ставок

def format_bets(bets):
    if not bets:
        return "Сделанных ставок нет."
    return "Сделанные ставки:\n" + "\n".join([f"{amt} на {target}" for amt, target in bets])

# /start

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in user_data:
        user_data[user_id] = {"balance": 1000, "bets": []}
    keyboard = [[InlineKeyboardButton("🎰 Рулетка", callback_data="roulette")]]
    await update.message.reply_text("Добро пожаловать в Scam Dub!", reply_markup=InlineKeyboardMarkup(keyboard))
    await update.message.reply_text(f"Баланс: {user_data[user_id]['balance']}₽", reply_markup=InlineKeyboardMarkup(keyboard))
    save_data()

# /bet

async def bet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)

    if user_id not in user_data:
        await update.message.reply_text("Сначала введите /start.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Использование: /bet {сумма} {ставка}")
        return

    try:
        amount = int(context.args[0])
        target = " ".join(context.args[1:]).lower()
    except ValueError:
        await update.message.reply_text("Неверный формат ставки.")
        return

    if amount == 0:
        await update.message.reply_text("Ставка не может быть 0.")
        return

    bets = user_data[user_id]['bets']
    existing_bet = next((b for b in bets if b[1] == target), None)

    if amount > 0:
        if user_data[user_id]['balance'] < amount:
            await update.message.reply_text("Недостаточно средств.")
            return

        if existing_bet:
            bets.remove(existing_bet)
            new_amount = existing_bet[0] + amount
            bets.append((new_amount, target))
        else:
            bets.append((amount, target))

        user_data[user_id]['balance'] -= amount

    elif amount < 0:
        if not existing_bet:
            await update.message.reply_text("Нет такой ставки, чтобы уменьшить.")
            return

        new_amount = existing_bet[0] + amount
        bets.remove(existing_bet)

        if new_amount > 0:
            bets.append((new_amount, target))
        else:
            await update.message.reply_text(f"Ставка на {target} удалена.")

        user_data[user_id]['balance'] += abs(amount)

    save_data()

    message_id = message_ids.get(user_id)
    if message_id:
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=message_id,
                text=f"/bet {amount} {target}\n\n{format_bets(bets)}\nБаланс: {user_data[user_id]['balance']}₽",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎯 Крутить", callback_data="spin")],
                    [InlineKeyboardButton("📜 Правила", callback_data="rules")],
                    [InlineKeyboardButton("🏠 Домой", callback_data="home")]
                ])
            )
        except:
            pass

# Кнопки: рулетка, крутить, правила, домой

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = str(query.from_user.id)
    await query.answer()

    if query.data == "roulette":
        message = await query.message.reply_text(
            "/bet {сумма} {на что}\n\nRed - красный\nBlack - чёрный\nEven - чётное\nOdd - нечётное\n1-18\n19-36\n1-12\n13-24\n25-36\n1st, 2rd, 3nd\n0 - Зелёный\nИли конкретные числа\n\n" + format_bets(user_data[user_id]['bets']) + f"\nБаланс: {user_data[user_id]['balance']}₽",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🎯 Крутить", callback_data="spin")],
                [InlineKeyboardButton("📜 Правила", callback_data="rules")],
                [InlineKeyboardButton("🏠 Домой", callback_data="home")]
            ])
        )
        message_ids[user_id] = message.message_id

    elif query.data == "rules":
        await query.message.reply_text(
            "📜 Правила ставок:\n\n"
            "Red/Black - x2\nEven/Odd - x2\n1-18 / 19-36 - x2\n1-12 / 13-24 / 25-36 - x3\n1st/2rd/3nd - x3\nКонкретное число - x36\n\nВвод: /bet 100 red",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Домой", callback_data="home")]])
        )

    elif query.data == "home":
        await query.message.reply_text(
            "Вы вернулись домой.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🎰 Рулетка", callback_data="roulette")]])
        )

    elif query.data == "spin":
        number = random.randint(0, 36)
        color = "Red" if number in red_numbers else "Black" if number in black_numbers else "Green"
        result_text = f"Выпало: {number} ({color})\n"

        total_win = 0
        for bet_amount, bet_target in user_data[user_id]['bets']:
            win = 0
            if bet_target == color.lower():
                win = bet_amount * 2
            elif bet_target == "even" and number % 2 == 0 and number != 0:
                win = bet_amount * 2
            elif bet_target == "odd" and number % 2 == 1:
                win = bet_amount * 2
            elif bet_target == "1-18" and 1 <= number <= 18:
                win = bet_amount * 2
            elif bet_target == "19-36" and 19 <= number <= 36:
                win = bet_amount * 2
            elif bet_target == "1-12" and 1 <= number <= 12:
                win = bet_amount * 3
            elif bet_target == "13-24" and 13 <= number <= 24:
                win = bet_amount * 3
            elif bet_target == "25-36" and 25 <= number <= 36:
                win = bet_amount * 3
            elif bet_target == "1st" and number in {1,4,7,10,13,16,19,22,25,28,31,34}:
                win = bet_amount * 3
            elif bet_target == "2rd" and number in {2,5,8,11,14,17,20,23,26,29,32,35}:
                win = bet_amount * 3
            elif bet_target == "3nd" and number in {3,6,9,12,15,18,21,24,27,30,33,36}:
                win = bet_amount * 3
            elif bet_target.isdigit() and int(bet_target) == number:
                win = bet_amount * 36

            total_win += win

        user_data[user_id]['balance'] += total_win
        result_text += f"Вы {'выиграли' if total_win else 'проиграли'} {total_win}₽\nБаланс: {user_data[user_id]['balance']}₽"
        user_data[user_id]['bets'].clear()
        save_data()

        await query.message.reply_text(result_text, reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🎰 Рулетка", callback_data="roulette")],
            [InlineKeyboardButton("📜 Правила", callback_data="rules")],
            [InlineKeyboardButton("🏠 Домой", callback_data="home")]
        ]))

# Основной запуск

if __name__ == '__main__':
    load_data()
    print("Бот запущен")

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("bet", bet))
    app.add_handler(CallbackQueryHandler(handle_button))
    app.run_polling()
