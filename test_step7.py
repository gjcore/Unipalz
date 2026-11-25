"""
test_step7.py - checks posts and the heap-based home feed.

Pals:  asha --- ravi,  asha --- meena.   kiran is NOT asha's pal.
"""

from core.network import Graph
from core.posts import PostStore
from core.feed import build_feed

g = Graph()
for name in ["asha", "ravi", "meena", "kiran", "zoya"]:
    g.add_user(name)
g.add_connection("asha", "ravi")
g.add_connection("asha", "meena")

store = PostStore()
store.create_post("ravi", "ravi post 1")      # id 1
store.create_post("meena", "meena post 1")    # id 2
store.create_post("kiran", "kiran post 1")    # id 3  (not asha's pal)
store.create_post("ravi", "ravi post 2")      # id 4
store.create_post("meena", "meena post 2")    # id 5
store.create_post("ravi", "ravi post 3")      # id 6
store.create_post("asha", "asha post 1")      # id 7

def ids(posts):
    return [p.id for p in posts]

# 1. feed = pals' posts only, newest first (kiran and asha herself are left out)
feed = build_feed(g, store, "asha")
print("1. feed ids (newest first):", ids(feed))
assert ids(feed) == [6, 5, 4, 2, 1]

# 2. limit: just the newest few
assert ids(build_feed(g, store, "asha", limit=3)) == [6, 5, 4]
print("2. limit OK")

# 3. include your own posts if you want
assert ids(build_feed(g, store, "asha", include_self=True)) == [7, 6, 5, 4, 2, 1]
print("3. include_self OK")

# 4. no pals -> empty feed
assert build_feed(g, store, "zoya") == []
print("4. empty feed OK")

# 5. view your own posts, newest first
assert ids(store.posts_of("ravi")) == [6, 4, 1]
print("5. posts_of OK")

# 6. delete: only your own posts, and the feed updates
assert not store.delete_post("asha", 6)[0]           # id 6 is ravi's
assert store.delete_post("ravi", 6)[0]
assert ids(build_feed(g, store, "asha")) == [5, 4, 2, 1]
print("6. delete OK")

# 7. validation
assert not store.create_post("asha", "   ")[0]
assert not store.create_post("asha", "x" * 501)[0]
print("7. validation OK")

# 8. a new post jumps to the top of the feed
store.create_post("meena", "meena post 3")           # id 8
assert ids(build_feed(g, store, "asha"))[0] == 8
print("8. new post appears first")

print("\nAll Step 7 tests passed!")