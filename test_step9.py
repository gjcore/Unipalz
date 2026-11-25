"""
test_step9.py - checks that data survives a restart.

We use a throw-away database file, so your real unipalz.db is not touched.
"""

import os
from storage.persistent import PersistentEngine

DB = "test_unipalz.db"
if os.path.exists(DB):
    os.remove(DB)

# ---------- session 1: the app is running and people use it ----------
e = PersistentEngine(DB)
e.signup("asha", "secret123", "Asha Rao", "CSE (AI)", 3, "Loves graphs",
         ["Python", "DSA"], "🐙")
for username, name in [("ravi", "Ravi Kumar"), ("meena", "Meena Iyer"),
                       ("zoya", "Zoya Khan")]:
    e.signup(username, "secret123", name)

e.send_request("ravi", "asha");  e.accept_request("asha", "ravi")   # pals
e.send_request("meena", "asha")                                     # still pending
e.send_request("zoya", "ravi");  e.cancel_request("zoya", "ravi")   # cancelled
e.send_request("zoya", "meena"); e.send_request("meena", "zoya")    # crossed -> pals

e.create_post("ravi", "ravi post 1")        # id 1 (will be deleted)
e.create_post("ravi", "ravi post 2")        # id 2
e.create_post("ravi", "ravi post 3")        # id 3
e.delete_post("ravi", 1)

e.update_profile("asha", name="Asha Rai", bio="Now loves BFS")
print("session 1: data created")

# ---------- the app is closed. A brand-new Engine starts from the file ----------
e2 = PersistentEngine(DB)

# 1. accounts and passwords survived
assert e2.login("asha", "secret123") is not None
assert e2.login("asha", "wrong") is None
user = e2.get_user("asha")
assert user.name == "Asha Rai" and user.bio == "Now loves BFS"
assert user.skills == ["Python", "DSA"] and user.year == 3 and user.avatar == "🐙"
print("1. accounts OK")

# 2. connections survived (including the crossed-request one)
assert e2.connections("asha") == ["ravi"]
assert e2.connections("zoya") == ["meena"]
print("2. connections OK")

# 3. pending request survived, cancelled one did not come back
assert e2.pending_requests("asha") == ["meena"]
assert e2.pending_requests("ravi") == []
assert e2.pending_requests("meena") == []
print("3. pending requests OK")

# 4. posts survived, deleted post stays deleted, feed works
assert [p.text for p in e2.feed("asha")] == ["ravi post 3", "ravi post 2"]
print("4. posts + feed OK")

# 5. search was rebuilt (new name works, old name does not)
assert e2.search("rai") == ["asha"] and e2.search("rao") == []
print("5. search OK")

# 6. graph algorithms work on the reloaded data
assert e2.degree("asha", "ravi") == "1st"
assert e2.degree("asha", "zoya") == "Not connected"
print("6. graph OK")

# 7. new post ids keep counting up after a restart
ok, post = e2.create_post("ravi", "after restart")
assert ok and post.id == 4
print("7. post ids continue OK")

# 8. changes made after the restart are saved too
e2.accept_request("asha", "meena")
e3 = PersistentEngine(DB)
assert e3.connections("asha") == ["meena", "ravi"]
assert len(e3.feed("asha")) == 3
print("8. second restart OK")

os.remove(DB)
print("\nAll Step 9 tests passed!")