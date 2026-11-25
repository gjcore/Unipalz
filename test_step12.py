"""
test_step12.py - checks My Pals, Yearbook (profile) and Edit profile.
"""

import os
os.environ["UNIPALZ_DB"] = "test_web12.db"
if os.path.exists("test_web12.db"):
    os.remove("test_web12.db")

from app import app

def text(r):
    return r.get_data(as_text=True)

def join(username, name):
    c = app.test_client()
    c.post("/signup", data={"username": username, "password": "secret123",
                            "name": name, "programme": "CSE", "year": "2",
                            "bio": "Bio of " + name, "skills": "Python, DSA"})
    return c

asha = join("asha", "Asha Rao")
ravi = join("ravi", "Ravi Kumar")
meena = join("meena", "Meena Iyer")

# 1. My Pals page lists incoming requests with Accept / Reject buttons
ravi.post("/request/send/asha")
page = text(asha.get("/pals"))
assert "Ravi Kumar" in page and "Pleased to meet you" in page and "Maybe later" in page
print("1. incoming request shown")

# 2. the sender sees it under 'sent', with a Cancel button
page = text(ravi.get("/pals"))
assert "Asha Rao" in page and "Cancel" in page
print("2. sent request shown")

# 3. accept: both now list each other under My Pals
asha.post("/request/accept/ravi")
assert "Ravi Kumar" in text(asha.get("/pals"))
assert "Asha Rao" in text(ravi.get("/pals"))
print("3. accept OK")

# 4. profile of a pal says '1st-degree pal' and offers Remove
page = text(asha.get("/user/ravi"))
assert "1st-degree pal" in page and "Remove pal" in page
print("4. 1st degree profile OK")

# 5. meena is ravi's pal, so for asha she is 2nd degree, with the chain shown
meena.post("/request/send/ravi"); ravi.post("/request/accept/meena")
page = text(asha.get("/user/meena"))
assert "2nd-degree pal" in page
assert ">You</a>" in page and "Ravi Kumar" in page and "Meena Iyer" in page
assert "Mutual pals" in page
print("5. 2nd degree + chain + mutuals OK")

# 6. a stranger shows 'Send a high-five' and 'not connected' when no path exists
zoya = join("zoya", "Zoya Khan")
page = text(asha.get("/user/zoya"))
assert "not connected yet" in page and "Send a high-five" in page
print("6. not connected OK")

# 7. cancel works from the profile page
asha.post("/request/send/zoya", data={"next": "/user/zoya"})
assert "Cancel request" in text(asha.get("/user/zoya"))
asha.post("/request/cancel/zoya")
assert "Send a high-five" in text(asha.get("/user/zoya"))
print("7. cancel OK")

# 8. remove a pal
asha.post("/remove/ravi")
assert "1st-degree" not in text(asha.get("/user/ravi"))
print("8. remove pal OK")

# 9. edit your own Yearbook
r = asha.post("/profile/edit", data={"name": "Asha R", "programme": "AI", "year": "4",
                                     "bio": "New bio here", "skills": "Graphs, BFS",
                                     "avatar": "🐙"}, follow_redirects=True)
page = text(r)
assert "Asha R" in page and "New bio here" in page and "Graphs" in page
print("9. edit profile OK")

# 10. unknown user gives a 404
assert asha.get("/user/ghost").status_code == 404
print("10. unknown profile -> 404")

os.remove("test_web12.db")
print("\nAll Step 12 tests passed!")