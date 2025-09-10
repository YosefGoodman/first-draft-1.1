"""
database.py
-----------
Handles all database operations for storing chat history with embeddings.

Instructions:
- Initialize SQLite database and tables with embedding support.
- Provide helper functions to save interactions with embeddings and retrieve
  context using similarity search.
- Support both raw text storage and vector embeddings for semantic search.
"""

import sqlite3
import time
import json
import numpy as np
from typing import List
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

DB_FILE = "database.db"
conn = None
embedding_model = None


def init_db():
    """Initialize the database and create tables if they don't exist."""
    global conn, embedding_model
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            timestamp TEXT,
            user_input TEXT,
            bot_response TEXT,
            user_input_embedding TEXT,
            bot_response_embedding TEXT,
            combined_embedding TEXT
        )
    """)
    conn.commit()

    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')


def generate_embedding(text: str) -> List[float]:
    """Generate embedding for a given text."""
    global embedding_model
    if embedding_model is None:
        embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    embedding = embedding_model.encode(text)
    return embedding.tolist()


def save_interaction(user_id: str, user_input: str, bot_response: str):
    """Save a single user-bot interaction with embeddings."""
    timestamp = str(time.time())

    user_embedding = generate_embedding(user_input)
    bot_embedding = generate_embedding(bot_response)
    combined_text = f"User: {user_input} Bot: {bot_response}"
    combined_embedding = generate_embedding(combined_text)

    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO conversations
           (user_id, timestamp, user_input, bot_response,
            user_input_embedding, bot_response_embedding, combined_embedding)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, timestamp, user_input, bot_response,
         json.dumps(user_embedding), json.dumps(bot_embedding),
         json.dumps(combined_embedding))
    )
    conn.commit()


def get_recent_context(user_id: str, limit: int = 5) -> List[str]:
    """Fetch the last 'limit' messages for a user as context (fallback)."""
    cursor = conn.cursor()
    cursor.execute(
        """SELECT user_input, bot_response FROM conversations
           WHERE user_id=? ORDER BY timestamp DESC LIMIT ?""",
        (user_id, limit)
    )
    rows = cursor.fetchall()
    # Reverse order to chronological
    rows.reverse()
    context = [f"User: {r[0]} | Bot: {r[1]}" for r in rows]
    return context


def get_similar_context(user_id: str, query: str, limit: int = 5) -> List[str]:
    """Retrieve most similar conversations using embedding-based similarity."""
    cursor = conn.cursor()
    cursor.execute(
        """SELECT user_input, bot_response, combined_embedding
           FROM conversations WHERE user_id=?
           AND combined_embedding IS NOT NULL""",
        (user_id,)
    )
    rows = cursor.fetchall()

    if not rows:
        return get_recent_context(user_id, limit)

    query_embedding = generate_embedding(query)
    query_embedding = np.array(query_embedding).reshape(1, -1)

    similarities = []
    for row in rows:
        user_input, bot_response, combined_embedding_json = row
        try:
            combined_embedding = json.loads(combined_embedding_json)
            combined_embedding = np.array(combined_embedding).reshape(1, -1)

            similarity = cosine_similarity(
                query_embedding, combined_embedding)[0][0]
            similarities.append((similarity, user_input, bot_response))
        except (json.JSONDecodeError, ValueError):
            continue

    similarities.sort(key=lambda x: x[0], reverse=True)
    top_similar = similarities[:limit]

    context = [f"User: {item[1]} | Bot: {item[2]}" for item in top_similar]
    return context


def migrate_existing_data():
    """Migrate existing conversations to include embeddings."""
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(conversations)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'user_input_embedding' not in columns:
        cursor.execute(
            "ALTER TABLE conversations ADD COLUMN user_input_embedding TEXT")
        cursor.execute(
            "ALTER TABLE conversations ADD COLUMN bot_response_embedding TEXT")
        cursor.execute(
            "ALTER TABLE conversations ADD COLUMN combined_embedding TEXT")
        conn.commit()

    cursor.execute(
        """SELECT rowid, user_input, bot_response FROM conversations
           WHERE combined_embedding IS NULL"""
    )
    rows = cursor.fetchall()

    for rowid, user_input, bot_response in rows:
        if user_input and bot_response:
            user_embedding = generate_embedding(user_input)
            bot_embedding = generate_embedding(bot_response)
            combined_text = f"User: {user_input} Bot: {bot_response}"
            combined_embedding = generate_embedding(combined_text)

            cursor.execute(
                """UPDATE conversations
                   SET user_input_embedding=?, bot_response_embedding=?,
                       combined_embedding=?
                   WHERE rowid=?""",
                (json.dumps(user_embedding), json.dumps(bot_embedding),
                 json.dumps(combined_embedding), rowid)
            )

    conn.commit()
