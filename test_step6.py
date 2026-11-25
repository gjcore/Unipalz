"""
test_step6.py - checks the trie search (suggestions as you type).
"""

from core.trie import UserSearch

s = UserSearch()
s.add_user("asha", "Asha Rao")
s.add_user("ravi", "Ravi Kumar")
s.add_user("rahul", "Rahul Sharma")
s.add_user("rajesh", "Rajesh Rao")
s.add_user("meena", "Meena Iyer")

# 1. prefix search: typing "ra" finds usernames AND name words starting with ra
print('"ra"  ->', s.search("ra"))
assert s.search("ra") == ["asha", "rahul", "rajesh", "ravi"]
print("1. prefix search OK")

# 2. gets narrower as you keep typing
assert s.search("raj") == ["rajesh"]
assert s.search("rav") == ["ravi"]
print("2. narrows as you type OK")

# 3. matches a surname too, and ignores capital letters
assert s.search("RAO") == ["asha", "rajesh"]
assert s.search("iyer") == ["meena"]
print("3. surname + case-insensitive OK")

# 4. several words must ALL match
assert s.search("asha r") == ["asha"]
assert s.search("rajesh ku") == []
print("4. multi-word OK")

# 5. nothing found / empty query
assert s.search("zzz") == []
assert s.search("") == []
assert s.search("   ") == []
print("5. empty cases OK")

# 6. limit
assert len(s.search("r", limit=2)) == 2
print("6. limit OK")

# 7. name change: old name stops matching, new one starts
s.update_name("ravi", "Ravi Kumar", "Ravi Nair")
assert s.search("kumar") == []
assert s.search("nair") == ["ravi"]
assert s.search("ravi") == ["ravi"]          # username still works
print("7. name update OK")

# 8. removing a user
s.remove_user("rahul", "Rahul Sharma")
assert "rahul" not in s.search("ra")
print("8. remove OK")

print("\nAll Step 6 tests passed!")