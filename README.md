# 📊 Телеграм Бот - Статистика Веса и Объёмов

Бот для отслеживания личной статистики веса и объёмов тела с локальным хранением данных.

## 🚀 Возможности

- **📊 Добавление измерений**: Сохранение веса, роста и объёмов (талия, бёдра, грудь)
- **📈 Отслеживание прогресса**: Сравнение с предыдущими измерениями
- **📅 История по периодам**: Просмотр изменений за неделю, месяц, 3 месяца или всё время
- **💾 Локальное хранение**: Все данные хранятся в JSON файлах на сервере
- **🔒 Приватность**: Данные каждого пользователя изолированы
- **👥 Контроль доступа**: Гибкая система авторизации пользователей

## 📋 Требования

- Python 3.8+
- Токен Telegram бота

## 🛠 Установка и настройка

### Шаг 1: Создание бота в Telegram

1. Найди [@BotFather](https://t.me/BotFather) в Telegram
2. Отправь команду `/newbot`
3. Следуй инструкциям:
   - Введи имя бота (например: "My Stats Bot")
   - Введи username бота (должен заканчиваться на "bot", например: "my_stats_bot")
4. Сохрани полученный **токен** - он понадобится для запуска

### Шаг 2: Подготовка окружения

```bash
# Клонируй или скачай файлы проекта
# Перейди в директорию проекта
cd telegram-stats-bot

# Создай виртуальное окружение (рекомендуется)
python3 -m venv venv

# Активируй виртуальное окружение
# На macOS/Linux:
source venv/bin/activate
# На Windows:
# venv\Scripts\activate

# Установи зависимости
pip install -r requirements.txt
```

### Шаг 3: Настройка токена

Есть несколько способов установить токен:

#### Способ 1: Переменная окружения (рекомендуется)
```bash
# На macOS/Linux:
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN_HERE"

# На Windows:
set TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
```

#### Способ 2: Создать файл .env
```bash
# Создай файл .env в корне проекта
echo "TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE" > .env
```

### Шаг 4: Настройка авторизации (опционально)

По умолчанию бот доступен всем пользователям. Чтобы ограничить доступ:

1. **Отредактируй файл `config.py`**
2. **Установи `OPEN_ACCESS = False`**
3. **Выбери один из вариантов:**

```python
# Вариант 1: По ID пользователей (рекомендуется)
ALLOWED_USER_IDS = [123456789, 987654321]

# Вариант 2: Только админ (первый пользователь)
ADMIN_ONLY_MODE = True

# Вариант 3: По username
ALLOWED_USERNAMES = ["your_username", "friend_username"]
```

**📋 Подробная инструкция:** [AUTHORIZATION.md](AUTHORIZATION.md)

**🆔 Узнать свой ID:** отправь боту команду `/id`

### Шаг 5: Запуск бота

```bash
# Запуск бота
python main.py
```

Если всё настроено правильно, увидишь сообщение:
```
🤖 Бот запущен и готов к работе!
Нажми Ctrl+C для остановки
```

## 📱 Использование бота

### Команды и кнопки:

1. **📊 Добавить измерения**
   - Введи данные в формате: `вес рост талия бёдра грудь`
   - Пример: `70.5 175 80 95 90`

2. **📈 Показать прогресс**
   - Показывает текущие показатели
   - Сравнивает с предыдущими измерениями

3. **📅 История за период**
   - За неделю, месяц, 3 месяца или всё время
   - Показывает динамику изменений

### Пример использования:

```
Пользователь: нажимает "📊 Добавить измерения"
Бот: Введи данные в формате: вес рост талия бёдра грудь

Пользователь: 72.3 175 82 96 91
Бот: ✅ Измерения сохранены!
     📈 Изменения: ⚖️ Вес: +0.8 кг, 📐 Талия: +2.0 см
```

## 📁 Структура данных

Данные хранятся в директории `user_data/`:
```
user_data/
├── user_123456789.json  # Данные пользователя с ID 123456789
├── user_987654321.json  # Данные другого пользователя
└── ...
```

Формат файла пользователя:
```json
{
  "records": [
    {
      "date": "2025-01-15 14:30:00",
      "weight": 70.5,
      "height": 175,
      "waist": 80,
      "hips": 95,
      "chest": 90
    }
  ]
}
```

## 🔧 Деплой на сервер

### На VPS/Dedicated сервере:

1. **Подключись к серверу**:
   ```bash
   ssh user@your-server.com
   ```

2. **Установи Python и Git**:
   ```bash
   # Ubuntu/Debian:
   sudo apt update
   sudo apt install python3 python3-pip python3-venv git
   
   # CentOS/RHEL:
   sudo yum install python3 python3-pip git
   ```

3. **Скачай проект**:
   ```bash
   git clone <your-repo-url>
   cd telegram-stats-bot
   ```

4. **Настрой окружение**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Установи токен**:
   ```bash
   export TELEGRAM_BOT_TOKEN="YOUR_TOKEN"
   ```

6. **Запуск в фоне с помощью screen**:
   ```bash
   # Установи screen если нет
   sudo apt install screen
   
   # Создай сессию
   screen -S telegram_bot
   
   # Запусти бота
   python main.py
   
   # Отключись от сессии: Ctrl+A, затем D
   # Подключись обратно: screen -r telegram_bot
   ```

### Автозапуск с systemd:

1. **Создай service файл**:
   ```bash
   sudo nano /etc/systemd/system/telegram-stats-bot.service
   ```

2. **Добавь конфигурацию**:
   ```ini
   [Unit]
   Description=Telegram Stats Bot
   After=network.target
   
   [Service]
   Type=simple
   User=your-username
   WorkingDirectory=/path/to/telegram-stats-bot
   Environment=TELEGRAM_BOT_TOKEN=YOUR_TOKEN_HERE
   ExecStart=/path/to/telegram-stats-bot/venv/bin/python main.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

3. **Активируй сервис**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable telegram-stats-bot
   sudo systemctl start telegram-stats-bot
   
   # Проверь статус
   sudo systemctl status telegram-stats-bot
   ```

## 🐛 Решение проблем

### Бот не запускается:
- Проверь правильность токена
- Убедись что установлены все зависимости: `pip install -r requirements.txt`
- Проверь версию Python: `python --version` (нужен 3.8+)

### Бот не отвечает:
- Проверь интернет соединение
- Убедись что токен активен (проверь в @BotFather)
- Посмотри логи на наличие ошибок

### Данные не сохраняются:
- Проверь права на запись в директорию проекта
- Убедись что создалась папка `user_data/`

## 📊 Мониторинг

Для просмотра логов:
```bash
# Если запущен через systemd
sudo journalctl -u telegram-stats-bot -f

# Если запущен в screen
screen -r telegram_bot
```

## 🔒 Безопасность

- Никогда не публикуй токен бота в открытом доступе
- Регулярно делай бэкапы папки `user_data/`
- Ограничь доступ к серверу только необходимыми пользователями

## 📝 Лицензия

Проект создан для личного использования. Можешь модифицировать под свои нужды.