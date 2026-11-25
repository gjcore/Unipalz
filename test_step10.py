"""
test_step10.py - checks the signup / login / logout pages.
Uses a throw-away database, so your real unipalz.db is not touched.
"""

import os
os.environ["UNIPALZ_DB"] = "test_web.db"
if os.path.exists("test_web.db"):
    os.remove("test_web.db")

from app import app

c = app.test_client()

def text(response):
    return response.get_data(as_text=True)

# 1. public pages open
assert c.get("/login").status_code == 200
assert "Join" in text(c.get("/signup"))
print("1. login and signup pages open")

# 2. the home page needs a login
r = c.get("/")
assert r.status_code == 302 and "/login" in r.headers["Location"]
print("2. home is protected")

# 3. sign up logs you in
r = c.post("/signup", data={"username": "Asha", "password": "secret123",
           "name": "Asha Rao", "programme": "CSE (AI)", "year": "3",
           "bio": "Loves graphs", "skills": "Python, DSA", "avatar": "🐙"},
           follow_redirects=True)
assert r.status_code == 200 and "The Bulletin Board" in text(r) and "Asha Rao" in text(r)
print("3. signup works and logs you in")

# 4. logout, then home is locked again
c.get("/logout")
assert c.get("/").status_code == 302
print("4. logout works")

# 5. wrong password is refused, right password works
r = c.post("/login", data={"username": "asha", "password": "nope"})
assert "Wrong username or password" in text(r)
r = c.post("/login", data={"username": "ASHA", "password": "secret123"},
           follow_redirects=True)
assert "The Bulletin Board" in text(r) and "Asha Rao" in text(r)
print("5. login works")

# 6. duplicate username and bad input show a message
c.get("/logout")
r = c.post("/signup", data={"username": "asha", "password": "secret123", "name": "X"})
assert "taken" in text(r)
r = c.post("/signup", data={"username": "newbie", "password": "12", "name": "N"})
assert "at least 6" in text(r)
print("6. signup errors shown")

# 7. users are saved: a brand-new app process can still log in
from storage.persistent import PersistentEngine
assert PersistentEngine("test_web.db").login("asha", "secret123") is not None
print("7. saved to the database")

os.remove("test_web.db")
print("\nAll Step 10 tests passed!")