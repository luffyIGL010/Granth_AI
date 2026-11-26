
import sqlite3
from pathlib import Path
from datetime import datetime, timezone


# ==========================================
# DATABASE CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "granth_mitra.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


# ==========================================
# CREATE DATABASE TABLES
# ==========================================

def init_db():

    with get_connection() as connection:

        connection.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                session_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,

                FOREIGN KEY (session_id)
                REFERENCES conversations(session_id)
                ON DELETE CASCADE
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_messages_session_id
            ON messages(session_id, id)
        """)




        connection.execute("""
            CREATE TABLE IF NOT EXISTS user_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                memory TEXT NOT NULL,
                category TEXT DEFAULT 'general',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE INDEX IF NOT EXISTS
            idx_user_memories_user_id
            ON user_memories(user_id)
        """)



# ==========================================
# CREATE CONVERSATION
# ==========================================

def create_conversation(session_id, title):

    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:

        connection.execute("""
            INSERT OR IGNORE INTO conversations (
                session_id,
                title,
                summary,
                created_at,
                updated_at
            )
            VALUES (?, ?, '', ?, ?)
        """, (session_id, title[:60], now, now))


# ==========================================
# SAVE MESSAGE
# ==========================================

def save_message(session_id, role, content):

    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:

        connection.execute("""
            INSERT INTO messages (
                session_id,
                role,
                content,
                created_at
            )
            VALUES (?, ?, ?, ?)
        """, (session_id, role, content, now))

        connection.execute("""
            UPDATE conversations
            SET updated_at = ?
            WHERE session_id = ?
        """, (now, session_id))


# ==========================================
# GET CONVERSATION
# ==========================================

def get_conversation(session_id):

    with get_connection() as connection:

        row = connection.execute("""
            SELECT *
            FROM conversations
            WHERE session_id = ?
        """, (session_id,)).fetchone()

        return dict(row) if row else None


# ==========================================
# GET MESSAGES
# ==========================================

def get_messages(session_id, limit=None):

    with get_connection() as connection:

        if limit is None:

            rows = connection.execute("""
                SELECT role, content, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
            """, (session_id,)).fetchall()

        else:

            rows = connection.execute("""
                SELECT role, content, created_at
                FROM (
                    SELECT id, role, content, created_at
                    FROM messages
                    WHERE session_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                )
                ORDER BY id ASC
            """, (session_id, limit)).fetchall()

        return [dict(row) for row in rows]


# ==========================================
# UPDATE SUMMARY
# ==========================================

def update_summary(session_id, summary):

    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:

        connection.execute("""
            UPDATE conversations
            SET summary = ?, updated_at = ?
            WHERE session_id = ?
        """, (summary, now, session_id))


# ==========================================
# GET ALL CONVERSATIONS
# ==========================================

def get_all_conversations(limit=50):

    with get_connection() as connection:

        rows = connection.execute("""
            SELECT
                session_id,
                title,
                created_at,
                updated_at
            FROM conversations
            ORDER BY updated_at DESC
            LIMIT ?
        """, (limit,)).fetchall()

        return [dict(row) for row in rows]


# ==========================================
# INITIALIZE DATABASE
# ==========================================

init_db()




# ==========================================
# DELETE CONVERSATION
# ==========================================

def delete_conversation(session_id):

    with get_connection() as connection:

        cursor = connection.execute("""
            DELETE FROM conversations
            WHERE session_id = ?
        """, (session_id,))

        return cursor.rowcount > 0






# ==========================================
# SAVE USER MEMORY
# ==========================================


# ==========================================
# SAVE USER MEMORY (DUPLICATE PREVENTION)
# ==========================================

def save_memory(user_id, memory, category="general"):

    now = datetime.now(timezone.utc).isoformat()

    memory = memory.strip()

    if not memory:
        return None

    with get_connection() as connection:

        existing = connection.execute("""
            SELECT id
            FROM user_memories
            WHERE user_id = ?
            AND LOWER(TRIM(memory)) = LOWER(TRIM(?))
        """, (user_id, memory)).fetchone()

        if existing:
            return existing["id"]

        cursor = connection.execute("""
            INSERT INTO user_memories (
                user_id,
                memory,
                category,
                created_at,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, memory, category, now, now))

        return cursor.lastrowid





# ==========================================
# GET USER MEMORIES
# ==========================================

def get_user_memories(user_id):

    with get_connection() as connection:

        rows = connection.execute("""
            SELECT id, memory, category, created_at, updated_at
            FROM user_memories
            WHERE user_id = ?
            ORDER BY updated_at DESC
        """, (user_id,)).fetchall()

        return [dict(row) for row in rows]



# ==========================================
# UPDATE USER MEMORY
# ==========================================

def update_memory(memory_id, user_id, new_memory, category=None):

    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as connection:

        cursor = connection.execute("""
            UPDATE user_memories
            SET memory = ?,
                category = COALESCE(?, category),
                updated_at = ?
            WHERE id = ? AND user_id = ?
        """, (new_memory, category, now, memory_id, user_id))

        return cursor.rowcount > 0




# ==========================================
# DELETE USER MEMORY
# ==========================================

def delete_memory(memory_id, user_id):

    with get_connection() as connection:

        cursor = connection.execute("""
            DELETE FROM user_memories
            WHERE id = ? AND user_id = ?
        """, (memory_id, user_id))

        return cursor.rowcount > 0
