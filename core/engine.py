"""
engine.py  -  Step 8: The Engine (one front door for the whole website)

This class does almost no thinking itself. It OWNS the pieces we built and
calls them in the right order:

    users.py        -> accounts + profiles            (hash table)
    network.py      -> pals graph, BFS, mutuals       (adjacency list)
    suggestions.py  -> Introductions                  (Jaccard)
    requests_q.py   -> pending requests               (queues)
    posts.py/feed.py-> posts + Bulletin Board         (heap)
    trie.py         -> search as you type             (trie)

The website (Flask) will only ever call methods of Engine. Engine knows
nothing about HTML, Flask or the database, so a console menu could use
exactly the same methods.

Almost every method returns (True/False, message) so the website can show
the message to the user.
"""

from core.users import UserRegistry
from core.network import Graph
from core.requests_q import RequestManager
from core.posts import PostStore
from core.feed import build_feed
from core.suggestions import people_you_may_know
from core.trie import UserSearch


class Engine:

    def __init__(self):
        self.users = UserRegistry()                  # hash table of users
        self.graph = Graph()                         # adjacency lists
        self.requests = RequestManager(self.graph)   # queues of pending requests
        self.posts = PostStore()                     # each user's posts
        self.search_index = UserSearch()             # trie

    @staticmethod
    def _norm(username):
        """Usernames are stored lower-case, so 'Ravi' and 'ravi' match."""
        return username.strip().lower()

    # ================= accounts =================

    def signup(self, username, password, name, programme="", year=1,
               bio="", skills=None, avatar="🦊"):
        ok, msg = self.users.signup(username, password, name, programme,
                                    year, bio, skills, avatar)
        if ok:
            username = self._norm(username)
            self.graph.add_user(username)                    # new dot on the map
            self.search_index.add_user(username, name)       # searchable from now on
        return ok, msg

    def login(self, username, password):
        """Returns the User or None. (Flask's session remembers who is logged in.)"""
        return self.users.login(username, password)

    def get_user(self, username):
        return self.users.get_user(username)

    def update_profile(self, username, name=None, programme=None, year=None,
                       bio=None, skills=None, avatar=None):
        user = self.users.get_user(username)
        if user is None:
            return False, "User not found"
        if name is not None and not name.strip():
            return False, "Name can't be empty"
        old_name = user.name
        self.users.update_profile(username, name, programme, year,
                                  bio, skills, avatar)
        if name is not None:
            self.search_index.update_name(user.username, old_name, user.name)
        return True, "Profile updated"

    # ================= search =================

    def search(self, query, limit=10):
        """Usernames matching what has been typed so far."""
        return self.search_index.search(query, limit)

    # ================= connections =================

    def send_request(self, sender, receiver):
        return self.requests.send_request(self._norm(sender), self._norm(receiver))

    def accept_request(self, receiver, sender):
        return self.requests.accept(self._norm(receiver), self._norm(sender))

    def reject_request(self, receiver, sender):
        return self.requests.reject(self._norm(receiver), self._norm(sender))

    def cancel_request(self, sender, receiver):
        return self.requests.cancel(self._norm(sender), self._norm(receiver))

    def remove_connection(self, a, b):
        return self.graph.remove_connection(self._norm(a), self._norm(b))

    def connections(self, username):
        return self.graph.connections(self._norm(username))

    def pending_requests(self, username):
        """Requests waiting for username's answer, oldest first."""
        return self.requests.pending_for(self._norm(username))

    def sent_requests(self, username):
        return self.requests.sent_by(self._norm(username))

    def mutuals(self, a, b):
        return self.graph.mutual_connections(self._norm(a), self._norm(b))

    def degree(self, a, b):
        """'1st', '2nd', '3rd', ... or 'Not connected'."""
        return self.graph.degree_label(self._norm(a), self._norm(b))

    def chain(self, a, b):
        """Shortest chain of pals, e.g. ['asha', 'ravi', 'meena'], or None."""
        return self.graph.shortest_path(self._norm(a), self._norm(b))

    def suggestions(self, username, limit=5):
        """Introductions: pals of pals, best first, skipping people you
        already have a pending request with (in either direction)."""
        username = self._norm(username)
        ranked = people_you_may_know(self.graph, username, limit=50)
        result = []
        for person, mutual, score in ranked:
            if self.requests.has_pending(username, person):
                continue
            if self.requests.has_pending(person, username):
                continue
            result.append((person, mutual, score))
        return result[:limit]

    def relationship(self, viewer, target):
        """What should the button on target's page say?
        'self', 'pals', 'request_sent', 'request_received' or 'none'."""
        viewer, target = self._norm(viewer), self._norm(target)
        if viewer == target:
            return "self"
        if self.graph.are_connected(viewer, target):
            return "pals"
        if self.requests.has_pending(viewer, target):
            return "request_sent"
        if self.requests.has_pending(target, viewer):
            return "request_received"
        return "none"

    def profile_view(self, viewer, target):
        """Everything the Yearbook page needs, in one go."""
        user = self.users.get_user(target)
        if user is None:
            return None
        return {
            "user": user,
            "relationship": self.relationship(viewer, target),
            "degree": self.degree(viewer, target),
            "chain": self.chain(viewer, target),
            "mutuals": self.mutuals(viewer, target),
            "pals": self.graph.connection_count(user.username),
            "posts": self.posts.posts_of(user.username),
        }

    # ================= posts and feed =================

    def create_post(self, username, text):
        username = self._norm(username)
        if username not in self.users.users:
            return False, "User not found"
        return self.posts.create_post(username, text)

    def delete_post(self, username, post_id):
        return self.posts.delete_post(self._norm(username), post_id)

    def feed(self, username, limit=20):
        """The Bulletin Board: posts from your pals, newest first."""
        return build_feed(self.graph, self.posts, self._norm(username), limit)

    def posts_of(self, username):
        return self.posts.posts_of(self._norm(username))