"""
test_step4.py - checks the Introductions (people you may know).

Map:
    asha --- ravi --- meena --- dev
      |        |        |
      +-- kiran +-------+         ravi --- sam          zoya (alone)
"""

from core.network import Graph
from core.suggestions import people_you_may_know

g = Graph()
for name in ["asha", "ravi", "kiran", "meena", "dev", "sam", "zoya"]:
    g.add_user(name)
for a, b in [("asha", "ravi"), ("asha", "kiran"), ("ravi", "meena"),
             ("kiran", "meena"), ("meena", "dev"), ("ravi", "sam")]:
    g.add_connection(a, b)

result = people_you_may_know(g, "asha")
print("Introductions for asha:", result)

# 1. only pals of pals are suggested: meena and sam, NOT dev (3 steps away)
names = [person for person, mutual, score in result]
assert names == ["meena", "sam"]
print("1. only pals-of-pals suggested")

# 2. meena shares 2 pals with asha (ravi, kiran), sam shares 1 (ravi)
assert result[0] == ("meena", 2, 0.67)
assert result[1] == ("sam", 1, 0.5)
print("2. scores OK (meena 0.67, sam 0.5)")

# 3. current pals and yourself are never suggested
assert "ravi" not in names and "kiran" not in names and "asha" not in names
print("3. no existing pals or self")

# 4. nobody to suggest
assert people_you_may_know(g, "zoya") == []
assert people_you_may_know(g, "ghost") == []
print("4. empty cases OK")

# 5. the limit works
assert len(people_you_may_know(g, "asha", limit=1)) == 1
print("5. limit OK")

print("\nAll Step 4 tests passed!")