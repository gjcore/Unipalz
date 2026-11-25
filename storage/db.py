"""
db.py  -  Step 9a: The storeroom (SQLite)

This file ONLY saves and loads data. It does no graph thinking: no BFS, no
suggestions, no feed. Those all happen in memory, in the core/ files.

Tables:
  users        one row per student
  connections  one row per accepted friendship (stored once, a < b)
  requests     one row per pending request (id keeps the queue order)
  posts        one row per post
"""

import json
import sqlite3

from core.users import User
from core.posts import Post


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    username      TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    salt          TEXT NOT NULL,
    name          TEXT NOT NULL,
    programme     TEXT,
    year          INTEGER,
    bio           TEXT,
    skills        TEXT,
    avatar        TEXT
);
CREATE TABLE IF NOT EXISTS connections (
    user_a TEXT NOT NULL,
    user_b TEXT NOT NULL,
    PRIMARY KEY (user_a, user_b)
);
CREATE TABLE IF NOT EXISTS requests (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    sender   TEXT NOT NULL,
    receiver TEXT NOT NULL,
    UNIQUE (sender, receiver)
);
CREATE TABLE IF NOT EXISTS posts (
    id         INTEGER PRIMARY KEY,
    author     TEXT NOT NULL,
    content    TEXT NOT NULL,
    created_at REAL
);
"""


class Database:

    def __init__(self, path="unipalz.db"):
        self.path = path
        conn = sqlite3.connect(self.path)
        try:
            conn.executescript(SCHEMA)      # create the tables if they are missing
            conn.commit()
        finally:
            conn.close()

    # ---------- two tiny helpers: run a command / ask a question ----------

    def _run(self, sql, params=()):
        conn = sqlite3.connect(self.path)
        try:
            conn.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    def _query(self, sql, params=()):
        conn = sqlite3.connect(self.path)
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    # ---------- saving ----------

    def add_user(self, user):
        self._run("INSERT INTO users VALUES (?,?,?,?,?,?,?,?,?)",
                  (user.username, user.password_hash, user.salt, user.name,
                   user.programme, user.year, user.bio,
                   json.dumps(user.skills), user.avatar))

    def update_user(self, user):
        self._run("UPDATE users SET name=?, programme=?, year=?, bio=?, "
                  "skills=?, avatar=? WHERE username=?",
                  (user.name, user.programme, user.year, user.bio,
                   json.dumps(user.skills), user.avatar, user.username))

    def add_connection(self, a, b):
        a, b = sorted((a, b))               # store each friendship only once
        self._run("INSERT OR IGNORE INTO connections VALUES (?,?)", (a, b))

    def delete_connection(self, a, b):
        a, b = sorted((a, b))
        self._run("DELETE FROM connections WHERE user_a=? AND user_b=?", (a, b))

    def add_request(self, sender, receiver):
        self._run("INSERT OR IGNORE INTO requests (sender, receiver) VALUES (?,?)",
                  (sender, receiver))

    def delete_request(self, sender, receiver):
        self._run("DELETE FROM requests WHERE sender=? AND receiver=?",
                  (sender, receiver))

    def add_post(self, post):
        self._run("INSERT INTO posts VALUES (?,?,?,?)",
                  (post.id, post.author, post.text, post.created_at))

    def delete_post(self, post_id):
        self._run("DELETE FROM posts WHERE id=?", (post_id,))

    # ---------- loading (runs once, when the app starts) ----------

    def load_into(self, engine):
        """Read everything from the database and rebuild the in-memory
        structures (hash table, graph, queues, post lists, trie)."""

        # users -> hash table, graph nodes, trie
        for row in self._query("SELECT * FROM users"):
            (username, pw_hash, salt, name, programme,
             year, bio, skills, avatar) = row
            user = User(username, pw_hash, salt, name, programme, year,
                        bio, json.loads(skills), avatar)
            engine.users.users[username] = user
            engine.graph.add_user(username)
            engine.search_index.add_user(username, name)

        # connections -> graph edges
        for a, b in self._query("SELECT user_a, user_b FROM connections"):
            engine.graph.add_connection(a, b)

        # pending requests -> queues, oldest first (ORDER BY id)
        for sender, receiver in self._query(
                "SELECT sender, receiver FROM requests ORDER BY id"):
            engine.requests.send_request(sender, receiver)

        # posts -> each author's list, in increasing id order
        for post_id, author, content, created_at in self._query(
                "SELECT id, author, content, created_at FROM posts ORDER BY id"):
            engine.posts.restore_post(Post(post_id, author, content, created_at))