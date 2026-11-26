"""
posts.py  -  Creating, viewing and deleting posts (text and/or a photo)

DSA used: HASH TABLES
  posts_by_user : username -> list of that user's posts (oldest first, newest LAST)
                  so the feed can merge these sorted lists cheaply (see feed.py)
  by_id         : post id  -> Post, for O(1) lookup (likes and comments need it)

Every post gets an id that only ever goes up (1, 2, 3 ...). A bigger id means
a newer post, which gives us a simple, reliable way to order posts.
"""

import time


class Post:
    """One post pinned on the Bulletin Board."""

    def __init__(self, post_id, author, text, created_at=None, image=None):
        self.id = post_id
        self.author = author
        self.text = text
        self.created_at = created_at if created_at is not None else time.time()
        self.image = image          # file name inside static/uploads, or None


class PostStore:
    """Keeps every user's posts."""

    MAX_LENGTH = 500

    def __init__(self):
        self.posts_by_user = {}     # username -> list of Post (oldest first)
        self.by_id = {}             # post id -> Post (hash table)
        self.next_id = 1            # the id the next new post will get

    def create_post(self, author, text, image=None):
        """Pin a post. Returns (True, the Post) or (False, reason).
        A post needs some text, a photo, or both."""
        text = text.strip()
        if not text and not image:
            return False, "A post can't be empty (add some text or a photo)"
        if len(text) > self.MAX_LENGTH:
            return False, "Posts can be at most 500 characters"

        post = Post(self.next_id, author, text, image=image)
        self.next_id += 1
        self.posts_by_user.setdefault(author, []).append(post)
        self.by_id[post.id] = post
        return True, post

    def restore_post(self, post):
        """Put back a post loaded from the database (keeps its old id).
        Posts must be restored in increasing id order."""
        self.posts_by_user.setdefault(post.author, []).append(post)
        self.by_id[post.id] = post
        if post.id >= self.next_id:
            self.next_id = post.id + 1

    def get_post(self, post_id):
        """Find a post by its id in O(1), or None."""
        return self.by_id.get(post_id)

    def delete_post(self, author, post_id):
        """Delete one of YOUR OWN posts. Returns (True/False, message)."""
        posts = self.posts_by_user.get(author, [])
        for i, post in enumerate(posts):
            if post.id == post_id:
                del posts[i]
                del self.by_id[post_id]
                return True, "Post deleted"
        return False, "Post not found (you can only delete your own posts)"

    def posts_of(self, username):
        """A user's posts, NEWEST first (for their Yearbook page)."""
        return list(reversed(self.posts_by_user.get(username, [])))