"""
test_step2.py - checks that network.py works.

We build this little map:

    asha --- ravi --- meena
      |                 |
      +----- kiran -----+          zoya (no pals yet)
"""

from core.network import Graph

g = Graph()
for name in ["asha", "ravi", "meena", "kiran", "zoya"]:
    g.add_user(name)

# 1. add connections
assert g.add_connection("asha", "ravi")[0]
assert g.add_connection("ravi", "meena")[0]
assert g.add_connection("asha", "kiran")[0]
assert g.add_connection("kiran", "meena")[0]
print("1. connections added")

# 2. it is undirected: both sides know each other
assert g.are_connected("asha", "ravi")
assert g.are_connected("ravi", "asha")
print("2. undirected OK")

# 3. rules: no self edge, no duplicate, no unknown user
assert not g.add_connection("asha", "asha")[0]
assert not g.add_connection("asha", "ravi")[0]
assert not g.add_connection("ravi", "asha")[0]      # duplicate the other way round
assert not g.add_connection("asha", "ghost")[0]
print("3. rules OK")

# 4. list pals and count them
assert g.connections("asha") == ["kiran", "ravi"]
assert g.connection_count("zoya") == 0
print("4. asha's pals:", g.connections("asha"))

# 5. mutual pals: asha and meena both know ravi and kiran
assert g.mutual_connections("asha", "meena") == ["kiran", "ravi"]
assert g.mutual_connections("asha", "zoya") == []
print("5. mutual pals of asha and meena:", g.mutual_connections("asha", "meena"))

# 6. remove a connection
assert g.remove_connection("asha", "ravi")[0]
assert not g.are_connected("asha", "ravi")
assert not g.are_connected("ravi", "asha")
assert not g.remove_connection("asha", "ravi")[0]   # already gone
print("6. removal OK")

print("\nAll Step 2 tests passed!")