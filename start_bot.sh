#!/bin/bash

# Скрипт для быстрого запуска Telegram бота статистики

echo "🤖 Запуск Telegram бота статистики веса и объёмов"
echo "================================================"

# Проверяем наличие токена
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ Ошибка: Не установлена переменная TELEGRAM_BOT_TOKEN"
    echo ""
    echo "Установи токен одним из способов:"
    echo "1. export TELEGRAM_BOT_TOKEN='your_token_here'"
    echo "2. Создай файл .env с содержимым: TELEGRAM_BOT_TOKEN=your_token_here"
    echo ""
    echo "Получить токен можно у @BotFather в Telegram"
    exit 1
fi

# Проверяем наличие Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден. Установи Python 3.8 или новее"
    exit 1
fi

# Проверяем виртуальное окружение
if [ ! -d "venv" ]; then
    echo "📦 Создаём виртуальное окружение..."
    python3 -m venv venv
fi

# Активируем виртуальное окружение
echo "🔧 Активируем виртуальное окружение..."
source venv/bin/activate

# Устанавливаем зависимости
echo "📥 Устанавливаем зависимости..."
pip install -r requirements.txt

# Создаём директорию для данных
if [ ! -d "user_data" ]; then
    mkdir user_data
    echo "📁 Создана директория user_data для хранения данных пользователей"
fi

echo ""
echo "✅ Всё готово! Запускаем бота..."
echo "Для остановки нажми Ctrl+C"
echo ""

# Запускаем бота
python main.py