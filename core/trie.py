"""
trie.py  -  Step 6: Search with suggestions as you type

DSA used: TRIE (prefix tree)

A trie stores words one LETTER per step, so words that start the same share
the same path:

            (start)
              |
              r
              |
              a
             / \
            h   v
            |   |
            u   i  ...
            |
            l

To find everything starting with "ra":
  walk r -> a  (just 2 steps), then collect every word below that point.
The time depends on the length of the prefix, NOT on how many users exist.

We insert each user's USERNAME and every WORD of their NAME, so typing
"rao" finds "Asha Rao" and typing "ra" finds ravi, rahul, ...
"""

import re


class TrieNode:
    """One letter-box in the tree."""

    def __init__(self):
        self.children = {}        # letter -> next TrieNode
        self.usernames = set()    # users whose word ENDS exactly here


class Trie:
    """A generic prefix tree that maps words to usernames."""

    def __init__(self):
        self.root = TrieNode()

    def insert(self, word, username):
        """Walk down the word letter by letter, making boxes where missing."""
        node = self.root
        for letter in word.lower():
            if letter not in node.children:
                node.children[letter] = TrieNode()
            node = node.children[letter]
        node.usernames.add(username)      # mark: this word belongs to username

    def remove(self, word, username):
        """Un-mark a word (the empty boxes are left in place; that is harmless)."""
        node = self.root
        for letter in word.lower():
            if letter not in node.children:
                return
            node = node.children[letter]
        node.usernames.discard(username)

    def usernames_with_prefix(self, prefix):
        """Every username that has a word starting with prefix (a set)."""
        # 1. walk down the prefix
        node = self.root
        for letter in prefix.lower():
            if letter not in node.children:
                return set()              # nothing starts with this prefix
            node = node.children[letter]

        # 2. collect everything below this point (a simple depth-first walk)
        found = set()
        stack = [node]
        while stack:
            current = stack.pop()
            found |= current.usernames
            stack.extend(current.children.values())
        return found


class UserSearch:
    """Search users by username or by any word of their name."""

    def __init__(self):
        self.trie = Trie()

    @staticmethod
    def _words(username, name):
        """The words we index: the username plus each word in the name."""
        name_words = re.findall(r"[a-z0-9]+", name.lower())
        return {username.lower()} | set(name_words)

    def add_user(self, username, name):
        for word in self._words(username, name):
            self.trie.insert(word, username)

    def remove_user(self, username, name):
        for word in self._words(username, name):
            self.trie.remove(word, username)

    def update_name(self, username, old_name, new_name):
        """Call this when someone edits their profile name."""
        self.remove_user(username, old_name)
        self.add_user(username, new_name)

    def search(self, query, limit=10):
        """Usernames matching the query, A-Z.
        'ra' -> anyone with a word starting 'ra'.
        'asha r' -> must match BOTH words (asha... AND r...)."""
        words = query.lower().split()
        if not words:
            return []
        results = None
        for word in words:
            matches = self.trie.usernames_with_prefix(word)
            results = matches if results is None else results & matches
        return sorted(results)[:limit]