import psycopg
from psycopg.rows import dict_row

from app.config import DATABASE_URL


async def get_connection():
    return await psycopg.AsyncConnection.connect(
        DATABASE_URL,
        row_factory=dict_row
    )


async def init_db():
    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    track TEXT,
                    role TEXT,
                    business_size TEXT,
                    timeframe TEXT,
                    motivation TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS user_scores (
                    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    fit_score INTEGER DEFAULT 0,
                    intent_score INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'new',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

            await cur.execute("""
                CREATE TABLE IF NOT EXISTS lead_events (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    event_name TEXT NOT NULL,
                    event_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

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


async def save_profile_field(user_id: int, field_name: str, value: str):
    allowed_fields = {"track", "role", "business_size", "timeframe", "motivation"}
    if field_name not in allowed_fields:
        raise ValueError(f"Недопустимое поле профиля: {field_name}")

    conn = await get_connection()
    try:
        async with conn.cursor() as cur:
            await cur.execute(
                f"""
                INSERT INTO user_profiles (user_id, {field_name})
                VALUES (%s, %s)
                ON CONFLICT (user_id) DO UPDATE SET
                    {field_name} = EXCLUDED.{field_name},
                    updated_at = CURRENT_TIMESTAMP;
                """,
                (user_id, value),
            )

        await conn.commit()
    finally:
        await conn.close()


async def save_scores(user_id: int, fit_score: int, intent_score: int, status: str):
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