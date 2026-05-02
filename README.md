# Telegram-бот для заявок на обучение

Асинхронный Telegram-бот на Python 3.12 и aiogram 3. Работает через long polling, сохраняет заявки в SQLite и отправляет уведомления в админскую группу.

## Почему long polling здесь нормален

Для небольшого бота по сбору заявок long polling подходит хорошо: не нужен публичный HTTPS endpoint, не нужно открывать входящие порты, проще запуск через Docker Compose. Вебхук обычно выбирают для высокой нагрузки или когда уже есть готовая инфраструктура с HTTPS и reverse proxy.

## Как создать бота через BotFather

1. Откройте в Telegram [@BotFather](https://t.me/BotFather).
2. Отправьте команду `/newbot`.
3. Укажите имя и username бота.
4. Скопируйте токен и сохраните его в `.env` как `BOT_TOKEN`.

## Настройка `.env`

Создайте файл `.env` из примера:

```bash
cp .env.example .env
```

Заполните значения:

```env
BOT_TOKEN=123456789:replace_with_token_from_botfather
ADMIN_CHAT_ID=0
DATABASE_URL=sqlite+aiosqlite:////app/data/applications.db
LOG_LEVEL=INFO
TELEGRAM_PROXY_URL=
SCHOOL_TEXT=С помощью бота вы сможете записаться на бесплатный пробный урок\nЗдравствуйте!\n...
```

`SCHOOL_TEXT` можно хранить одной строкой с `\n` для переносов строк. Бот автоматически превратит `\n` в реальные переносы.

Если сервер не может подключиться к Telegram API напрямую, укажите прокси:

```env
TELEGRAM_PROXY_URL=socks5://host.docker.internal:1080
```

Для Linux-сервера чаще всего удобнее подключить контейнер к сети хоста и использовать локальный Xray на `127.0.0.1`:

```yaml
services:
  bot:
    network_mode: host
```

Тогда в `.env` можно указать:

```env
TELEGRAM_PROXY_URL=socks5://127.0.0.1:1080
```

Для деплоя на Linux-сервер с локальным Xray можно использовать готовый файл:

```bash
docker compose -f docker-compose.server.yml up -d --build
```

## Как узнать `chat_id` группы

1. Временно оставьте `ADMIN_CHAT_ID=0`.
2. Запустите бота.
3. Добавьте бота в нужную Telegram-группу.
4. В группе отправьте команду `/chat_id`.
5. Бот ответит ID текущего чата. Для групп он обычно отрицательный, например `-1001234567890`.
6. Впишите это значение в `.env` как `ADMIN_CHAT_ID` и перезапустите контейнер.

## Запуск

```bash
docker compose up -d --build
```

Контейнер не открывает входящие порты. База SQLite хранится в папке `data/` на хосте.

## Логи

```bash
docker compose logs -f bot
```

Остановить бота:

```bash
docker compose down
```

## Команды бота

- `/start` - начать сценарий и выбрать возраст ребенка.
- `/cancel` - сбросить текущий сценарий.
- `/chat_id` - показать ID текущего чата.
