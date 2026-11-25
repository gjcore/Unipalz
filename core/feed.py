"""
feed.py  -  Step 7b: The Bulletin Board (home feed)

DSA used: MIN-HEAP (heapq)  ->  "k-way merge"

The problem:
  I have k pals. Each pal's posts are already in time order.
  I want ONE list of all their posts, newest first, but only the top few.

The slow way: put every post of every pal in one big list and sort it.
The smart way (this file):
  - Look only at each pal's NEWEST post. The newest post overall must be
    one of these k posts.
  - A heap always gives us the biggest/newest of them in O(log k).
  - Take it, then put that pal's NEXT newest post into the heap. Repeat.

Python's heapq is a MIN-heap (smallest first), so we store the id as a
negative number: the newest post (biggest id) becomes the smallest value.

Cost: O(k + n log k) to get the top n posts, instead of sorting everything.
"""

import heapq


def build_feed(graph, store, username, limit=20, include_self=False):
    """Return a list of Posts from username's pals, newest first.
    graph = Graph (who is pals with whom), store = PostStore (all posts)."""
    authors = set(graph.connections(username))
    if include_self:
        authors.add(username)

    # 1. put each author's NEWEST post into the heap
    heap = []
    for author in authors:
        posts = store.posts_by_user.get(author, [])
        if posts:
            last = len(posts) - 1                         # index of newest post
            heapq.heappush(heap, (-posts[last].id, author, last))

    # 2. repeatedly take the newest, then add that author's next-newest
    feed = []
    while heap and len(feed) < limit:
        neg_id, author, index = heapq.heappop(heap)
        posts = store.posts_by_user[author]
        feed.append(posts[index])
        if index > 0:
            heapq.heappush(heap, (-posts[index - 1].id, author, index - 1))

    return feed