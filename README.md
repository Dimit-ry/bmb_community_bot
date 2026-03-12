# Telegram Reminder Bot

Telegram бот для отправки напоминаний и сбора ответов от пользователей.

## Функционал

### Для пользователей:
- Подписка на рассылки
- Получение напоминаний с кнопками ответа
- Возможность отписаться от рассылки

### Для администраторов:
- Назначение других администраторов
- Создание и отправка рассылок
- Отложенная отправка сообщений
- Статистика по ответам пользователей
- Статистика по подписчикам
- Поддержка медиафайлов (фото, документы)
- HTML форматирование и гиперссылки

## Технологии

- **Python 3.11+**
- **aiogram 3.4+** - фреймворк для Telegram ботов
- **SQLite** - база данных
- **APScheduler** - для отложенных сообщений
- **Docker** - для развертывания

## Установка и развертывание

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd telegram-reminder-bot
```

### 2. Настройка окружения
```bash
# Создайте файл .env на основе .env.example
cp .env.example .env
```

Отредактируйте `.env` файл:
```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_admin_telegram_id_here
DATABASE_PATH=bot.db
```

### 3. Запуск через Docker (рекомендуется)

```bash
# Сборка и запуск
docker-compose up -d

# Просмотр логов
docker-compose logs -f telegram-bot

# Остановка
docker-compose down
```

### 4. Запуск без Docker

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск бота
python bot.py
```

## Использование

### Для пользователей:
1. Найдите бота в Telegram и нажмите "Start"
2. Вы будете автоматически подписаны на рассылки
3. При получении напоминания выберите один из вариантов ответа

### Для администраторов:
1. Получите права администратора (назначаются через /admin)
2. Используйте команду `/admin` для доступа к панели управления
3. Создавайте рассылки и просматривайте статистику

## Структура проекта

```
telegram-reminder-bot/
├── bot.py              # Основной файл бота
├── database.py         # Работа с базой данных
├── keyboards.py        # Клавиатуры и кнопки
├── config.py           # Конфигурация
├── requirements.txt    # Зависимости Python
├── Dockerfile          # Конфигурация Docker
├── docker-compose.yml  # Docker Compose конфигурация
├── .env.example        # Пример файла окружения
└── README.md          # Документация
```

## Команды бота

- `/start` - Начать работу с ботом
- `/admin` - Панель администратора (только для админов)

## 🚀 Развертывание на хостинге

### Быстрый деплой через Railway (рекомендуется)

1. **Подключите GitHub к Railway:**
   - Зайдите на [railway.app](https://railway.app)
   - Нажмите "Deploy from GitHub repo"
   - Выберите репозиторий `bmb_community_bot`

2. **Настройте переменные окружения:**
   В Railway Settings → Variables добавьте:
   ```
   BOT_TOKEN=8794012246:AAEATYMVG-ITc3X1y9JoGAM27M85ImR1j70
   ADMIN_ID=420366725
   DATABASE_PATH=/app/data/bot.db
   ```

3. **Запустите деплой:**
   - Railway автоматически определит Python проект
   - Установит зависимости из `requirements.txt`
   - Запустит бота через `Procfile`

### Альтернативные хостинги

**Render:**
- Аналогично Railway через GitHub integration
- Variables: `BOT_TOKEN`, `ADMIN_ID`, `DATABASE_PATH=/app/data/bot.db`

**Heroku:**
- Создайте приложение через Heroku CLI
- Установите переменные: `heroku config:set BOT_TOKEN=... DATABASE_PATH=/app/data/bot.db`

### Docker деплой

```bash
# Сборка и запуск
docker-compose up -d

# Или на сервере:
docker build -t telegram-bot .
docker run -d --env-file .env telegram-bot
```

## Поддержка

При возникновении проблем:
1. Проверьте логи: `docker-compose logs telegram-bot`
2. Убедитесь, что токен бота правильный
3. Проверьте, что ID администратора указан верно

## Лицензия

MIT License
