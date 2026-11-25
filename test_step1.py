"""
test_step1.py - run this to check that users.py works.
Each 'assert' says: "this must be true, otherwise stop and complain".
"""

from core.users import UserRegistry

reg = UserRegistry()

# 1. sign up works
ok, msg = reg.signup("Asha", "secret123", "Asha Rao", "CSE (AI)", 3,
                     "Loves graphs", ["Python", "UI/UX"], "🐙")
assert ok, msg
print("1. signup OK ->", msg)

# 2. duplicate username is rejected (even with different capital letters)
ok, msg = reg.signup("ASHA", "another1", "Someone Else")
assert not ok
print("2. duplicate rejected ->", msg)

# 3. bad input is rejected
assert not reg.signup("ab", "secret123", "Too Short")[0]        # username too short
assert not reg.signup("ravi", "123", "Ravi")[0]                  # password too short
print("3. validation OK")

# 4. login: right password works, wrong one fails, unknown user fails
assert reg.login("asha", "secret123") is not None
assert reg.login("asha", "wrongpass") is None
assert reg.login("nobody", "secret123") is None
print("4. login OK")

# 5. the password is NOT stored as plain text
user = reg.get_user("asha")
assert user.password_hash != "secret123"
print("5. stored hash:", user.password_hash[:30], "...")

# 6. same password for two users gives DIFFERENT hashes (because of salt)
reg.signup("ravi", "secret123", "Ravi K")
assert reg.get_user("ravi").password_hash != user.password_hash
print("6. salt works: same password, different hashes")

# 7. profile update
reg.update_profile("asha", bio="Now loves BFS", skills=["Python", "DSA"])
assert reg.get_user("asha").bio == "Now loves BFS"
print("7. profile update OK")

print("\nAll Step 1 tests passed!")