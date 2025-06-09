# -*- coding: utf-8 -*-

import asyncio
import os
import logging
import sqlite3
import datetime
import random

from telethon import TelegramClient, errors
from telethon.tl.types import Dialog
from typing import Optional, List

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor

# --- ОСНОВНЫЕ НАСТРОЙКИ ---
API_ID = 29921368
API_HASH = '27c77fb9c9d274e6d81fe25766147631'
SESSION_NAME = 'Watermelon'

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- КЛИЕНТ TELEGRAM ---
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

async def sending_loop(entity, interval: int, message: str):
    """
    Бесконечный цикл отправки сообщений в одну конкретную группу.
    Теперь принимает объект entity напрямую, а не его имя.
    """
    # Получаем название группы для логов
    group_title = getattr(entity, 'title', f"ID: {entity.id}")
    logger.info(f"Запущена рассылка для группы '{group_title}' с интервалом {interval} сек.")
    
    while True:
        try:
            await client.send_message(entity, message)
            logger.info(f"Сообщение успешно отправлено в группу '{group_title}'.")
            await asyncio.sleep(interval)
        except errors.FloodWaitError as e:
            logger.warning(f"Слишком много запросов для группы '{group_title}'. Ждем {e.seconds} секунд.")
            await asyncio.sleep(e.seconds)
        except errors.UserIsBlockedError:
            logger.error(f"Бот заблокирован в группе '{group_title}'. Рассылка для этой группы остановлена.")
            break
        except Exception as e:
            logger.error(f"Произошла непредвиденная ошибка для группы '{group_title}': {e}")
            logger.info("Попробую снова через 60 секунд...")
            await asyncio.sleep(60)

async def select_group_from_dialogs() -> Optional[Dialog]:
    """
    Загружает диалоги пользователя, выводит список групп/каналов и
    позволяет выбрать один из них по номеру.
    """
    print("\nЗагружаю список ваших чатов...")
    dialogs = await client.get_dialogs()
    
    # Фильтруем, оставляя только группы и каналы
    groups_and_channels: List[Dialog] = [d for d in dialogs if d.is_group or d.is_channel]
    
    if not groups_and_channels:
        print("Не найдено ни одной группы или канала в вашем аккаунте.")
        return None
        
    print("Выберите группу/канал для рассылки, введя ее номер:")
    for i, dialog in enumerate(groups_and_channels):
        print(f"  {i + 1}. {dialog.title}")
        
    while True:
        try:
            choice_str = input("Введите номер: ")
            choice = int(choice_str) - 1
            if 0 <= choice < len(groups_and_channels):
                return groups_and_channels[choice]
            else:
                print("Неверный номер. Пожалуйста, выберите номер из списка.")
        except ValueError:
            print("Ошибка: введите корректное число.")

def get_multiline_message() -> str:
    """
    Читает многострочное сообщение от пользователя до тех пор,
    пока не будет введено слово 'СТОП' на новой строке.
    """
    print("\nВведите ваше сообщение. Для создания абзаца нажмите Enter.")
    print("Когда закончите, напишите СТОП на новой строке и нажмите Enter.")
    
    lines = []
    while True:
        line = input()
        if line.strip().upper() == 'СТОП':
            break
        lines.append(line)
    
    return "\n".join(lines)

async def main():
    """
    Основная функция: собирает данные от пользователя и запускает рассылку.
    """
    print("--- Автоматическая рассылка сообщений в группы Telegram ---")
    await client.start()
    
    group_configs = []
    
    while True:
        selected_dialog = await select_group_from_dialogs()
        if not selected_dialog:
            break
        
        group_title = selected_dialog.title

        while True:
            try:
                interval_str = input(f"Введите интервал в секундах для группы '{group_title}': ")
                interval = int(interval_str)
                if interval > 0:
                    break
                else:
                    print("Интервал должен быть больше нуля.")
            except ValueError:
                print("Ошибка: введите корректное число для интервала.")
        
        message = get_multiline_message()
        if not message.strip():
            logger.warning("Вы ввели пустое сообщение. Группа будет пропущена.")
        else:
            group_configs.append({"entity": selected_dialog.entity, "interval": interval, "message": message})
            logger.info(f"Группа '{group_title}' добавлена в очередь на рассылку.")

        add_another = input("\nДобавить еще одну группу для рассылки? (y/n): ").strip().lower()
        if add_another != 'y':
            break

    if not group_configs:
        logger.info("Нет групп для рассылки. Завершение работы.")
        return

    print("-" * 30)
    logger.info("Запускаю рассылку...")

    tasks = [
        asyncio.create_task(sending_loop(config['entity'], config['interval'], config['message']))
        for config in group_configs
    ]
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        with client:
            client.loop.run_until_complete(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("\nПрограмма остановлена пользователем.")
    finally:
        logger.info("Отключение от Telegram...")
        
# Удаляем существующую БД, если есть
db_filename = 'quokka_shop.db'
if os.path.exists(db_filename):
    os.remove(db_filename)

API_TOKEN = "7715331660:AAEs_B2tnLbWjHKwu-Vl8u4oQTP53puOooA"
MODERATORS_CHAT_ID = -1002670384649
CARD_NUMBER = "2200 7013 7750-5745"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# --- Database ---
conn = sqlite3.connect(db_filename, check_same_thread=False)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_code TEXT,
    user_id INTEGER,
    product TEXT,
    amount REAL,
    status TEXT,
    timestamp DATETIME,
    payment_name TEXT,
    credentials TEXT,
    subscription_expires DATETIME
)
''')
conn.commit()

class OrderStates(StatesGroup):
    waiting_stars_count = State()
    waiting_payment_name = State()
    waiting_email = State()
    waiting_password = State()
    waiting_account_product = State()
    waiting_account_service = State()
    waiting_account_payname = State()
    waiting_subscription_email = State()

class AdminDeclineStates(StatesGroup):
    waiting_decline_reason = State()

EMOJI_CART = "🛒"
EMOJI_SPOTIFY = "🎵"
EMOJI_NETFLIX = "🎬"
EMOJI_ADOBE = "🎨"
EMOJI_TGPREM = "💎"
EMOJI_CONTACT = "📞"
EMOJI_ACCOUNT = "👤"

PRODUCTS = {
    'spotify': [
        {'name': 'Индивидуальная', 'price': 259, 'pay_url': 'https://pay.cloudtips.ru/p/b676bba2'},
        {'name': 'Дуо', 'price': 379, 'pay_url': 'https://pay.cloudtips.ru/p/674add5a'},
        {'name': 'Семейная', 'price': 479, 'pay_url': 'https://pay.cloudtips.ru/p/00c9504e'}
    ],
    'netflix': [
        {'name': 'Basic', 'price': 499, 'pay_url': 'https://pay.cloudtips.ru/p/6365546b'},
        {'name': 'Standard', 'price': 699, 'pay_url': 'https://pay.cloudtips.ru/p/d62816e5'},
        {'name': 'Premium', 'price': 899, 'pay_url': 'https://pay.cloudtips.ru/p/b4630298'}
    ],
    'adobe': [
        {'name': 'Photoshop', 'price': 2359, 'pay_url': 'https://pay.cloudtips.ru/p/a799827c'},
        {'name': 'After Effects', 'price': 2359, 'pay_url': 'https://pay.cloudtips.ru/p/b4e1fa76'},
        {'name': 'Premiere Pro', 'price': 2359, 'pay_url': 'https://pay.cloudtips.ru/p/4e314e18'}
    ],
    'telegram_premium': [
        {'name': '1 месяц', 'price': 259, 'pay_url': 'https://pay.cloudtips.ru/p/6c5c4ea7'},
        {'name': '1 год', 'price': 1799, 'pay_url': 'https://pay.cloudtips.ru/p/6c5c4ea7'}
    ]
}

TELEGRAM_STARS = {
    'min': 50,
    'price': 1.8,
    'pay_url': 'https://pay.cloudtips.ru/p/b04d736e'
}

STATUS_ICONS = {
    'На проверке': '🟡',
    'Выполняется': '🟠',
    'Выполнен': '🟢',
    'Отклонен': '❌'
}

PRODUCT_DESCRIPTIONS = {
    'spotify': {
        'Индивидуальная': "🎧 Персональный аккаунт с музыкой без рекламы, с возможностью скачивать треки и слушать их в любом порядке с высоким качеством звука.\n\n✨ Если у Вас нету аккаунта данного сервиса, то Вы можете приобрести его, обратившись в поддержку - @quokka_key",
        'Дуо': "🎶 Два отдельных Premium-аккаунта, экономичнее двух индивидуальных подписок.\n\n✨ Если у Вас нету аккаунта данного сервиса, то Вы можете приобрести его, обратившись в поддержку - @quokka_key",
        'Семейная': "🎼 До шести отдельных Premium-аккаунтов, с раздельной персонализацией и рекомендациями для каждого.\n\n✨ Если у Вас нету аккаунта данного сервиса, то Вы можете приобретить его, обратившись в поддержку - @quokka_key"
    },
    'netflix': {
        'Basic': "🎬 Доступ к библиотеке фильмов и сериалов с возможностью просмотра на одном устройстве, часто включает рекламу и контент в стандартном качестве.\n⚠️ VPN необходим для использования сервиса в России, без него доступ невозможен! 🚨\n\n✨ Если у Вас нету аккаунта данного сервиса, то Вы можете приобрести его, обратившись в поддержку - @quokka_key",
        'Standard': "🍿 Просмотр в Full HD качестве на двух устройствах одновременно с возможностью добавления одного дополнительного пользователя и скачивания контента.\n⚠️ VPN необходим для использования сервиса в России, без него доступ невозможен! 🚨\n\n✨ Если у Вас нету аккаунта данного сервиса, то Вы можете приобрести его, обратившись в поддержку - @quokka_key",
        'Premium': "🎥 Просмотр на четырех устройствах одновременно в качестве Ultra HD 4K с возможностью добавления двух дополнительных пользователей и пространственным аудио.\n⚠️ VPN необходим для использования сервиса в России, без него доступ невозможен! 🚨\n\n✨ Если у Вас нету аккаунта данного сервиса, то Вы можете приобрести его, обратившись в поддержку - @quokka_key"
    },
    'adobe': {
        'Photoshop': "📷 Профессиональный инструмент для обработки фотографий, создания иллюстраций, макетов и прототипов для веб-дизайна.\n\n✨ Если у Вас нету аккаунта данного сервиса, то Вы можете приобрести его, обратившись в поддержку - @quokka_key",
        'After Effects': "✨ Продвинутый редактор для создания впечатляющих визуальных эффектов, анимации и графических композиций для фильмов, рекламы и веб-проектов.\n\n✨ Если у Вас нету аккаунта данного сервиса, то Вы можете приобрести его, обратившись в поддержку - @quokka_key",
        'Premiere Pro': "🎞️ Мощная программа для монтажа видео с функциями нарезки и склейки фрагментов, цветокоррекции и профессиональной работы со звуком.\n\n✨ Если у Вас нету аккаунта данного сервиса, то Вы можете приобрести его, обратившись в поддержку - @quokka_key"
    },
    'telegram_premium': {
        '1 месяц': "🌟 Месячная подписка дарит мгновенную приоритетную загрузку файлов и эксклюзивные стикеры. 🚀 Наслаждайтесь молниеносной отправкой сообщений и яркими реакциями в каждом чате!\n\n✨ Если у Вас нетy аккаунта данного сервиса, то Вы можете приобрести его, обратившись в поддержку - @quokka_key",
        '1 год': "✨ Годовая подписка открывает полный набор Premium-функций: эксклюзивные эмодзи, приоритетную загрузку больших файлов и просмотр профилей без рекламы. 🎉 А ещё Вы получаете ранний доступ к новым реакциям, темам оформления и экспериментальным функциям весь год!\n\n✨ Если у Вас нетy аккаунта данного сервиса, то Вы можете приобрести его, обратившись в поддержку - @quokka_key"
    }
}

def is_subscription(product_name: str) -> bool:
    excluded = ["звёзды"]
    for ex in excluded:
        if ex in product_name:
            return False
    keywords = ["Spotify", "Netflix", "Adobe", "Telegram"]
    return any(kw in product_name for kw in keywords)

def generate_order_code(order_id: int) -> str:
    rnd = random.randint(1000, 9999)
    return f"ORD{order_id}_{rnd}"

async def has_orders(user_id: int) -> bool:
    cursor.execute("SELECT EXISTS(SELECT 1 FROM orders WHERE user_id=? LIMIT 1)", (user_id,))
    return bool(cursor.fetchone()[0])

async def main_menu(user_id: int) -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton(f"{EMOJI_SPOTIFY} Spotify", callback_data="category_spotify"),
        types.InlineKeyboardButton(f"{EMOJI_NETFLIX} Netflix", callback_data="category_netflix"),
        types.InlineKeyboardButton(f"{EMOJI_ADOBE} Adobe", callback_data="category_adobe"),
        types.InlineKeyboardButton(f"{EMOJI_TGPREM} Telegram Premium", callback_data="category_telegram_premium")
    )
    if await has_orders(user_id):
        kb.add(types.InlineKeyboardButton("📝 История заказов", callback_data="history"))
    return kb

def back_to_start_kb() -> types.InlineKeyboardMarkup:
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Назад в главное меню", callback_data="start"))
    return kb

@dp.message_handler(commands=['start'])
async def cmd_start(msg: types.Message):
    photo_url = "https://files.oaiusercontent.com/file-7PH4Tcjfap6LcpnVxS99dp?se=2025-05-18T18%3A19%3A52Z&sp=r&sv=2024-08-04&sr=b&rscc=max-age%3D299%2C%20immutable%2C%20private&rscd=attachment%3B%20filename%3Dphoto_2025-05-18_21-14-27.jpg&sig=GOtpSKbWA4QWY7U9EkIvfzqNnW0IKCfexy4Cmeu106Y%3D"
    caption = (
        "👋 Здравствуйте! Рады приветствовать вас в онлайн-магазине \"Ключ Квокки\"!\n\n"
        "С нами Вы сможете:\n"
        "🎵 Наслаждаться любимой музыкой без ограничений\n"
        "🍿 Погрузиться в захватывающие миры сериалов и фильмов\n"
        "✨ Открыть все скрытые возможности мессенджеров\n"
        "🎨 Творить без границ с профессиональными инструментами\n\n"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("Выбрать подписку 💎", callback_data="choose"),
        types.InlineKeyboardButton("Новостной канал 📡", url="https://t.me/key_quokka"),
        types.InlineKeyboardButton("Поддержка ☎️", url="https://t.me/quokka_key")
        
    )
    await bot.send_photo(msg.chat.id, photo=photo_url, caption=caption, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == "start")
async def callback_start(cb: types.CallbackQuery):
    await cb.message.delete()
    main_menu_text = "Пожалуйста, выберите интересующую Вас категорию товаров:"
    kb = await main_menu(cb.from_user.id)
    await cb.message.answer(main_menu_text, reply_markup=kb)
    await cb.answer()

@dp.callback_query_handler(lambda c: c.data == "choose")
async def choose_subscription(cb: types.CallbackQuery):
    await cb.message.delete()
    main_menu_text = "Пожалуйста, выберите интересующую Вас категорию товаров:"
    main_menu_kb = await main_menu(cb.from_user.id)
    await cb.message.answer(main_menu_text, reply_markup=main_menu_kb)
    await cb.answer()

@dp.callback_query_handler(lambda c: c.data == 'history')
async def process_history(cb: types.CallbackQuery):
    uid = cb.from_user.id
    cursor.execute(
        "SELECT id, order_code, product, amount, status, timestamp FROM orders WHERE user_id=? ORDER BY timestamp DESC LIMIT 10",
        (uid,)
    )
    rows = cursor.fetchall()
    if not rows:
        await cb.message.answer("У вас ещё нет заказов.", reply_markup=back_to_start_kb())
    else:
        kb = types.InlineKeyboardMarkup(row_width=1)
        for oid, order_code, prod, amt, st, ts in rows:
            icon = STATUS_ICONS.get(st, '')
            btn_text = f"#{oid} ({order_code}) {icon} {prod}"
            kb.add(types.InlineKeyboardButton(btn_text, callback_data=f"order_{oid}"))
        kb.add(types.InlineKeyboardButton("🔙 Назад в главное меню", callback_data="start"))
        await cb.message.answer("📝 История заказов:", reply_markup=kb)
    await cb.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('order_'))
async def order_details(cb: types.CallbackQuery):
    oid = int(cb.data.split('_')[1])
    cursor.execute(
        "SELECT order_code, product, payment_name, status, timestamp, subscription_expires FROM orders WHERE id=?",
        (oid,)
    )
    order = cursor.fetchone()
    if order:
        order_code, prod, pay_name, status, ts, sub_expires = order
        icon = STATUS_ICONS.get(status, '')
        details = f"📦 Заказ #{oid} ({order_code})\n"
        details += f"Товар: {prod}\n"
        details += f"Описание (имя из оплаты): {pay_name}\n"
        details += f"Статус: {status} {icon}\n"
        details += f"Дата создания: {ts.split('.')[0]}\n\n"
        if sub_expires:
            details += f"Подписка активна до: {sub_expires}\n"
            details += "Вы всегда можете продлить подписку после её окончания.\n"
        details += "\nСвязаться с поддержкой - @quokka_key"
        kb = types.InlineKeyboardMarkup(row_width=2)
        if sub_expires:
            kb.add(types.InlineKeyboardButton("Продлить подписку 😊", callback_data=f"renew_{oid}"))
        kb.add(types.InlineKeyboardButton("🔙 Назад в главное меню", callback_data="start"))
        await cb.message.edit_text(details, parse_mode="HTML", reply_markup=kb)
    else:
        await cb.message.answer("Заказ не найден.", reply_markup=back_to_start_kb())
    await cb.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('category_'))
async def process_category(cb: types.CallbackQuery):
    cat = cb.data.split('_', 1)[1]
    await cb.message.delete()
    if cat in PRODUCTS:
        if cat == "telegram_premium":
            kb = types.InlineKeyboardMarkup(row_width=1)
            kb.add(
                types.InlineKeyboardButton(f"{EMOJI_CART} Telegram Premium 1 месяц – 259₽", callback_data="product_telegram_premium_0"),
                types.InlineKeyboardButton(f"{EMOJI_CART} Telegram Premium 1 год – 1799₽", callback_data="product_telegram_premium_1"),
            )
            kb.add(types.InlineKeyboardButton("🔙 Назад в главное меню", callback_data="start"))
            await cb.message.answer("Выберите тариф:", reply_markup=kb)
        elif cat in ("spotify", "netflix", "adobe"):
            kb = types.InlineKeyboardMarkup(row_width=1)
            for i, p in enumerate(PRODUCTS[cat]):
                kb.add(types.InlineKeyboardButton(
                    f"{EMOJI_CART} {cat.capitalize()} {p['name']} – {p['price']}₽",
                    callback_data=f"product_{cat}_{i}"
                ))
            kb.add(types.InlineKeyboardButton("🔙 Назад в главное меню", callback_data="start"))
            await cb.message.answer("Выберите тариф:", reply_markup=kb)
    await cb.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('product_'))
async def process_product(cb: types.CallbackQuery):
    data_wo_prefix = cb.data[len('product_'):]
    try:
        cat, idx = data_wo_prefix.rsplit('_', 1)
        p = PRODUCTS[cat][int(idx)]
    except Exception:
        await cb.message.answer("Ошибка: Неверная callback_data.", reply_markup=back_to_start_kb())
        return
    prod_name = p['name']
    if cat == 'telegram_premium':
        title = f"🛒 Telegram Premium {prod_name}"
        price_str = f"💰 {p['price']}₽"
        description = PRODUCT_DESCRIPTIONS.get(cat, {}).get(prod_name, "")
    else:
        title = f"🛒 {cat.capitalize()} {prod_name}"
        price_str = f"💰 {p['price']}₽"
        description = PRODUCT_DESCRIPTIONS.get(cat, {}).get(prod_name, "")
    text = (
        f"{title}\n\n"
        f"{description}\n\n"
        f"{price_str}"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("Перейти к оплате 💳", callback_data=f"proceed_{cat}_{idx}"),
        types.InlineKeyboardButton("🔙 Назад в главное меню", callback_data="start")
    )
    await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('proceed_'))
async def process_proceed(cb: types.CallbackQuery):
    data_wo_prefix = cb.data[len('proceed_'):]
    try:
        cat, idx = data_wo_prefix.rsplit('_', 1)
        p = PRODUCTS[cat][int(idx)]
    except Exception:
        await cb.message.answer("Ошибка: Неверная callback_data.", reply_markup=back_to_start_kb())
        return
    if cat == "telegram_premium":
        prod_name = p['name']
        text = (
            f"🛒 Telegram Premium {prod_name}\n"
            f"💵 Стоимость: {p['price']}₽\n\n"
            "💫 Инструкция по оплате 💫\n"
            "1️⃣ Нажмите «Оплатить 💳» и перейдите на страницу платежа.\n"
            "2️⃣ В поле «Комментарий*» укажите ваш @nickname — мы не храним данные после оплаты 🛡️ \n"
            "3️⃣ Завершите оплату 💸.\n"
            "4️⃣ Вернитесь в бота «Ключ Квокки» и нажмите «Я оплатил ✅» \n"
            "5️⃣ Отправьте модератору номер заказа и следуйте его инструкциям.\n\n"
            "🎉 Готово! Ваш заказ принят и скоро будет выполнен! "
        )
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("Оплатить 💳", url=p['pay_url']),
            types.InlineKeyboardButton("Я оплатил ✅", callback_data=f"paid_telegram_premium_{idx}"),
            types.InlineKeyboardButton("🔙 Назад в главное меню", callback_data="start")
        )
        await cb.message.edit_text(text, reply_markup=kb)
    else:
        text = (
            f"🛒 {cat.capitalize()} {p['name']}\n"
            f"💵 Стоимость: {p['price']}₽\n\n"
            "💫 Инструкция по оплате 💫\n"
            "Как оплатить подписку:\n"
            "1️⃣ Нажмите кнопку \"Оплатить 💳\" и перейдите на страницу оплаты\n\n"
            "2️⃣ На странице оплаты укажите:\n"
            " В поле \"Комментарий*\" - вашу почту для входа в аккаунт 📧\n"
            " В поле \"Обратная связь\" - пароль от аккаунта 🔐\n"
            " Мы не храним ваши данные после оплаты! Безопасность гарантирована 🛡️\n\n"
            "3️⃣ Завершите оплату 💸\n\n"
            "4️⃣ Вернитесь в телеграм-бот \"Ключ Квокки\" и нажмите кнопку \"Я оплатил ✅\"\n\n"
            "5️⃣ Введите ещё раз вашу почту для входа в аккаунт 📨\n\n"
            "🎉 Готово! Ваш заказ принят и скоро будет выполнен! 🎉"
        )
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton("Оплатить 💳", url=p['pay_url']),
            types.InlineKeyboardButton("✅ Я оплатил", callback_data=f"paid_{cat}_{idx}"),
            types.InlineKeyboardButton("🔙 Назад в главное меню", callback_data="start")
        )
        await cb.message.edit_text(text, reply_markup=kb)
    await cb.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('paid_telegram_premium_'))
async def process_paid_telegram_premium(cb: types.CallbackQuery):
    data_wo_prefix = cb.data[len('paid_telegram_premium_'):]
    idx = data_wo_prefix
    cat = 'telegram_premium'
    try:
        p = PRODUCTS[cat][int(idx)]
    except Exception:
        await cb.message.answer("Ошибка: Неверная callback_data.", reply_markup=back_to_start_kb())
        return
    user = cb.from_user
    order_timestamp = datetime.datetime.now()
    days = 30 if idx == "0" else 365
    sub_expires = (order_timestamp + datetime.timedelta(days=days)).strftime('%d.%m.%Y %H:%M:%S')
    prod_name = f"Telegram Premium {p['name']}"
    amt = p['price']
    payment_name = f"@{user.username}" if user.username else f"id{user.id}"
    cursor.execute(
        "INSERT INTO orders(user_id, product, amount, status, timestamp, payment_name, subscription_expires) "
        "VALUES(?,?,?,?,?,?,?)",
        (user.id, prod_name, amt, 'На проверке', order_timestamp, payment_name, sub_expires)
    )
    conn.commit()
    oid = cursor.lastrowid
    order_code = generate_order_code(oid)
    cursor.execute("UPDATE orders SET order_code=? WHERE id=?", (order_code, oid))
    conn.commit()
    await cb.message.answer(
        f"✅ Ваш заказ #{oid} ({order_code}) создан и ожидает обработки модератором. \n"
        f"Для связи с модератором перейдите в чат: https://t.me/quokka_key\n"
        f"Пожалуйста, следуйте инструкциям модератора 📋✨🔑",
        reply_markup=back_to_start_kb()
    )
    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Выполнено", callback_data=f"admin_done_{oid}"),
        types.InlineKeyboardButton("❌ Ваш заказ отклонен", callback_data=f"admin_decline_{oid}")
    )
    moderator_text = (
        f"📦 Новый заказ #{oid} ({order_code})\n"
        f"Пользователь: {user.full_name} (@{user.username})\n"
        f"Товар: Telegram Premium {p['name']}\nСумма: {amt}₽\n"
        f"@nickname: @{user.username if user.username else user.id}\n"
        f"Подписка активна до: {sub_expires}"
    )
    await bot.send_message(MODERATORS_CHAT_ID, moderator_text, reply_markup=kb)
    await cb.answer()

@dp.callback_query_handler(lambda c: c.data.startswith('paid_') and not c.data.startswith('paid_telegram_premium_'))
async def process_paid_subscription(cb: types.CallbackQuery, state: FSMContext):
    try:
        data_wo_prefix = cb.data[len('paid_'):]
        cat, idx = data_wo_prefix.rsplit('_', 1)
        if cat not in ['spotify', 'netflix', 'adobe']:
            raise ValueError
        p = PRODUCTS[cat][int(idx)]
    except Exception:
        await cb.message.answer("Ошибка: Неверная callback_data.", reply_markup=back_to_start_kb())
        return

    await cb.message.answer(
        "Пожалуйста, введите вашу почту, которую вы указывали при оплате 📧\n"
        "Пока вы не введёте почту, заказ не будет обработан модератором 😊"
    )
    await state.update_data(category=cat, idx=idx, product_name=p['name'], price=p['price'])
    await OrderStates.waiting_subscription_email.set()
    await cb.answer()

@dp.message_handler(state=OrderStates.waiting_subscription_email)
async def process_subscription_email(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    user = msg.from_user
    order_timestamp = datetime.datetime.now()
    product_name = f"{data['category'].capitalize()} {data['product_name']}"
    payment_name = f"@{user.username}" if user.username else f"id{user.id}"
    credentials = msg.text

    cursor.execute(
        "INSERT INTO orders(user_id, product, amount, status, timestamp, payment_name, credentials) "
        "VALUES(?,?,?,?,?,?,?)",
        (user.id, product_name, data['price'], 'На проверке', order_timestamp, payment_name, credentials)
    )
    conn.commit()
    oid = cursor.lastrowid
    order_code = generate_order_code(oid)
    cursor.execute("UPDATE orders SET order_code=? WHERE id=?", (order_code, oid))
    conn.commit()

    await msg.answer(
        f"✅ Ваш заказ #{oid} ({order_code}) создан и ожидает обработки модератором.\n"
        f"Для связи с модератором перейдите в чат: https://t.me/quokka_key\n"
        f"Пожалуйста, следуйте инструкциям модератора 📋✨🔑",
        reply_markup=back_to_start_kb()
    )

    kb = types.InlineKeyboardMarkup()
    kb.add(
        types.InlineKeyboardButton("✅ Выполнено", callback_data=f"admin_done_{oid}"),
        types.InlineKeyboardButton("❌ Ваш заказ отклонен", callback_data=f"admin_decline_{oid}")
    )
    moderator_text = (
        f"📦 Новый заказ #{oid} ({order_code})\n"
        f"Пользователь: {user.full_name} (@{user.username})\n"
        f"Товар: {product_name}\nСумма: {data['price']}₽\n"
        f"Почта: {credentials}\n"
        f"@nickname: @{user.username if user.username else user.id}"
    )
    await bot.send_message(MODERATORS_CHAT_ID, moderator_text, reply_markup=kb)
    await state.finish()
    
@dp.callback_query_handler(lambda c: c.data.startswith('admin_done_'))
async def admin_done(cb: types.CallbackQuery):
    oid = int(cb.data[len('admin_done_'):])
    cursor.execute("UPDATE orders SET status='Выполнен' WHERE id=?", (oid,))
    conn.commit()
    await cb.answer("✅ Заказ выполнен!")
    await cb.message.edit_text(
        f"{cb.message.text}\n\nСтатус обновлён на: ✅ Выполнен",
        reply_markup=None
    )
    # Получаем user_id заказа
    cursor.execute("SELECT user_id FROM orders WHERE id=?", (oid,))
    user_id = cursor.fetchone()[0]
    # Уведомляем пользователя
    await bot.send_message(
        user_id,
        "Ваш заказ успешно выполнен! 🎉 Спасибо за покупку! Если возникнут вопросы — пишите в поддержку @quokka_key"
    )

@dp.callback_query_handler(lambda c: c.data.startswith('admin_decline_'))
async def admin_decline(cb: types.CallbackQuery, state: FSMContext):
    oid = int(cb.data[len('admin_decline_'):])
    await state.update_data(oid=oid)
    await AdminDeclineStates.waiting_decline_reason.set()
    await cb.message.answer("Пожалуйста, укажите причину отказа для пользователя:")
    await cb.answer()

@dp.message_handler(state=AdminDeclineStates.waiting_decline_reason)
async def process_decline_reason(msg: types.Message, state: FSMContext):
    data = await state.get_data()
    oid = data['oid']
    reason = msg.text
    cursor.execute("UPDATE orders SET status='Отклонен' WHERE id=?", (oid,))
    conn.commit()
    # Получаем user_id заказа
    cursor.execute("SELECT user_id FROM orders WHERE id=?", (oid,))
    user_id = cursor.fetchone()[0]
    # Уведомляем пользователя
    await bot.send_message(
        user_id,
        f"К сожалению, ваш заказ был отклонён. Причина: {reason}\n\nЕсли есть вопросы — пишите в поддержку @quokka_key"
    )
    await msg.answer("Причина отказа отправлена пользователю.", reply_markup=back_to_start_kb())
    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
