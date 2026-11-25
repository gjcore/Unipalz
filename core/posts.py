"""
posts.py  -  Step 7a: Creating, viewing and deleting posts

DSA used: HASH TABLE of LISTS
  posts_by_user maps  username -> list of that user's posts
  Posts are appended in the order they are made, so each list is already
  sorted by time (oldest first, newest LAST). Because of this, the feed can
  merge these lists cheaply (see feed.py).

Every post gets an id that only ever goes up (1, 2, 3 ...). A bigger id means
a newer post, which gives us a simple, reliable way to order posts.
"""

import time


class Post:
    """One post pinned on the Bulletin Board."""

    def __init__(self, post_id, author, text, created_at=None):
        self.id = post_id
        self.author = author
        self.text = text
        self.created_at = created_at if created_at is not None else time.time()


class PostStore:
    """Keeps every user's posts."""

    MAX_LENGTH = 500

    def __init__(self):
        self.posts_by_user = {}     # username -> list of Post (oldest first)
        self.next_id = 1            # the id the next new post will get

    def create_post(self, author, text):
        """Pin a post. Returns (True, the Post) or (False, reason)."""
        text = text.strip()
        if not text:
            return False, "A post can't be empty"
        if len(text) > self.MAX_LENGTH:
            return False, "Posts can be at most 500 characters"

        post = Post(self.next_id, author, text)
        self.next_id += 1
        self.posts_by_user.setdefault(author, []).append(post)
        return True, post

    def restore_post(self, post):
        """Put back a post loaded from the database (keeps its old id).
        Posts must be restored in increasing id order."""
        self.posts_by_user.setdefault(post.author, []).append(post)
        if post.id >= self.next_id:
            self.next_id = post.id + 1

    def delete_post(self, author, post_id):
        """Delete one of YOUR OWN posts. Returns (True/False, message)."""
        posts = self.posts_by_user.get(author, [])
        for i, post in enumerate(posts):
            if post.id == post_id:
                del posts[i]
                return True, "Post deleted"
        return False, "Post not found (you can only delete your own posts)"

    def posts_of(self, username):
        """A user's posts, NEWEST first (for their Yearbook page)."""
        return list(reversed(self.posts_by_user.get(username, [])))