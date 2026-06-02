"""Memoria persistente ligera basada en SQLite."""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


class MemoryManager:
    def __init__(self, db_path: str = "/tmp/terminatori_memory.db"):
        self.db_path = str(Path(db_path))
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS facts (key TEXT PRIMARY KEY, value TEXT, category TEXT DEFAULT 'general')"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS episodes (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, role TEXT, content TEXT)"
            )
            conn.commit()

    async def save_fact(self, key: str, value: str, category: str = "general") -> None:
        await asyncio.to_thread(self._save_fact_sync, key, value, category)

    def _save_fact_sync(self, key: str, value: str, category: str) -> None:
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO facts(key, value, category) VALUES (?, ?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value, category=excluded.category",
                (key, value, category),
            )
            conn.commit()

    async def get_fact(self, key: str) -> Optional[str]:
        return await asyncio.to_thread(self._get_fact_sync, key)

    def _get_fact_sync(self, key: str) -> Optional[str]:
        with self._get_conn() as conn:
            row = conn.execute("SELECT value FROM facts WHERE key = ?", (key,)).fetchone()
        return row[0] if row else None

    async def get_all_facts(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_all_facts_sync, category)

    def _get_all_facts_sync(self, category: Optional[str]) -> List[Dict[str, Any]]:
        query = "SELECT key, value, category FROM facts"
        params = ()
        if category:
            query += " WHERE category = ?"
            params = (category,)
        with self._get_conn() as conn:
            rows = conn.execute(query, params).fetchall()
        return [{"key": r[0], "value": r[1], "category": r[2]} for r in rows]

    async def save_exchange(self, session_id: str, user_content: str, assistant_content: str, tokens: int = 0) -> None:
        await asyncio.to_thread(self._save_exchange_sync, session_id, user_content, assistant_content)

    def _save_exchange_sync(self, session_id: str, user_content: str, assistant_content: str) -> None:
        with self._get_conn() as conn:
            conn.execute("INSERT INTO episodes(session_id, role, content) VALUES (?, ?, ?)", (session_id, "user", user_content))
            conn.execute("INSERT INTO episodes(session_id, role, content) VALUES (?, ?, ?)", (session_id, "assistant", assistant_content))
            conn.commit()

    async def get_recent_episodes(self, session_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._get_recent_episodes_sync, session_id, limit)

    def _get_recent_episodes_sync(self, session_id: str, limit: int) -> List[Dict[str, Any]]:
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT role, content FROM episodes WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        rows = list(reversed(rows))
        return [{"role": r[0], "content": r[1]} for r in rows]

    async def search(self, query: str) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(self._search_sync, query)

    def _search_sync(self, query: str) -> List[Dict[str, Any]]:
        like = f"%{query}%"
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT session_id, role, content FROM episodes WHERE content LIKE ? ORDER BY id DESC LIMIT 20",
                (like,),
            ).fetchall()
        return [{"session_id": r[0], "role": r[1], "content": r[2]} for r in rows]

    async def build_context(self, query: str) -> str:
        facts = await self.get_all_facts()
        matches = await self.search(query)
        fact_text = "\n".join(f"- {item['key']}: {item['value']}" for item in facts[:10])
        episode_text = "\n".join(f"- {item['role']}: {item['content']}" for item in matches[:10])
        return f"Facts:\n{fact_text}\n\nEpisodes:\n{episode_text}".strip()

    async def get_stats(self) -> Dict[str, int]:
        return await asyncio.to_thread(self._get_stats_sync)

    def _get_stats_sync(self) -> Dict[str, int]:
        with self._get_conn() as conn:
            facts = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
            episodes = conn.execute("SELECT COUNT(*) FROM episodes").fetchone()[0]
            sessions = conn.execute("SELECT COUNT(DISTINCT session_id) FROM episodes").fetchone()[0]
        return {"facts": facts, "episodes": episodes, "sessions": sessions}
