"""
interactions.py  -  Likes and comments (with replies)

DSA used:
  LIKES    -> a SET of usernames for every post
              likes[post_id] = {"asha", "ravi"}
              A set makes "like / unlike" O(1) and makes it IMPOSSIBLE to
              like the same post twice.

  COMMENTS -> a TREE
              Each comment keeps a list of its replies, and replies can have
              replies of their own:

                  post 7
                   +-- comment A
                   |     +-- reply A1
                   |     |     +-- reply A1a
                   |     +-- reply A2
                   +-- comment B

              comments[post_id] holds the top-level comments (the roots).
              by_id[comment_id] is a hash table for jumping straight to any
              comment (needed to reply to it or delete it).
"""

import time


class Comment:
    """One node of the tree."""

    def __init__(self, comment_id, post_id, author, text,
                 parent_id=None, created_at=None):
        self.id = comment_id
        self.post_id = post_id
        self.author = author
        self.text = text
        self.parent_id = parent_id          # None = top-level comment
        self.created_at = created_at if created_at is not None else time.time()
        self.replies = []                   # the children of this node


class Interactions:

    MAX_LENGTH = 300

    def __init__(self):
        self.likes = {}         # post_id -> set of usernames
        self.comments = {}      # post_id -> list of top-level Comments
        self.by_id = {}         # comment_id -> Comment (hash table)
        self.counts = {}        # post_id -> number of comments, replies included
        self.next_id = 1

    # ---------------- likes ----------------

    def toggle_like(self, post_id, username):
        """Like if not liked yet, otherwise unlike. Returns True if the post
        is liked NOW, False if it was just unliked."""
        who = self.likes.setdefault(post_id, set())
        if username in who:
            who.remove(username)
            return False
        who.add(username)
        return True

    def restore_like(self, post_id, username):
        self.likes.setdefault(post_id, set()).add(username)

    def like_count(self, post_id):
        return len(self.likes.get(post_id, ()))

    def has_liked(self, post_id, username):
        return username in self.likes.get(post_id, ())

    # ---------------- comments ----------------

    def add_comment(self, post_id, author, text, parent_id=None):
        """Add a top-level comment, or a reply when parent_id is given.
        Returns (True, the Comment) or (False, reason)."""
        text = text.strip()
        if not text:
            return False, "A comment can't be empty"
        if len(text) > self.MAX_LENGTH:
            return False, "Comments can be at most 300 characters"

        parent = None
        if parent_id is not None:
            parent = self.by_id.get(parent_id)
            if parent is None or parent.post_id != post_id:
                return False, "That comment no longer exists"

        comment = Comment(self.next_id, post_id, author, text, parent_id)
        self.next_id += 1
        self._attach(comment, parent)
        return True, comment

    def _attach(self, comment, parent):
        """Hang the new node on the tree: under its parent, or as a root."""
        if parent is None:
            self.comments.setdefault(comment.post_id, []).append(comment)
        else:
            parent.replies.append(comment)
        self.by_id[comment.id] = comment
        self.counts[comment.post_id] = self.counts.get(comment.post_id, 0) + 1

    def restore_comment(self, comment):
        """Put back a comment loaded from the database. Comments must be
        restored in increasing id order, so a parent always comes first."""
        parent = None
        if comment.parent_id is not None:
            parent = self.by_id.get(comment.parent_id)
            if parent is None:
                return                      # its parent is gone: skip it
        self._attach(comment, parent)
        if comment.id >= self.next_id:
            self.next_id = comment.id + 1

    def comments_for(self, post_id):
        """The top-level comments of a post, oldest first (each has .replies)."""
        return list(self.comments.get(post_id, []))

    def comment_count(self, post_id):
        return self.counts.get(post_id, 0)

    def subtree_ids(self, comment_id):
        """The ids of a comment and everything below it (walk down the tree)."""
        start = self.by_id.get(comment_id)
        if start is None:
            return []
        ids = []
        stack = [start]
        while stack:
            node = stack.pop()
            ids.append(node.id)
            stack.extend(node.replies)
        return ids

    def delete_comment(self, comment_id, username):
        """Delete your own comment. Its replies go with it (the whole branch).
        Returns (True/False, message)."""
        comment = self.by_id.get(comment_id)
        if comment is None:
            return False, "Comment not found"
        if comment.author != username:
            return False, "You can only delete your own comments"

        ids = self.subtree_ids(comment_id)
        if comment.parent_id is None:
            self.comments[comment.post_id].remove(comment)
        else:
            self.by_id[comment.parent_id].replies.remove(comment)
        for cid in ids:
            del self.by_id[cid]
        self.counts[comment.post_id] -= len(ids)
        return True, "Comment deleted"

    def remove_post(self, post_id):
        """When a post is deleted, throw away its likes and all its comments."""
        self.likes.pop(post_id, None)
        for root in self.comments.pop(post_id, []):
            for cid in self.subtree_ids(root.id):
                del self.by_id[cid]
        self.counts.pop(post_id, None)