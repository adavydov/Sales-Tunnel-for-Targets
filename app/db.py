import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL


ALLOWED_TRACKS = {"t1", "t2"}
ALLOWED_ROLES = {"owner", "partner", "ceo", "ops"}
ALLOWED_BUSINESS_SIZES = {"large", "medium", "small"}
ALLOWED_TIMEFRAMES = {"now", "3_6", "6_12", "later"}
ALLOWED_MOTIVATIONS = {
    "exit", "liquidity", "burnout", "risk",
    "growth", "partner", "control", "scale",
}
ALLOWED_STATUSES = {"new", "not_fit", "nurture", "ready_t1", "ready_t2"}
ALLOWED_CONTACT_TYPES = {"email", "telegram", "phone"}
CONTACT_COLUMN_BY_TYPE = {
    "email": "contact_email",
    "telegram": "contact_telegram",
    "phone": "contact_phone",
}
ALLOWED_PROFILE_FIELDS = {
    "track",
    "role",
    "business_size",
    "timeframe",
    "motivation",
    "company",
    "contact_name",
    "contact_phone",
    "contact_email",
    "contact_position",
    "onboarding_consent",
}



WARMUP_SEED_MESSAGES = [
    {
        "slug": "case_founder_exit",
        "title": "Кейс: собственник вышел из операционки",
        "body": (
            "Один из собственников годами держал бизнес на себе и не мог выйти "
            "из ежедневного операционного управления. После подготовки к сделке "
            "и пересборки управленческой модели он получил возможность обсуждать "
            "продажу бизнеса с сильной переговорной позиции."
        ),
    },
    {
        "slug": "fact_price_depends_on_system",
        "title": "Факт: стоимость бизнеса зависит не только от выручки",
        "body": (
            "Покупатели смотрят не только на финансовые показатели, но и на то, "
            "насколько бизнес может работать без полного ручного участия собственника. "
            "Чем лучше система управления, тем выше шанс на качественную сделку."
        ),
    },
    {
        "slug": "case_partner_growth",
        "title": "Кейс: партнерство вместо полной продажи",
        "body": (
            "Не всем собственникам подходит сценарий полной продажи. В одном из кейсов "
            "основатель сохранил стратегический контроль, но привлек сильного партнера "
            "для масштабирования и снятия части нагрузки."
        ),
    },
    {
        "slug": "fact_timing_matters",
        "title": "Факт: поздний выход на переговоры снижает гибкость",
        "body": (
            "Когда собственник начинает думать о продаже или партнерстве слишком поздно, "
            "пространство для сильных решений обычно уже меньше. Подготовка заранее почти "
            "всегда дает более выгодные варианты."
        ),
    },
    {
        "slug": "case_risk_reduction",
        "title": "Кейс: продажа части бизнеса как способ снизить риски",
        "body": (
            "Для некоторых компаний оптимальным шагом становится не полная продажа, "
            "а частичный выход с распределением рисков и ответственности между партнерами."
        ),
    },
    {
        "slug": "fact_owner_burnout",
        "title": "Факт: усталость собственника часто маскируется под «ещё чуть-чуть потерплю»",
        "body": (
            "Во многих случаях собственник не принимает решение, потому что привыкает "
            "к постоянной перегрузке. Но именно в этот момент полезно посмотреть на сценарий "
            "продажи или партнерства как на управленческое решение, а не как на поражение."
        ),
    },
]


async def get_connection():
    return await psycopg.AsyncConnection.connect(
        DATABASE_URL,
        row_factory=dict_row
    )


async def seed_warmup_messages(conn):
    async with conn.cursor() as cur:
        for item in WARMUP_SEED_MESSAGES:
            await cur.execute("""
                INSERT INTO warmup_messages (slug, title, body)
                VALUES (%s, %s, %s)
                ON CONFLICT (slug) DO NOTHING;
            """, (item["slug"], item["title"], item["body"]))


async def init_db():
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            # Legacy tables are no longer used after schema simplification.
            await cur.execute("""
                DROP TABLE IF EXISTS lead_contacts;
            """)
            await cur.execute("""
                DROP TABLE IF EXISTS user_profiles;
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    track TEXT CHECK (track IN ('t1', 't2')),
                    role TEXT CHECK (role IN ('owner', 'partner', 'ceo', 'ops')),
                    business_size TEXT CHECK (business_size IN ('large', 'medium', 'small')),
                    timeframe TEXT CHECK (timeframe IN ('now', '3_6', '6_12', 'later')),
                    motivation TEXT CHECK (
                        motivation IN ('exit', 'liquidity', 'burnout', 'risk', 'growth', 'partner', 'control', 'scale')
                    ),
                    company TEXT,
                    contact_name TEXT,
                    contact_phone TEXT,
                    contact_email TEXT,
                    contact_position TEXT,
                    onboarding_consent TEXT,
                    contact_telegram TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS track TEXT CHECK (track IN ('t1', 't2'));
            """)
            await cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS role TEXT CHECK (role IN ('owner', 'partner', 'ceo', 'ops'));
            """)
            await cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS business_size TEXT CHECK (business_size IN ('large', 'medium', 'small'));
            """)
            await cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS timeframe TEXT CHECK (timeframe IN ('now', '3_6', '6_12', 'later'));
            """)
            await cur.execute("""
                ALTER TABLE users ADD COLUMN IF NOT EXISTS motivation TEXT CHECK (
                    motivation IN ('exit', 'liquidity', 'burnout', 'risk', 'growth', 'partner', 'control', 'scale')
                );
            """)
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS company TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_name TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_phone TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_email TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_position TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_consent TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_telegram TEXT;""")

            await cur.execute("""ALTER TABLE users DROP COLUMN IF EXISTS lead_email;""")
            await cur.execute("""ALTER TABLE users DROP COLUMN IF EXISTS lead_telegram;""")
            await cur.execute("""ALTER TABLE users DROP COLUMN IF EXISTS lead_phone;""")

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS lead_events (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    event_name TEXT NOT NULL,
                    event_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS user_questions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    question_text TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'new'
                        CHECK (status IN ('new', 'resolved', 'not_resolved')),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS user_scores (
                    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    fit_score INTEGER DEFAULT 0,
                    intent_score INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'new'
                        CHECK (status IN ('new', 'not_fit', 'nurture', 'ready_t1', 'ready_t2')),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS warmup_messages (
                    id SERIAL PRIMARY KEY,
                    slug TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    is_active BOOLEAN NOT NULL DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS warmup_delivery_logs (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    warmup_message_id INTEGER NOT NULL REFERENCES warmup_messages(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_lead_events_user_created
                ON lead_events (user_id, created_at DESC);
            """)

            await cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_questions_user_status
                ON user_questions (user_id, status);
            """)

            await cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_warmup_delivery_user_created
                ON warmup_delivery_logs (user_id, created_at DESC);
            """)


        await seed_warmup_messages(conn)
        await conn.commit()
    finally:
        await conn.close()


async def upsert_user(
    telegram_id: int,
    username: str | None,
    first_name: str | None,
    last_name: str | None,
) -> int:
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO users (telegram_id, username, first_name, last_name)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id;
            """, (telegram_id, username, first_name, last_name))

            row = await cur.fetchone()

        await conn.commit()
        return row["id"]
    finally:
        await conn.close()


async def add_event(user_id: int, event_name: str, event_value: str | None = None):
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO lead_events (user_id, event_name, event_value)
                VALUES (%s, %s, %s);
            """, (user_id, event_name, event_value))

        await conn.commit()
    finally:
        await conn.close()


async def create_user_question(user_id: int, question_text: str) -> int:
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO user_questions (user_id, question_text)
                VALUES (%s, %s)
                RETURNING id;
            """, (user_id, question_text))

            row = await cur.fetchone()

        await conn.commit()
        return row["id"]
    finally:
        await conn.close()


async def update_question_status(question_id: int, status: str):
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                UPDATE user_questions
                SET status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s;
            """, (status, question_id))

        await conn.commit()
    finally:
        await conn.close()


async def save_profile_field(user_id: int, field_name: str, value: str):
    if field_name not in ALLOWED_PROFILE_FIELDS:
        raise ValueError(f"Недопустимое поле профиля: {field_name}")
    if field_name == "track" and value not in ALLOWED_TRACKS:
        raise ValueError(f"Недопустимое значение track: {value}")
    if field_name == "role" and value not in ALLOWED_ROLES:
        raise ValueError(f"Недопустимое значение role: {value}")
    if field_name == "business_size" and value not in ALLOWED_BUSINESS_SIZES:
        raise ValueError(f"Недопустимое значение business_size: {value}")
    if field_name == "timeframe" and value not in ALLOWED_TIMEFRAMES:
        raise ValueError(f"Недопустимое значение timeframe: {value}")
    if field_name == "motivation" and value not in ALLOWED_MOTIVATIONS:
        raise ValueError(f"Недопустимое значение motivation: {value}")

    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                UPDATE users
                SET {field_name} = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s;
                """,
                (value, user_id),
            )

        await conn.commit()
    finally:
        await conn.close()


async def save_scores(user_id: int, fit_score: int, intent_score: int, status: str):
    if status not in ALLOWED_STATUSES:
        raise ValueError(f"Недопустимый статус: {status}")

    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO user_scores (user_id, fit_score, intent_score, status)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    fit_score = EXCLUDED.fit_score,
                    intent_score = EXCLUDED.intent_score,
                    status = EXCLUDED.status,
                    updated_at = CURRENT_TIMESTAMP;
            """, (user_id, fit_score, intent_score, status))

        await conn.commit()
    finally:
        await conn.close()


async def upsert_contact(user_id: int, contact_type: str, contact_value: str):
    if contact_type not in ALLOWED_CONTACT_TYPES:
        raise ValueError(f"Недопустимый тип контакта: {contact_type}")

    column_name = CONTACT_COLUMN_BY_TYPE[contact_type]

    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                UPDATE users
                SET {column_name} = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s;
                """,
                (contact_value, user_id),
            )

        await conn.commit()
    finally:
        await conn.close()


async def get_all_users():
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT id, telegram_id
                FROM users
                ORDER BY id ASC;
            """)
            rows = await cur.fetchall()
        return rows
    finally:
        await conn.close()


async def get_random_warmup_message():
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT id, title, body
                FROM warmup_messages
                WHERE is_active = TRUE
                ORDER BY RANDOM()
                LIMIT 1;
            """)
            row = await cur.fetchone()
        return row
    finally:
        await conn.close()


async def log_warmup_delivery(user_id: int, warmup_message_id: int):
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                INSERT INTO warmup_delivery_logs (user_id, warmup_message_id)
                VALUES (%s, %s);
            """, (user_id, warmup_message_id))
        await conn.commit()
    finally:
        await conn.close()


async def get_filled_contact_types(user_id: int) -> list[str]:
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                SELECT contact_email, contact_telegram, contact_phone
                FROM users
                WHERE id = %s;
            """, (user_id,))
            row = await cur.fetchone()

        if not row:
            return []

        filled_types: list[str] = []
        if row["contact_email"]:
            filled_types.append("email")
        if row["contact_telegram"]:
            filled_types.append("telegram")
        if row["contact_phone"]:
            filled_types.append("phone")

        return filled_types
    finally:
        await conn.close()