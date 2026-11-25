"""
test_step3.py - checks BFS: degree of connection and shortest chain.

Map:
    asha --- ravi --- meena --- dev --- nina
      |                 |
      +----- kiran -----+          zoya (no pals yet)
"""

from core.network import Graph

g = Graph()
for name in ["asha", "ravi", "meena", "kiran", "dev", "nina", "zoya"]:
    g.add_user(name)
for a, b in [("asha", "ravi"), ("ravi", "meena"), ("asha", "kiran"),
             ("kiran", "meena"), ("meena", "dev"), ("dev", "nina")]:
    g.add_connection(a, b)

# 1. shortest chains
assert g.shortest_path("asha", "ravi") == ["asha", "ravi"]
print("1. asha -> meena:", g.shortest_path("asha", "meena"))
assert len(g.shortest_path("asha", "meena")) == 3      # 2 lines, 3 people
chain = g.shortest_path("asha", "nina")      # two equally short chains exist (via ravi or kiran)
assert len(chain) == 5 and chain[0] == "asha" and chain[-1] == "nina"
print("   asha -> nina :", g.shortest_path("asha", "nina"))

# 2. degrees
assert g.degree_of_connection("asha", "ravi") == 1
assert g.degree_of_connection("asha", "meena") == 2
assert g.degree_of_connection("asha", "dev") == 3
assert g.degree_of_connection("asha", "asha") == 0
print("2. degrees OK")

# 3. labels for the website
assert g.degree_label("asha", "ravi") == "1st"
assert g.degree_label("asha", "meena") == "2nd"
assert g.degree_label("asha", "dev") == "3rd"
assert g.degree_label("asha", "nina") == "4th"
print("3. labels OK")

# 4. not connected / unknown users
assert g.shortest_path("asha", "zoya") is None
assert g.degree_label("asha", "zoya") == "Not connected"
assert g.shortest_path("asha", "ghost") is None
print("4. no path handled OK")

# 5. works both ways
assert g.degree_of_connection("nina", "asha") == 4
print("5. symmetric OK")

print("\nAll Step 3 tests passed!")