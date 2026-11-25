"""
network.py  -  Steps 2 and 3: The graph of pals

DSA used: GRAPH stored as an ADJACENCY LIST
  self.adj is a dict:  username -> SET of that user's pals
  Example:  {"asha": {"ravi", "kiran"}, "ravi": {"asha"}, ...}

Why a set (not a list) for the pals?
  - "are we already pals?" is O(1)
  - a set cannot hold duplicates, so no multiple edges
  - removing a pal is O(1)

The graph is UNDIRECTED: if asha is a pal of ravi, then ravi is a pal of asha,
so every connection is written into BOTH users' sets.

BFS (breadth-first search) uses a QUEUE to find the shortest chain of pals.
"""

from collections import deque   # the queue that BFS needs


class Graph:
    """The network of accepted connections between users."""

    def __init__(self):
        # THE ADJACENCY LIST: username -> set of pals
        self.adj = {}

    # ---------- users (nodes) ----------

    def add_user(self, username):
        """Add a new dot to the map (a user with no pals yet)."""
        if username not in self.adj:
            self.adj[username] = set()

    # ---------- connections (edges) ----------

    def are_connected(self, a, b):
        """True if a and b are already pals. O(1)."""
        return a in self.adj and b in self.adj[a]

    def add_connection(self, a, b):
        """Draw a line between a and b. Returns (True/False, message)."""
        if a == b:
            return False, "You can't connect with yourself"      # no self edges
        if a not in self.adj or b not in self.adj:
            return False, "User not found"
        if b in self.adj[a]:
            return False, "Already pals"                         # no multiple edges
        self.adj[a].add(b)    # a knows b ...
        self.adj[b].add(a)    # ... and b knows a (undirected)
        return True, "Connected"

    def remove_connection(self, a, b):
        """Erase the line between a and b. Returns (True/False, message)."""
        if not self.are_connected(a, b):
            return False, "You are not pals"
        self.adj[a].remove(b)
        self.adj[b].remove(a)
        return True, "Connection removed"

    # ---------- questions we can ask ----------

    def connections(self, username):
        """List of a user's pals (sorted so the output is always the same)."""
        return sorted(self.adj.get(username, set()))

    def connection_count(self, username):
        """How many pals a user has."""
        return len(self.adj.get(username, set()))

    def mutual_connections(self, a, b):
        """Pals that BOTH a and b have: the overlap of the two sets."""
        if a not in self.adj or b not in self.adj:
            return []
        return sorted(self.adj[a] & self.adj[b])    # & means set intersection

    # ---------- BFS: degree of connection and shortest chain ----------

    def shortest_path(self, source, target):
        """BFS (breadth-first search).
        Returns the shortest chain as a list, e.g. ["asha", "ravi", "meena"],
        or None if there is no way to get from source to target.

        How it works (like ripples in a pond):
          1. start at source
          2. visit all of its pals, then all THEIR pals, and so on
          3. the first time we reach target, we got there with the fewest lines
        """
        if source not in self.adj or target not in self.adj:
            return None
        if source == target:
            return [source]

        parent = {source: None}      # who we came from; also marks "visited"
        queue = deque([source])      # people waiting to be explored (FIFO)

        while queue:
            current = queue.popleft()                  # take the one waiting longest
            for pal in sorted(self.adj[current]):      # sorted = same answer every time
                if pal not in parent:                  # not visited yet
                    parent[pal] = current              # remember how we got here
                    if pal == target:
                        return self._build_path(parent, target)
                    queue.append(pal)                  # explore this pal later
        return None                                    # ran out of people: not connected

    def _build_path(self, parent, target):
        """Walk backwards from target using the parent map, then flip the list."""
        path = []
        node = target
        while node is not None:
            path.append(node)
            node = parent[node]
        path.reverse()
        return path

    def degree_of_connection(self, a, b):
        """1 = direct pal, 2 = pal of a pal, 3 = ... None = not connected at all.
        (It is just the number of lines in the shortest chain.)"""
        path = self.shortest_path(a, b)
        if path is None:
            return None
        return len(path) - 1

    def degree_label(self, a, b):
        """Friendly text for the website: "1st", "2nd", "3rd", "4th"..."""
        d = self.degree_of_connection(a, b)
        if d is None:
            return "Not connected"
        if d == 0:
            return "You"
        return {1: "1st", 2: "2nd", 3: "3rd"}.get(d, str(d) + "th")