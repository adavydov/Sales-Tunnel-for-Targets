import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL


ALLOWED_STATUSES = {"new", "not_fit", "nurture", "ready_t1", "ready_t2"}
ALLOWED_CONTACT_TYPES = {"email", "telegram", "phone"}
CONTACT_COLUMN_BY_TYPE = {
    "email": "contact_email",
    "telegram": "contact_telegram",
    "phone": "contact_phone",
}
ALLOWED_PROFILE_FIELDS = {
    "company",
    "company_website",
    "simulate_consent",
    "valuation_consent",
}
ALLOWED_FUNNEL_FIELDS = {
    "last_connection_at",
    "contact_name",
    "contact_phone",
    "contact_email",
    "accountants_count",
    "avg_salary",
    "express_saving_6",
    "express_saving_12",
    "meeting_booked",
    "advisory_band",
    "active_clients_count",
    "standardization_level",
    "automation_level",
    "precise_assessment",
    "margin_percent",
    "growth_band",
    "mna_interest",
    "file_downloaded",
    "uploaded_file_link",
}
ALLOWED_STANDARDIZATION = {"high", "medium", "low"}
ALLOWED_AUTOMATION = {"none", "partial", "systems"}
ALLOWED_ADVISORY = {"lt10", "10_20", "gt20"}
ALLOWED_GROWTH = {"none", "normal", "fast"}
ALLOWED_MNA = {"yes", "no"}



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
                    company TEXT,
                    contact_name TEXT,
                    contact_phone TEXT,
                    contact_email TEXT,
                    contact_position TEXT,
                    onboarding_consent TEXT,
                    contact_telegram TEXT,
                    company_website TEXT,
                    simulate_consent TEXT,
                    valuation_consent TEXT,
                    last_connection_at TIMESTAMP,
                    accountants_count INTEGER,
                    avg_salary INTEGER,
                    express_saving_6 BIGINT,
                    express_saving_12 BIGINT,
                    meeting_booked BOOLEAN DEFAULT FALSE,
                    advisory_band TEXT CHECK (advisory_band IN ('lt10', '10_20', 'gt20')),
                    active_clients_count INTEGER,
                    standardization_level TEXT CHECK (standardization_level IN ('high', 'medium', 'low')),
                    automation_level TEXT CHECK (automation_level IN ('none', 'partial', 'systems')),
                    precise_assessment TEXT,
                    margin_percent INTEGER,
                    growth_band TEXT CHECK (growth_band IN ('none', 'normal', 'fast')),
                    mna_interest TEXT CHECK (mna_interest IN ('yes', 'no')),
                    file_downloaded BOOLEAN DEFAULT FALSE,
                    uploaded_file_link TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS company TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_name TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_phone TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_email TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_position TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS onboarding_consent TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS contact_telegram TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS company_website TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS simulate_consent TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS valuation_consent TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS last_connection_at TIMESTAMP;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS accountants_count INTEGER;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS avg_salary INTEGER;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS express_saving_6 BIGINT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS express_saving_12 BIGINT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS meeting_booked BOOLEAN DEFAULT FALSE;""")
            await cur.execute(
                """ALTER TABLE users ADD COLUMN IF NOT EXISTS advisory_band TEXT
                   CHECK (advisory_band IN ('lt10', '10_20', 'gt20'));"""
            )
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS active_clients_count INTEGER;""")
            await cur.execute(
                """ALTER TABLE users ADD COLUMN IF NOT EXISTS standardization_level TEXT
                   CHECK (standardization_level IN ('high', 'medium', 'low'));"""
            )
            await cur.execute(
                """ALTER TABLE users ADD COLUMN IF NOT EXISTS automation_level TEXT
                   CHECK (automation_level IN ('none', 'partial', 'systems'));"""
            )
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS precise_assessment TEXT;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS margin_percent INTEGER;""")
            await cur.execute(
                """ALTER TABLE users ADD COLUMN IF NOT EXISTS growth_band TEXT
                   CHECK (growth_band IN ('none', 'normal', 'fast'));"""
            )
            await cur.execute(
                """ALTER TABLE users ADD COLUMN IF NOT EXISTS mna_interest TEXT
                   CHECK (mna_interest IN ('yes', 'no'));"""
            )
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS file_downloaded BOOLEAN DEFAULT FALSE;""")
            await cur.execute("""ALTER TABLE users ADD COLUMN IF NOT EXISTS uploaded_file_link TEXT;""")

            await cur.execute("""ALTER TABLE users DROP COLUMN IF EXISTS lead_email;""")
            await cur.execute("""ALTER TABLE users DROP COLUMN IF EXISTS lead_telegram;""")
            await cur.execute("""ALTER TABLE users DROP COLUMN IF EXISTS lead_phone;""")
            await cur.execute("""ALTER TABLE users DROP COLUMN IF EXISTS track;""")
            await cur.execute("""ALTER TABLE users DROP COLUMN IF EXISTS role;""")
            await cur.execute("""ALTER TABLE users DROP COLUMN IF EXISTS business_size;""")
            await cur.execute("""ALTER TABLE users DROP COLUMN IF EXISTS timeframe;""")
            await cur.execute("""ALTER TABLE users DROP COLUMN IF EXISTS motivation;""")

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
                INSERT INTO users (telegram_id, username, first_name, last_name, last_connection_at)
                VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP)
                ON CONFLICT (telegram_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    last_connection_at = CURRENT_TIMESTAMP,
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


async def save_funnel_fields(user_id: int, **fields):
    if not fields:
        return

    unknown = set(fields) - ALLOWED_FUNNEL_FIELDS
    if unknown:
        raise ValueError(f"Недопустимые funnel-поля: {', '.join(sorted(unknown))}")

    if "standardization_level" in fields and fields["standardization_level"] not in ALLOWED_STANDARDIZATION:
        raise ValueError(f"Недопустимая стандартизация: {fields['standardization_level']}")
    if "automation_level" in fields and fields["automation_level"] not in ALLOWED_AUTOMATION:
        raise ValueError(f"Недопустимая автоматизация: {fields['automation_level']}")
    if "advisory_band" in fields and fields["advisory_band"] not in ALLOWED_ADVISORY:
        raise ValueError(f"Недопустимый advisory: {fields['advisory_band']}")
    if "growth_band" in fields and fields["growth_band"] not in ALLOWED_GROWTH:
        raise ValueError(f"Недопустимый рост: {fields['growth_band']}")
    if "mna_interest" in fields and fields["mna_interest"] not in ALLOWED_MNA:
        raise ValueError(f"Недопустимый M&A: {fields['mna_interest']}")

    set_parts = []
    values = []
    for field_name, value in fields.items():
        set_parts.append(f"{field_name} = %s")
        values.append(value)
    set_parts.append("updated_at = CURRENT_TIMESTAMP")
    values.append(user_id)

    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                UPDATE users
                SET {", ".join(set_parts)}
                WHERE id = %s;
                """,
                values,
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


async def get_tool_consent(user_id: int, tool_name: str) -> bool:
    if tool_name not in {"simulate", "valuation"}:
        raise ValueError(f"Unsupported tool for consent lookup: {tool_name}")

    column_name = f"{tool_name}_consent"

    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                SELECT {column_name}
                FROM users
                WHERE id = %s;
                """,
                (user_id,),
            )
            row = await cur.fetchone()

        if not row:
            return False

        return row[column_name] == "accepted"
    finally:
        await conn.close()
