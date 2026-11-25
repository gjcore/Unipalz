"""
test_step13.py - checks search and the suggestions-as-you-type API (the trie).
"""

import os
os.environ["UNIPALZ_DB"] = "test_web13.db"
if os.path.exists("test_web13.db"):
    os.remove("test_web13.db")

from app import app

def text(r):
    return r.get_data(as_text=True)

def join(username, name):
    c = app.test_client()
    c.post("/signup", data={"username": username, "password": "secret123", "name": name})
    return c

asha = join("asha", "Asha Rao")
join("ravi", "Ravi Kumar")
join("rahul", "Rahul Sharma")
join("meena", "Meena Iyer")

# 1. the typeahead API (JSON) uses the trie
data = asha.get("/api/search?q=ra").get_json()
names = [u["username"] for u in data]
assert names == ["asha", "rahul", "ravi"]           # asha matches via 'Rao'
assert data[0]["name"] == "Asha Rao" and "avatar" in data[0]
print("1. api search:", names)

# 2. narrower prefix, empty query
assert [u["username"] for u in asha.get("/api/search?q=rah").get_json()] == ["rahul"]
assert asha.get("/api/search?q=").get_json() == []
assert asha.get("/api/search?q=zzz").get_json() == []
print("2. narrowing + empty OK")

# 3. the full search page shows results with a link to the Yearbook
page = text(asha.get("/search?q=ra"))
assert "Ravi Kumar" in page and "Rahul Sharma" in page and "View Yearbook" in page
assert "Meena" not in page
print("3. search page OK")

# 4. nothing found
assert "No one found" in text(asha.get("/search?q=zzz"))
print("4. no results message OK")

# 5. search is for logged-in users only
r = app.test_client().get("/api/search?q=ra")
assert r.status_code == 302
print("5. login required")

os.remove("test_web13.db")
print("\nAll Step 13 tests passed!")