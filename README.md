# Sales Tunnel Bot MVP

Telegram-бот для первичной квалификации пользователей с возможностью ознакомиться с материалами, оценить бизнес и получить контактные данные команды.

## Функционал MVP

- /start — приветственное меню с 3 кнопками:
  1. Почитать материалы — присылает 5 локальных файлов/видео
  2. Оценить бизнес — развилка на трек 1 / трек 2 с минимальным опросником (роль, размер, срок, мотив)
  3. Связаться с нами — показывает контактные данные команды
- Финальные экраны треков с кнопкой “Оставить контакт”
- Контактный flow:
  - подтверждение использования данных
  - выбор формата контакта (email / Telegram / телефон)
  - запись данных в PostgreSQL
  - возможность добавить ещё один контакт или исправить существующий
  - кнопка “Меню” доступна только после завершения контактного flow
- Прогрев и вопросы закомментированы/отключены для MVP

## Структура проекта

Sales-Tunnel-for-Targets/

├── .env

├── .gitignore

├── main.py

└── app/

    ├── __init__.py

    ├── config.py

    ├── db.py

    ├── keyboards.py

    ├── materials.py

    ├── scoring.py

    ├── states.py

    └── handlers/

        ├── __init__.py
        
        └── start.py

## Установка

1. Клонировать репозиторий:
git clone <URL>
cd Sales-Tunnel-for-Targets

2. Создать виртуальное окружение и активировать:
python3 -m venv .venv
source .venv/bin/activate

3. Установить зависимости:
python3 -m pip install --upgrade pip
python3 -m pip install aiogram python-dotenv "psycopg[binary]" APScheduler

4. Создать .env файл:
BOT_TOKEN=<ваш_токен_бота>
DATABASE_URL=postgresql://bot_user:<сложный_пароль>@localhost:5432/sales_tunnel_for_targets_bot_db
GOOGLE_SHEETS_API_KEY=<google_api_key_для_sheets>
GOOGLE_SHEETS_SPREADSHEET_ID=<id_таблицы>
GOOGLE_SHEETS_RANGE=Content-events!A2:F

## Настройка PostgreSQL

- Локальный PostgreSQL (Homebrew или Postgres.app)
- Создать пользователя и базу:
CREATE USER bot_user WITH PASSWORD '<сложный_пароль>';
CREATE DATABASE sales_tunnel_for_targets_bot_db OWNER bot_user;

- Таблицы создаются автоматически при запуске бота через init_db()

## Запуск бота

source .venv/bin/activate
python3 main.py

##Материалы

- 5 локальных файлов/видео находятся в materials/
- При нажатии Почитать материалы бот отправляет их пользователю

## Контактный flow

- После трека пользователь может оставить контакт
- Подтверждает использование данных
- Выбирает тип контакта: email / Telegram / телефон
- Вводит значение → сохраняется в БД
- Можно добавить ещё один контакт или исправить существующий
- После успешного ввода всех контактов кнопка “Меню” снова доступна

## Конфигурация

- Кнопки и тексты настраиваются в keyboards.py
- FSM состояния треков и контактов — states.py
- Расчёт fit/intent/status — scoring.py
- Материалы — materials.py
- Хранение и логирование — db.py
