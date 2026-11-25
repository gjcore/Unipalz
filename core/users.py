"""
users.py  -  Step 1: Accounts and profiles

DSA used: HASH TABLE (Python dict)
  self.users maps  username -> User object
  Looking up a user by username takes O(1) time on average,
  no matter how many users exist.

This file knows nothing about Flask, HTML or the database.
"""

import hashlib   # for password hashing
import hmac      # for safe comparison of hashes
import os        # for generating a random salt
import re        # for checking the username format


class User:
    """One student's account + profile. Just a bundle of data."""

    def __init__(self, username, password_hash, salt, name,
                 programme="", year=1, bio="", skills=None, avatar="🦊"):
        self.username = username
        self.password_hash = password_hash   # hex string, NEVER the real password
        self.salt = salt                     # hex string, random per user
        self.name = name
        self.programme = programme           # e.g. "CSE (AI)"
        self.year = year                     # 1 to 4
        self.bio = bio
        self.skills = skills if skills is not None else []   # list of strings
        self.avatar = avatar                 # an emoji


class UserRegistry:
    """Holds all users. Handles sign up, login and profile lookups."""

    PBKDF2_ROUNDS = 100_000   # how many times the hash is repeated (slows attackers)

    def __init__(self):
        # THE HASH TABLE: username -> User
        self.users = {}

    # ---------- password helpers ----------

    def _hash_password(self, password, salt_bytes):
        """Scramble a password using PBKDF2 (SHA-256) and the user's salt.
        Returns a hex string. This is one-way: you cannot get the password back."""
        digest = hashlib.pbkdf2_hmac(
            "sha256",                 # the hash algorithm
            password.encode("utf-8"), # text -> bytes
            salt_bytes,
            self.PBKDF2_ROUNDS,
        )
        return digest.hex()

    # ---------- sign up ----------

    def signup(self, username, password, name, programme="", year=1,
               bio="", skills=None, avatar="🦊"):
        """Create an account. Returns (True, message) or (False, reason)."""
        username = username.strip().lower()   # "Ravi" and "ravi" are the same user

        # 1. validate the input
        if not re.fullmatch(r"[a-z0-9_]{3,20}", username):
            return False, "Username must be 3-20 characters: letters, numbers or _"
        if len(password) < 6:
            return False, "Password must be at least 6 characters"
        if not name.strip():
            return False, "Please enter your name"

        # 2. usernames must be unique  (O(1) check thanks to the dict)
        if username in self.users:
            return False, "That username is taken"

        # 3. make a random salt and hash the password with it
        salt_bytes = os.urandom(16)
        pw_hash = self._hash_password(password, salt_bytes)

        # 4. store the new user in the hash table
        self.users[username] = User(
            username=username,
            password_hash=pw_hash,
            salt=salt_bytes.hex(),
            name=name.strip(),
            programme=programme.strip(),
            year=year,
            bio=bio.strip(),
            skills=skills,
            avatar=avatar,
        )
        return True, "Account created"

    # ---------- log in ----------

    def login(self, username, password):
        """Check credentials. Returns the User on success, or None on failure.
        (Staying logged in / logging out is handled later by Flask's session.)"""
        username = username.strip().lower()
        user = self.users.get(username)       # O(1) lookup
        if user is None:
            return None

        # hash the typed password with THIS user's salt and compare
        attempt = self._hash_password(password, bytes.fromhex(user.salt))
        # compare_digest is a timing-safe comparison (better than ==)
        if hmac.compare_digest(attempt, user.password_hash):
            return user
        return None

    # ---------- profiles ----------

    def get_user(self, username):
        """Return the User with this username, or None."""
        return self.users.get(username.strip().lower())

    def update_profile(self, username, name=None, programme=None,
                       year=None, bio=None, skills=None, avatar=None):
        """Change profile fields. Only the fields you pass are changed."""
        user = self.get_user(username)
        if user is None:
            return False
        if name is not None:
            user.name = name.strip()
        if programme is not None:
            user.programme = programme.strip()
        if year is not None:
            user.year = year
        if bio is not None:
            user.bio = bio.strip()
        if skills is not None:
            user.skills = skills
        if avatar is not None:
            user.avatar = avatar
        return True

    def all_usernames(self):
        """List of every username (handy later for the trie and search)."""
        return list(self.users.keys())