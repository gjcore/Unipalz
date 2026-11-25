"""
test_step8.py - runs a whole mini story through the Engine.
"""

from core.engine import Engine

e = Engine()

# 1. sign up five students
for username, name in [("asha", "Asha Rao"), ("ravi", "Ravi Kumar"),
                       ("meena", "Meena Iyer"), ("kiran", "Kiran Shetty"),
                       ("zoya", "Zoya Khan")]:
    ok, msg = e.signup(username, "secret123", name, "CSE (AI)", 3)
    assert ok, msg
assert not e.signup("ASHA", "secret123", "Someone")[0]        # duplicate
print("1. signup OK")

# 2. login
assert e.login("ASHA", "secret123") is not None
assert e.login("asha", "wrong") is None
print("2. login OK")

# 3. requests: send, see them waiting, accept
assert e.send_request("Ravi", "asha")[0]                      # capital letters are fine
assert e.pending_requests("asha") == ["ravi"]
assert e.relationship("asha", "ravi") == "request_received"
assert e.relationship("ravi", "asha") == "request_sent"
assert e.accept_request("asha", "ravi")[0]
assert e.relationship("asha", "ravi") == "pals"
print("3. requests OK")

# 4. build a chain: asha - ravi - meena - kiran
e.send_request("ravi", "meena");  e.accept_request("meena", "ravi")
e.send_request("meena", "kiran"); e.accept_request("kiran", "meena")
assert e.chain("asha", "kiran") == ["asha", "ravi", "meena", "kiran"]
assert e.degree("asha", "kiran") == "3rd"
assert e.degree("asha", "zoya") == "Not connected"
print("4. chain:", e.chain("asha", "kiran"), "->", e.degree("asha", "kiran"))

# 5. Introductions, and a pending request removes the person from the list
assert e.suggestions("asha") == [("meena", 1, 0.5)]
e.send_request("asha", "meena")
assert e.suggestions("asha") == []
print("5. suggestions OK")

# 6. search
assert e.search("ra") == ["asha", "ravi"]
print("6. search OK")

# 7. posts and feed
e.create_post("ravi", "Ravi's first post")
e.create_post("meena", "Meena's first post")
e.create_post("kiran", "Kiran's first post")
assert [p.author for p in e.feed("asha")] == ["ravi"]
assert [p.author for p in e.feed("ravi")] == ["meena"]
print("7. feed OK")

# 8. profile view for the Yearbook page
view = e.profile_view("asha", "kiran")
assert view["degree"] == "3rd" and len(view["chain"]) == 4
assert view["relationship"] == "none" and len(view["posts"]) == 1
assert e.profile_view("asha", "ghost") is None
print("8. profile_view OK")

# 9. changing your name updates search
assert e.update_profile("asha", name="Asha Rai")[0]
assert e.search("rai") == ["asha"] and e.search("rao") == []
assert not e.update_profile("asha", name="   ")[0]
print("9. profile update + search OK")

# 10. removing a pal changes the feed
assert e.remove_connection("asha", "ravi")[0]
assert e.feed("asha") == []
print("10. remove connection OK")

print("\nAll Step 8 tests passed!")