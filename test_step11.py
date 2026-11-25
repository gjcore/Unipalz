"""
test_step11.py - checks the Bulletin Board: posts, feed, requests, Introductions.
Uses a throw-away database.
"""

import os
os.environ["UNIPALZ_DB"] = "test_web11.db"
if os.path.exists("test_web11.db"):
    os.remove("test_web11.db")

from app import app

def text(r):
    return r.get_data(as_text=True)

def join(username, name):
    c = app.test_client()
    c.post("/signup", data={"username": username, "password": "secret123",
                            "name": name, "year": "2"})
    return c

asha = join("asha", "Asha Rao")
ravi = join("ravi", "Ravi Kumar")
meena = join("meena", "Meena Iyer")

# 1. empty board message
assert "Nothing pinned yet" in text(asha.get("/"))
print("1. empty board OK")

# 2. ravi sends a request, asha accepts: they are pals
assert "Request sent" in text(ravi.post("/request/send/asha", follow_redirects=True))
asha.post("/request/accept/ravi")
print("2. request + accept OK")

# 3. ravi pins two posts; asha sees them, NEWEST FIRST (the heap merge)
ravi.post("/post", data={"text": "Hello from Ravi"})
ravi.post("/post", data={"text": "Second post"})
page = text(asha.get("/"))
assert "Hello from Ravi" in page and "Second post" in page
assert page.index("Second post") < page.index("Hello from Ravi")
print("3. feed shows pal's posts, newest first")

# 4. empty posts are refused
r = ravi.post("/post", data={"text": "   "}, follow_redirects=True)
assert "empty" in text(r)
print("4. empty post refused")

# 5. you can only delete your own post (post id 1 is ravi's)
asha.post("/post/1/delete")
assert "Hello from Ravi" in text(asha.get("/"))
ravi.post("/post/1/delete")
assert "Hello from Ravi" not in text(asha.get("/"))
print("5. delete only your own posts")

# 6. Introductions: meena is a pal of ravi, so asha is introduced to meena
meena.post("/request/send/ravi"); ravi.post("/request/accept/meena")
page = text(asha.get("/"))
assert "Meena Iyer" in page and "Send a high-five" in page
print("6. introductions OK")

# 7. after asha sends a high-five, meena leaves the list
assert "Request sent" in text(asha.post("/request/send/meena", data={"next": "/"},
                                        follow_redirects=True))
assert "Send a high-five" not in text(asha.get("/"))
print("7. pending request hides the suggestion")

# 8. the pending badge appears for meena
assert 'class="badge"' in text(meena.get("/"))
print("8. pending badge OK")

# 9. logged-out visitors are sent to login
r = app.test_client().post("/post", data={"text": "hi"})
assert r.status_code == 302 and "/login" in r.headers["Location"]
print("9. login required")

os.remove("test_web11.db")
print("\nAll Step 11 tests passed!")