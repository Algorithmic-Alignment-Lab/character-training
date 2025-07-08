import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import uuid

MAIN_DATABASE_FILE = "conversations.db"
CONVERSATIONS_DIR = "conversations"


def init_db(db_path: str = MAIN_DATABASE_FILE):
    """Initialize the database and create tables if they don't exist."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Create conversations table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL,
            name TEXT,
            system_prompt_name TEXT,
            system_prompt TEXT,
            model TEXT,
            summary TEXT
        )
        """)

        # Create messages table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            message_index INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
        """)

        # Create character_analysis table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS character_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id TEXT NOT NULL,
            message_id TEXT NOT NULL,
            is_in_character BOOLEAN NOT NULL,
            consistency_score INTEGER,
            trait_evaluations TEXT,
            analysis TEXT,
            interesting_moment BOOLEAN,
            failure_type TEXT,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id),
            FOREIGN KEY (message_id) REFERENCES messages (id)
        )
        """)

        # --- Schema Migrations ---
        cursor.execute("PRAGMA table_info(conversations)")
        convo_columns = [column[1] for column in cursor.fetchall()]
        if 'system_prompt' in convo_columns and 'system_prompt_name' not in convo_columns:
            cursor.execute("ALTER TABLE conversations RENAME COLUMN system_prompt TO system_prompt_name")
        if 'name' not in convo_columns:
            cursor.execute("ALTER TABLE conversations ADD COLUMN name TEXT")
        if 'system_prompt' not in convo_columns:
            cursor.execute("ALTER TABLE conversations ADD COLUMN system_prompt TEXT")

        cursor.execute("PRAGMA table_info(messages)")
        msg_columns = [c[1] for c in cursor.fetchall()]
        if 'id' in msg_columns and [c for c in cursor.execute("PRAGMA table_info(messages)").fetchall() if c[1] == 'id'][0][2] == 'INTEGER':
            # This is a more complex migration to change primary key from INT to TEXT (UUID)
            # For simplicity in this context, we assume new dbs will be correct
            # and old dbs might need manual migration if this script fails.
            pass # Simple solution: ignore for existing dbs and let new ones be created correctly

        conn.commit()


def rename_conversation(db_path: str, conversation_id: str, new_name: str):
    """Renames a conversation in the database."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE conversations SET name = ? WHERE id = ?", (new_name, conversation_id))
        conn.commit()

def save_analysis_to_db(conversation_id: str, message_id: str,
                        analysis_data: Dict, db_path: str = MAIN_DATABASE_FILE):
    """Save the character analysis to the database."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO character_analysis (
            conversation_id, message_id, is_in_character, consistency_score,
            trait_evaluations, analysis, interesting_moment, failure_type
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            conversation_id,
            message_id,
            analysis_data.get('is_in_character'),
            analysis_data.get('consistency_score'),
            json.dumps(analysis_data.get('trait_evaluations')),
            analysis_data.get('analysis'),
            analysis_data.get('interesting_moment'),
            analysis_data.get('failure_type')
        ))
        conn.commit()


def save_conversation_to_db(conversation_id: str, messages: List[Dict],
                            system_prompt: str, provider: str, model: str,
                            summary: str, db_path: str = MAIN_DATABASE_FILE):
    """Save or update a conversation, preserving creation time."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        cursor.execute("""
        INSERT OR REPLACE INTO conversations (
            id, created_at, system_prompt, provider, model, summary)
        VALUES (?, COALESCE((SELECT created_at FROM conversations WHERE id = ?),
               ?), ?, ?, ?, ?)
        """, (conversation_id, conversation_id, datetime.now().isoformat(),
              system_prompt, provider, model, summary))

        cursor.execute("DELETE FROM messages WHERE conversation_id = ?",
                       (conversation_id,))

        for i, msg in enumerate(messages):
            cursor.execute("""
            INSERT INTO messages (conversation_id, message_index, role, content)
            VALUES (?, ?, ?, ?)
            """, (conversation_id, i, msg['role'], msg['content']))

        conn.commit()


def load_conversation_from_db(db_path: str, conversation_id: str) -> Optional[Dict]:
    """Load a full conversation from the database."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM conversations WHERE id = ?",
                       (conversation_id,))
        convo_row = cursor.fetchone()

        if not convo_row:
            return None

        conversation = dict(convo_row)

        cursor.execute("""SELECT role, content FROM messages
                       WHERE conversation_id = ? ORDER BY message_index""",
                       (conversation_id,))
        messages = [dict(row) for row in cursor.fetchall()]

        conversation['messages'] = messages
        return conversation


def get_all_conversations_from_db(db_path: str) -> List[Dict]:
    """Retrieve all conversations with their summaries."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""SELECT id, created_at, summary, name FROM conversations
                       ORDER BY created_at DESC""")
        return [dict(row) for row in cursor.fetchall()]


def get_message_by_index_from_db(db_path: str, conversation_id: str,
                                 message_index: int) -> Optional[Dict]:
    """Get a specific message by its index from the database."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
        SELECT role, content FROM messages
        WHERE conversation_id = ? AND message_index = ?
        """, (conversation_id, message_index))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_conversations(db_path: str) -> List[Dict]:
    """Retrieve all conversations from a specific database file."""
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""SELECT id, created_at as start_time, model, system_prompt_name
                           FROM conversations ORDER BY created_at DESC""")
            return [dict(row) for row in cursor.fetchall()]
    except sqlite3.Error:
        return [] # Return empty list if table/columns not found


def get_messages(db_path: str, conversation_id: str) -> List[Dict]:
    """Load chat history from the database for a given conversation ID."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""SELECT id, role, content FROM messages
                       WHERE conversation_id = ? ORDER BY message_index""",
                       (conversation_id,))
        return [dict(row) for row in cursor.fetchall()]


def save_conversation(
    db_path: str, conversation_id: Optional[str], role: str,
    content: str, model: str, system_prompt_name: str, system_prompt: str
) -> tuple[str, str]:
    """Saves a single message, creating a new conversation if necessary."""
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())
            start_time = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO conversations (id, created_at, model, system_prompt_name, system_prompt)
                VALUES (?, ?, ?, ?, ?)
            """, (conversation_id, start_time, model, system_prompt_name, system_prompt))
        else:
            # Update model and persona if they have changed
            cursor.execute("""
                UPDATE conversations
                SET model = ?, system_prompt_name = ?, system_prompt = ?
                WHERE id = ?
            """, (model, system_prompt_name, system_prompt, conversation_id))

        message_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO messages (id, conversation_id, role, content, message_index)
            VALUES (?, ?, ?, ?, (SELECT COALESCE(MAX(message_index), -1) + 1
                               FROM messages WHERE conversation_id = ?))
        """, (message_id, conversation_id, role, content, conversation_id))
        conn.commit()
    return conversation_id, message_id


def get_conversation_by_message_id(db_path: str, message_id: str) -> Optional[Dict]:
    """Finds a conversation by a message ID."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.id, c.created_at as start_time, c.model, c.system_prompt_name
            FROM conversations c
            JOIN messages m ON c.id = m.conversation_id
            WHERE m.id = ?
        """, (message_id,))
        return dict(row) if (row := cursor.fetchone()) else None


def get_all_analysis_data(db_path: str = MAIN_DATABASE_FILE) -> List[Dict]:
    """Fetches all character analysis data for CSV export."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
        SELECT
            ca.conversation_id,
            c.system_prompt_name,
            c.model as ai_model,
            m.role as message_role,
            m.content as message_content,
            ca.message_id,
            ca.is_in_character,
            ca.failure_type,
            ca.consistency_score,
            ca.trait_evaluations,
            ca.analysis,
            ca.interesting_moment
        FROM character_analysis ca
        JOIN conversations c ON ca.conversation_id = c.id
        JOIN messages m ON ca.message_id = m.id
        """)
        return [dict(row) for row in cursor.fetchall()]


def migrate_json_to_sqlite():
    """Migrate conversations from JSON to SQLite and rename folder."""
    migrated_dir_name = f"{CONVERSATIONS_DIR}_migrated"
    if not os.path.exists(CONVERSATIONS_DIR) or os.path.exists(migrated_dir_name):
        return

    json_files = [f for f in os.listdir(CONVERSATIONS_DIR) if f.endswith('.json')]
    if not json_files:
        if os.path.exists(CONVERSATIONS_DIR):
            try:
                os.rename(CONVERSATIONS_DIR, migrated_dir_name)
                print(f"Renamed empty '{CONVERSATIONS_DIR}' to "
                      f"'{migrated_dir_name}'.")
            except OSError as e:
                print(f"Warning: Could not rename '{CONVERSATIONS_DIR}' "
                      f"directory: {e}")
        return

    print("Starting migration of conversations from JSON to SQLite...")
    with sqlite3.connect(MAIN_DATABASE_FILE) as conn:
        cursor = conn.cursor()

        for filename in json_files:
            filepath = os.path.join(CONVERSATIONS_DIR, filename)
            with open(filepath, 'r') as f:
                data = json.load(f)

            conversation_id = data['id']

            cursor.execute("SELECT id FROM conversations WHERE id = ?",
                           (conversation_id,))
            if cursor.fetchone():
                continue

            created_at = data.get('created_at', datetime.now().isoformat())
            messages = data.get('messages', [])
            system_prompt = data.get('system_prompt', '')
            provider = data.get('provider', '')
            model = data.get('model', '')
            summary = data.get('summary', '')

            cursor.execute("""
            INSERT INTO conversations (id, created_at, system_prompt, provider,
                                     model, summary)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (conversation_id, created_at, system_prompt, provider, model,
                  summary))

            for i, msg in enumerate(messages):
                cursor.execute("""
                INSERT INTO messages (conversation_id, message_index, role, content)
                VALUES (?, ?, ?, ?)
                """, (conversation_id, i, msg['role'], msg['content']))

            print(f"Migrated {filename} to SQLite.")

    print("Migration complete.")
    try:
        os.rename(CONVERSATIONS_DIR, migrated_dir_name)
        print(f"Renamed '{CONVERSATIONS_DIR}' to '{migrated_dir_name}'.")
    except OSError as e:
        print(f"Warning: Could not rename '{CONVERSATIONS_DIR}' "
              f"directory: {e}")


def merge_databases(source_db_path: str, target_db_path: str):
    """Merges records from the source database into the target database."""
    if not os.path.exists(source_db_path):
        print(f"Source database {source_db_path} not found. Skipping merge.")
        return

    print(f"Merging {source_db_path} into {target_db_path}...")
    source_conn = sqlite3.connect(source_db_path)
    target_conn = sqlite3.connect(target_db_path)

    source_cursor = source_conn.cursor()
    target_cursor = target_conn.cursor()

    # Merge conversations
    source_cursor.execute("SELECT * FROM conversations")
    for row in source_cursor.fetchall():
        target_cursor.execute("INSERT OR IGNORE INTO conversations VALUES "
                              "(?, ?, ?, ?, ?, ?)", row)

    # Merge messages
    source_cursor.execute("SELECT * FROM messages")
    for row in source_cursor.fetchall():
        target_cursor.execute("INSERT OR IGNORE INTO messages VALUES "
                              "(?, ?, ?, ?, ?)", row)

    # Merge character_analysis
    source_cursor.execute("SELECT * FROM character_analysis")
    for row in source_cursor.fetchall():
        target_cursor.execute("INSERT OR IGNORE INTO character_analysis VALUES "
                              "(?, ?, ?, ?, ?, ?, ?, ?, ?)", row)

    target_conn.commit()
    source_conn.close()
    target_conn.close()
    print("Merge complete.")


# Initialize and migrate on first import
init_db()
migrate_json_to_sqlite()
