"""
db.py  -  The storeroom (SQLite)

This file ONLY saves and loads data. It does no graph thinking: no BFS, no
suggestions, no feed. Those all happen in memory, in the core/ files.

Tables:
  users        one row per student
  connections  one row per accepted friendship (stored once, a < b)
  requests     one row per pending request (id keeps the queue order)
  posts        one row per post (image = file name of an uploaded photo)
  likes        one row per (post, user) like
  comments     one row per comment or reply (parent_id = the comment replied to)
"""

import json
import sqlite3

from core.users import User
from core.posts import Post
from core.interactions import Comment


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
    created_at REAL,
    image      TEXT
);
CREATE TABLE IF NOT EXISTS likes (
    post_id  INTEGER NOT NULL,
    username TEXT NOT NULL,
    PRIMARY KEY (post_id, username)
);
CREATE TABLE IF NOT EXISTS comments (
    id         INTEGER PRIMARY KEY,
    post_id    INTEGER NOT NULL,
    author     TEXT NOT NULL,
    text       TEXT NOT NULL,
    parent_id  INTEGER,
    created_at REAL
);
"""


class Database:

    def __init__(self, path="unipalz.db"):
        self.path = path
        conn = sqlite3.connect(self.path)
        try:
            conn.executescript(SCHEMA)      # create the tables if they are missing
            # a database made by an older version has no 'image' column: add it
            columns = [row[1] for row in conn.execute("PRAGMA table_info(posts)")]
            if "image" not in columns:
                conn.execute("ALTER TABLE posts ADD COLUMN image TEXT")
            conn.commit()
        finally:
            conn.close()

    # ---------- tiny helpers: run commands / ask a question ----------

    def _run_many(self, commands):
        """Run several commands together: all of them happen, or none."""
        conn = sqlite3.connect(self.path)
        try:
            for sql, params in commands:
                conn.execute(sql, params)
            conn.commit()
        finally:
            conn.close()

    def _run(self, sql, params=()):
        self._run_many([(sql, params)])

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
        self._run("INSERT INTO posts (id, author, content, created_at, image) "
                  "VALUES (?,?,?,?,?)",
                  (post.id, post.author, post.text, post.created_at, post.image))

    def delete_post(self, post_id):
        """Delete the post together with its likes and comments."""
        self._run_many([
            ("DELETE FROM posts WHERE id=?", (post_id,)),
            ("DELETE FROM likes WHERE post_id=?", (post_id,)),
            ("DELETE FROM comments WHERE post_id=?", (post_id,)),
        ])

    def add_like(self, post_id, username):
        self._run("INSERT OR IGNORE INTO likes VALUES (?,?)", (post_id, username))

    def delete_like(self, post_id, username):
        self._run("DELETE FROM likes WHERE post_id=? AND username=?",
                  (post_id, username))

    def add_comment(self, c):
        self._run("INSERT INTO comments VALUES (?,?,?,?,?,?)",
                  (c.id, c.post_id, c.author, c.text, c.parent_id, c.created_at))

    def delete_comments(self, comment_ids):
        self._run_many([("DELETE FROM comments WHERE id=?", (cid,))
                        for cid in comment_ids])

    # ---------- loading (runs once, when the app starts) ----------

    def load_into(self, engine):
        """Read everything from the database and rebuild the in-memory
        structures (hash table, graph, queues, post lists, trie, likes, tree)."""

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
        for post_id, author, content, created_at, image in self._query(
                "SELECT id, author, content, created_at, image "
                "FROM posts ORDER BY id"):
            engine.posts.restore_post(Post(post_id, author, content,
                                           created_at, image))

        # likes -> one set per post
        for post_id, username in self._query("SELECT post_id, username FROM likes"):
            engine.interactions.restore_like(post_id, username)

        # comments -> the tree (parents have smaller ids, so they come first)
        for cid, post_id, author, text, parent_id, created_at in self._query(
                "SELECT id, post_id, author, text, parent_id, created_at "
                "FROM comments ORDER BY id"):
            engine.interactions.restore_comment(
                Comment(cid, post_id, author, text, parent_id, created_at))