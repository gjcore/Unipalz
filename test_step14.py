"""
test_step14.py - checks likes (sets), comments (tree), photo posts and that
everything survives a restart (including an OLD database without photos).
"""

import os
import sqlite3
from core.interactions import Interactions
from core.engine import Engine
from storage.persistent import PersistentEngine

# ---------- part 1: the data structures on their own ----------
it = Interactions()

# 1. likes are a set: like, unlike, never twice
assert it.toggle_like(1, "asha") is True
assert it.toggle_like(1, "ravi") is True
assert it.like_count(1) == 2 and it.has_liked(1, "asha")
assert it.toggle_like(1, "asha") is False          # second press = unlike
assert it.like_count(1) == 1 and not it.has_liked(1, "asha")
print("1. likes (set) OK")

# 2. comments form a tree: comment -> reply -> reply to the reply
ok, a = it.add_comment(7, "asha", "Nice project!")
ok, a1 = it.add_comment(7, "ravi", "Thanks!", parent_id=a.id)
ok, a1a = it.add_comment(7, "asha", "Welcome :)", parent_id=a1.id)
ok, a2 = it.add_comment(7, "meena", "Agreed", parent_id=a.id)
ok, b = it.add_comment(7, "meena", "Second thread")
roots = it.comments_for(7)
assert [c.text for c in roots] == ["Nice project!", "Second thread"]
assert [r.text for r in roots[0].replies] == ["Thanks!", "Agreed"]
assert roots[0].replies[0].replies[0].text == "Welcome :)"
assert it.comment_count(7) == 5
print("2. comment tree OK")

# 3. rules
assert not it.add_comment(7, "asha", "   ")[0]
assert not it.add_comment(7, "asha", "x" * 301)[0]
assert not it.add_comment(7, "asha", "hi", parent_id=999)[0]       # no such parent
assert not it.add_comment(8, "asha", "hi", parent_id=a.id)[0]      # parent is on another post
print("3. comment rules OK")

# 4. deleting a comment removes its whole branch; only the author may delete
assert not it.delete_comment(a1.id, "asha")[0]                     # ravi's comment
assert it.delete_comment(a1.id, "ravi")[0]                         # takes 'Welcome :)' with it
assert it.comment_count(7) == 3
assert [r.text for r in it.comments_for(7)[0].replies] == ["Agreed"]
assert a1a.id not in it.by_id
print("4. branch delete OK")

# 5. removing a post clears its likes and comments
it.remove_post(7); it.remove_post(1)
assert it.comment_count(7) == 0 and it.comments_for(7) == [] and it.like_count(1) == 0
print("5. remove_post OK")

# ---------- part 2: through the Engine ----------
e = Engine()
e.signup("asha", "secret123", "Asha Rao")
ok, post = e.create_post("asha", "", image="abc.png")      # a photo-only post
assert ok and post.image == "abc.png"
assert not e.create_post("asha", "   ")[0]                  # nothing at all: refused
assert e.toggle_like("ravi", post.id) == (True, True)
assert e.toggle_like("ravi", 999)[0] is False               # no such post
ok, c = e.add_comment("ravi", post.id, "Cool pic")
assert ok and e.comment_count(post.id) == 1
view = e.post_view("ravi", post.id)
assert view["likes"] == 1 and view["liked"] and len(view["comments"]) == 1
e.delete_post("asha", post.id)
assert e.post_view("ravi", post.id) is None
print("6. engine OK")

# ---------- part 3: persistence ----------
DB = "test_unipalz14.db"
if os.path.exists(DB):
    os.remove(DB)
p = PersistentEngine(DB)
p.signup("asha", "secret123", "Asha Rao")
p.signup("ravi", "secret123", "Ravi Kumar")
ok, post = p.create_post("asha", "Look at this", image="pic1.png")
p.toggle_like("ravi", post.id)
p.toggle_like("asha", post.id)
p.toggle_like("asha", post.id)                               # asha unlikes again
ok, root = p.add_comment("ravi", post.id, "Great!")
ok, reply = p.add_comment("asha", post.id, "Thank you", parent_id=root.id)
ok, extra = p.add_comment("ravi", post.id, "Another one")

q = PersistentEngine(DB)                                      # the app restarts
same = q.posts.get_post(post.id)
assert same.image == "pic1.png" and same.text == "Look at this"
assert q.like_count(post.id) == 1 and q.has_liked(post.id, "ravi")
assert not q.has_liked(post.id, "asha")
tree = q.interactions.comments_for(post.id)
assert [c.text for c in tree] == ["Great!", "Another one"]
assert tree[0].replies[0].text == "Thank you"
assert q.comment_count(post.id) == 3
print("7. likes, comments and photo name survive a restart")

# deleting a comment branch is saved too
q.delete_comment("ravi", root.id)
r = PersistentEngine(DB)
assert r.comment_count(post.id) == 1
# deleting a post removes its likes and comments from the database
r.delete_post("asha", post.id)
s = PersistentEngine(DB)
assert s.posts.get_post(post.id) is None and s.comment_count(post.id) == 0
conn = sqlite3.connect(DB)
assert conn.execute("SELECT COUNT(*) FROM likes").fetchone()[0] == 0
assert conn.execute("SELECT COUNT(*) FROM comments").fetchone()[0] == 0
conn.close()
print("8. deletes are saved OK")

# ---------- part 4: an OLD database (made before photos existed) still opens ----------
OLD = "test_old14.db"
if os.path.exists(OLD):
    os.remove(OLD)
conn = sqlite3.connect(OLD)
conn.executescript("""
CREATE TABLE users (username TEXT PRIMARY KEY, password_hash TEXT NOT NULL, salt TEXT NOT NULL,
  name TEXT NOT NULL, programme TEXT, year INTEGER, bio TEXT, skills TEXT, avatar TEXT);
CREATE TABLE posts (id INTEGER PRIMARY KEY, author TEXT NOT NULL, content TEXT NOT NULL, created_at REAL);
INSERT INTO users VALUES ('asha','x','00','Asha','',1,'','[]','🦊');
INSERT INTO posts VALUES (1,'asha','old post',1.0);
""")
conn.commit(); conn.close()
old = PersistentEngine(OLD)
assert old.posts.get_post(1).text == "old post" and old.posts.get_post(1).image is None
ok, newpost = old.create_post("asha", "new one", image="n.png")
assert ok and PersistentEngine(OLD).posts.get_post(newpost.id).image == "n.png"
print("9. old database upgraded OK")

os.remove(DB); os.remove(OLD)
print("\nAll Step 14 tests passed!")