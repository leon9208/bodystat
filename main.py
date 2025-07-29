#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Телеграм бот для отслеживания статистики веса и объёмов тела
Все данные хранятся локально в JSON файлах для каждого пользователя
"""

import os
import json
import logging
from flask import Flask
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from keep_alive import keep_alive

keep_alive()

# Загружаем переменные окружения из .env файла
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Директория для хранения данных пользователей
DATA_DIR = "user_data"

# Импортируем настройки авторизации из конфигурационного файла
try:
    from config import (
        OPEN_ACCESS, ALLOWED_USER_IDS, ALLOWED_USERNAMES, 
        ADMIN_ONLY_MODE, ADMIN_USER_ID, UNAUTHORIZED_MESSAGE,
        LOG_UNAUTHORIZED_ATTEMPTS
    )
except ImportError:
    # Настройки по умолчанию, если config.py не найден
    OPEN_ACCESS = True
    ALLOWED_USER_IDS = []
    ALLOWED_USERNAMES = []
    ADMIN_ONLY_MODE = False
    ADMIN_USER_ID = None
    UNAUTHORIZED_MESSAGE = """
🚫 **Доступ запрещён**

У тебя нет доступа к этому боту.
Обратись к администратору для получения доступа.

👤 Твой ID: {user_id}
📝 Username: @{username}
    """
    LOG_UNAUTHORIZED_ATTEMPTS = True

class UserStatsManager:
    """Класс для управления статистикой пользователей"""
    
    def __init__(self):
        # Создаём директорию для данных, если её нет
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
    
    def get_user_file_path(self, user_id: int) -> str:
        """Получить путь к файлу данных пользователя"""
        return os.path.join(DATA_DIR, f"user_{user_id}.json")
    
    def load_user_data(self, user_id: int) -> Dict:
        """Загрузить данные пользователя из файла"""
        file_path = self.get_user_file_path(user_id)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Ошибка загрузки данных пользователя {user_id}: {e}")
                return {"records": []}
        return {"records": []}
    
    def save_user_data(self, user_id: int, data: Dict) -> bool:
        """Сохранить данные пользователя в файл"""
        file_path = self.get_user_file_path(user_id)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            logger.error(f"Ошибка сохранения данных пользователя {user_id}: {e}")
            return False
    
    def add_record(self, user_id: int, weight: float, waist: float, hips: float, chest: float) -> bool:
        """Добавить новую запись измерений"""
        data = self.load_user_data(user_id)
        
        # Создаём новую запись с текущей датой
        new_record = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "weight": weight,
            "waist": waist,
            "hips": hips,
            "chest": chest
        }
        
        data["records"].append(new_record)
        return self.save_user_data(user_id, data)
    
    def get_latest_record(self, user_id: int) -> Optional[Dict]:
        """Получить последнюю запись пользователя"""
        data = self.load_user_data(user_id)
        if data["records"]:
            return data["records"][-1]
        return None
    
    def get_previous_record(self, user_id: int) -> Optional[Dict]:
        """Получить предпоследнюю запись для сравнения"""
        data = self.load_user_data(user_id)
        if len(data["records"]) >= 2:
            return data["records"][-2]
        return None
    
    def get_records_by_period(self, user_id: int, days: int) -> List[Dict]:
        """Получить записи за определённый период"""
        data = self.load_user_data(user_id)
        if not data["records"]:
            return []
        
        # Вычисляем дату начала периода
        start_date = datetime.now() - timedelta(days=days)
        filtered_records = []
        
        for record in data["records"]:
            record_date = datetime.strptime(record["date"], "%Y-%m-%d %H:%M:%S")
            if record_date >= start_date:
                filtered_records.append(record)
        
        return filtered_records

# Создаём экземпляр менеджера статистики
stats_manager = UserStatsManager()

# Словарь для отслеживания состояния ввода данных пользователями
user_input_state = {}

def is_user_authorized(user_id: int, username: str = None) -> bool:
    """Проверить, авторизован ли пользователь для использования бота"""
    global ADMIN_USER_ID
    
    # Если открытый доступ - разрешаем всем
    if OPEN_ACCESS:
        return True
    
    # Режим "только админ"
    if ADMIN_ONLY_MODE:
        if ADMIN_USER_ID is None:
            # Первый пользователь становится админом
            ADMIN_USER_ID = user_id
            logger.info(f"Установлен админ бота: {user_id}")
            return True
        return user_id == ADMIN_USER_ID
    
    # Проверяем по ID пользователя
    if user_id in ALLOWED_USER_IDS:
        return True
    
    # Проверяем по username
    if username and username.lower() in [u.lower() for u in ALLOWED_USERNAMES]:
        return True
    
    return False

def authorization_required(func):
    """Декоратор для проверки авторизации пользователя"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        user_id = user.id
        username = user.username
        
        if not is_user_authorized(user_id, username):
            # Отправляем сообщение о запрете доступа
            unauthorized_text = UNAUTHORIZED_MESSAGE.format(
                user_id=user_id,
                username=username if username else 'не указан',
                first_name=user.first_name
            )
            await update.message.reply_text(unauthorized_text)
            
            # Логируем попытку несанкционированного доступа, если включено
            if LOG_UNAUTHORIZED_ATTEMPTS:
                logger.warning(f"Несанкционированный доступ: {user_id} (@{username}) - {user.first_name}")
            return
        
        # Если авторизован - выполняем функцию
        return await func(update, context, *args, **kwargs)
    
    return wrapper

async def get_my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда для получения своего Telegram ID"""
    user = update.effective_user
    id_text = f"""
🆔 **Твоя информация:**

👤 Имя: {user.first_name}
🆔 ID: `{user.id}`
📝 Username: @{user.username if user.username else 'не указан'}
🔗 Ссылка: [tg://user?id={user.id}](tg://user?id={user.id})

Скопируй свой ID и отправь администратору бота для получения доступа.
    """
    await update.message.reply_text(id_text)

def get_main_keyboard():
    """Создать основную клавиатуру бота"""
    keyboard = [
        [KeyboardButton("📊 Добавить измерения")],
        [KeyboardButton("📈 Показать прогресс"), KeyboardButton("📅 История за период")],
        [KeyboardButton("ℹ️ Помощь")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

@authorization_required
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_text = f"""
Привет, {user.first_name}! 👋

Я бот для отслеживания твоей статистики веса и объёмов тела.

Что я умею:
📊 Сохранять твои измерения (вес, объёмы)
📈 Показывать прогресс и изменения
📅 Отображать историю за разные периоды
💾 Все данные хранятся локально и безопасно

Используй кнопки меню для навигации!
    """
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard()
    )

@authorization_required
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды помощи"""
    help_text = """
🔧 Как пользоваться ботом:

📊 Добавить измерения:
   • Нажми кнопку "Добавить измерения"
   • Введи данные в формате: вес талия бёдра грудь
   • Пример: 70.5 80 95 90

📈 Показать прогресс:
   • Сравнение с предыдущими измерениями
   • Показывает изменения по всем параметрам

📅 История за период:
   • Выбери период: неделя, месяц, 3 месяца
   • Посмотри динамику изменений

💡 Советы:
   • Измеряйся в одно время дня
   • Веди записи регулярно для точной статистики
   • Все данные хранятся только у тебя
    """
    
    await update.message.reply_text(help_text)

@authorization_required
async def add_measurements(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Начать процесс добавления измерений"""
    user_id = update.effective_user.id
    user_input_state[user_id] = "waiting_for_measurements"
    
    instruction_text = """
📊 Добавление новых измерений

Введи свои данные в одной строке через пробел:
**вес талия бёдра грудь**

Пример: `70.5 80 95 90`

Где:
• Вес в кг (например: 70.5)
• Талия в см (например: 80)
• Бёдра в см (например: 95)
• Грудь в см (например: 90)
    """
    
    await update.message.reply_text(instruction_text)

@authorization_required
async def show_progress(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать прогресс пользователя"""
    user_id = update.effective_user.id
    
    # Получаем последнюю и предыдущую записи
    latest = stats_manager.get_latest_record(user_id)
    previous = stats_manager.get_previous_record(user_id)
    
    if not latest:
        await update.message.reply_text(
            "📊 У тебя пока нет записей измерений.\n"
            "Нажми 'Добавить измерения' чтобы начать!"
        )
        return
    
    # Форматируем текущие данные
    current_text = f"""
📊 **Текущие показатели:**
📅 Дата: {latest['date'][:10]}
⚖️ Вес: {latest['weight']} кг
📐 Талия: {latest['waist']} см
🍑 Бёдра: {latest['hips']} см
📏 Грудь: {latest['chest']} см
    """
    
    # Если есть предыдущая запись, показываем изменения
    if previous:
        changes_text = "\n📈 **Изменения с прошлого раза:**\n"
        
        # Вычисляем разности
        weight_diff = latest['weight'] - previous['weight']
        waist_diff = latest['waist'] - previous['waist']
        hips_diff = latest['hips'] - previous['hips']
        chest_diff = latest['chest'] - previous['chest']
        
        # Функция для форматирования изменений
        def format_change(value: float, unit: str) -> str:
            if value > 0:
                return f"+{value:.1f} {unit} 📈"
            elif value < 0:
                return f"{value:.1f} {unit} 📉"
            else:
                return f"без изменений ➡️"
        
        changes_text += f"⚖️ Вес: {format_change(weight_diff, 'кг')}\n"
        changes_text += f"📐 Талия: {format_change(waist_diff, 'см')}\n"
        changes_text += f"🍑 Бёдра: {format_change(hips_diff, 'см')}\n"
        changes_text += f"📏 Грудь: {format_change(chest_diff, 'см')}\n"
        
        current_text += changes_text
    
    await update.message.reply_text(current_text)

@authorization_required
async def show_history_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показать меню выбора периода для истории"""
    keyboard = [
        [KeyboardButton("📅 За неделю"), KeyboardButton("📅 За месяц")],
        [KeyboardButton("📅 За 3 месяца"), KeyboardButton("📅 За всё время")],
        [KeyboardButton("🔙 Назад")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "📅 Выбери период для просмотра истории:",
        reply_markup=reply_markup
    )

@authorization_required
async def show_history_period(update: Update, context: ContextTypes.DEFAULT_TYPE, days: int) -> None:
    """Показать историю за определённый период"""
    user_id = update.effective_user.id
    
    if days == -1:  # За всё время
        data = stats_manager.load_user_data(user_id)
        records = data["records"]
        period_name = "всё время"
    else:
        records = stats_manager.get_records_by_period(user_id, days)
        period_name = f"{days} дней"
    
    if not records:
        await update.message.reply_text(
            f"📅 За {period_name} записей не найдено.",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Формируем текст истории
    history_text = f"📅 **История за {period_name}:**\n\n"
    
    # Если записей много, показываем только последние 10
    display_records = records[-10:] if len(records) > 10 else records
    
    for i, record in enumerate(display_records, 1):
        date_str = record['date'][:10]  # Только дата без времени
        history_text += f"**{i}. {date_str}**\n"
        history_text += f"⚖️ {record['weight']}кг | 📐 {record['waist']}см | "
        history_text += f"🍑 {record['hips']}см | 📏 {record['chest']}см\n\n"
    
    # Показываем общую статистику за период
    if len(records) >= 2:
        first_record = records[0]
        last_record = records[-1]
        
        weight_total_change = last_record['weight'] - first_record['weight']
        waist_total_change = last_record['waist'] - first_record['waist']
        hips_total_change = last_record['hips'] - first_record['hips']
        chest_total_change = last_record['chest'] - first_record['chest']
        
        history_text += f"� **Общие иaзменения за период:**\n"
        history_text += f"⚖️ Вес: {weight_total_change:+.1f} кг\n"
        history_text += f"📐 Талия: {waist_total_change:+.1f} см\n"
        history_text += f"🍑 Бёдра: {hips_total_change:+.1f} см\n"
        history_text += f"📏 Грудь: {chest_total_change:+.1f} см\n"
    
    if len(records) > 10:
        history_text += f"\n📝 Показано последние 10 из {len(records)} записей"
    
    await update.message.reply_text(history_text, reply_markup=get_main_keyboard())

async def process_measurements_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработать ввод измерений пользователем"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    try:
        # Парсим введённые данные
        values = text.split()
        if len(values) != 4:
            raise ValueError("Неверное количество параметров")
        
        weight, waist, hips, chest = map(float, values)
        
        # Проверяем разумность значений
        if not (30 <= weight <= 300):
            raise ValueError("Вес должен быть от 30 до 300 кг")
        if not (40 <= waist <= 200):
            raise ValueError("Объём талии должен быть от 40 до 200 см")
        if not (50 <= hips <= 200):
            raise ValueError("Объём бёдер должен быть от 50 до 200 см")
        if not (50 <= chest <= 200):
            raise ValueError("Объём груди должен быть от 50 до 200 см")
        
        # Сохраняем данные
        if stats_manager.add_record(user_id, weight, waist, hips, chest):
            # Получаем предыдущую запись для сравнения
            previous = stats_manager.get_previous_record(user_id)
            
            success_text = f"""
✅ **Измерения успешно сохранены!**

📊 Твои новые показатели:
⚖️ Вес: {weight} кг
📐 Талия: {waist} см
🍑 Бёдра: {hips} см
📏 Грудь: {chest} см
            """
            
            # Если есть предыдущая запись, показываем изменения
            if previous:
                weight_diff = weight - previous['weight']
                waist_diff = waist - previous['waist']
                
                success_text += f"\n📈 **Изменения:**\n"
                success_text += f"⚖️ Вес: {weight_diff:+.1f} кг\n"
                success_text += f"📐 Талия: {waist_diff:+.1f} см"
            
            await update.message.reply_text(success_text, reply_markup=get_main_keyboard())
        else:
            await update.message.reply_text(
                "❌ Ошибка при сохранении данных. Попробуй ещё раз.",
                reply_markup=get_main_keyboard()
            )
    
    except ValueError as e:
        error_text = f"""
❌ **Ошибка ввода данных:**
{str(e)}

Пожалуйста, введи данные в правильном формате:
**вес талия бёдра грудь**

Пример: `70.5 80 95 90`
        """
        await update.message.reply_text(error_text)
    
    # Сбрасываем состояние ввода
    if user_id in user_input_state:
        del user_input_state[user_id]

@authorization_required
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Основной обработчик сообщений"""
    user_id = update.effective_user.id
    text = update.message.text
    
    # Проверяем, ожидаем ли мы ввод измерений от пользователя
    if user_id in user_input_state and user_input_state[user_id] == "waiting_for_measurements":
        await process_measurements_input(update, context)
        return
    
    # Обрабатываем команды с кнопок
    if text == "📊 Добавить измерения":
        await add_measurements(update, context)
    elif text == "📈 Показать прогресс":
        await show_progress(update, context)
    elif text == "📅 История за период":
        await show_history_menu(update, context)
    elif text == "📅 За неделю":
        await show_history_period(update, context, 7)
    elif text == "📅 За месяц":
        await show_history_period(update, context, 30)
    elif text == "📅 За 3 месяца":
        await show_history_period(update, context, 90)
    elif text == "📅 За всё время":
        await show_history_period(update, context, -1)
    elif text == "ℹ️ Помощь":
        await help_command(update, context)
    elif text == "🔙 Назад":
        await update.message.reply_text(
            "Главное меню:",
            reply_markup=get_main_keyboard()
        )
    else:
        # Неизвестная команда
        await update.message.reply_text(
            "🤔 Не понимаю эту команду. Используй кнопки меню или /help для справки.",
            reply_markup=get_main_keyboard()
        )

def main():
    """Основная функция запуска бота"""
    # Получаем токен бота из переменной окружения
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not bot_token:
        print("❌ Ошибка: Не найден токен бота!")
        print("Установи переменную окружения TELEGRAM_BOT_TOKEN")
        print("Пример: export TELEGRAM_BOT_TOKEN='your_bot_token_here'")
        return
    
    # Создаём приложение
    application = Application.builder().token(bot_token).build()
    
    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("id", get_my_id))  # Команда для получения ID
    
    # Регистрируем обработчик всех текстовых сообщений
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    print("🤖 Бот запущен и готов к работе!")
    print("Нажми Ctrl+C для остановки")
    
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        print("\n👋 Бот остановлен")

if __name__ == '__main__':
    main()