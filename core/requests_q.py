"""
requests_q.py  -  Step 5: Pending connection requests

DSA used: QUEUES (collections.deque) + a SET

A pending request is a ONE-WAY arrow (sender -> receiver) that waits until the
receiver accepts or rejects it. Only when it is accepted does it become a real,
two-way line in the graph.

We keep two structures:
  incoming[receiver] = QUEUE of senders, oldest request first (FIFO)
       -> "who is waiting for my answer?"
  outgoing[sender]   = SET of receivers
       -> "who have I asked?"  and  O(1) check for duplicate requests / cancel
"""

from collections import deque


class RequestManager:
    """Handles send, accept, reject and cancel. Works together with a Graph."""

    def __init__(self, graph):
        self.graph = graph        # the Graph from network.py
        self.incoming = {}        # receiver -> deque of senders
        self.outgoing = {}        # sender   -> set of receivers

    # ---------- helpers ----------

    def has_pending(self, sender, receiver):
        """Is there a waiting request from sender to receiver? O(1)."""
        return receiver in self.outgoing.get(sender, set())

    def _remove(self, sender, receiver):
        """Take a request out of BOTH structures. Returns True if it existed."""
        if not self.has_pending(sender, receiver):
            return False
        self.incoming[receiver].remove(sender)     # leave the queue
        self.outgoing[sender].remove(receiver)     # leave the set
        return True

    # ---------- the five actions ----------

    def send_request(self, sender, receiver):
        """Send a high-five. Returns (True/False, message)."""
        if sender == receiver:
            return False, "You can't send a request to yourself"
        if sender not in self.graph.adj or receiver not in self.graph.adj:
            return False, "User not found"
        if self.graph.are_connected(sender, receiver):
            return False, "You are already pals"
        if self.has_pending(sender, receiver):
            return False, "Request already sent"

        # the other person already asked us? Then both want it: connect them now.
        if self.has_pending(receiver, sender):
            self._remove(receiver, sender)
            self.graph.add_connection(sender, receiver)
            return True, "They had already sent you a request, so you are now pals"

        # normal case: join the back of the receiver's queue
        self.incoming.setdefault(receiver, deque()).append(sender)
        self.outgoing.setdefault(sender, set()).add(receiver)
        return True, "Request sent"

    def accept(self, receiver, sender):
        """Pleased to meet you! The receiver accepts: the arrow becomes a line."""
        if not self._remove(sender, receiver):
            return False, "No such request"
        self.graph.add_connection(sender, receiver)
        return True, "You are now pals"

    def reject(self, receiver, sender):
        """Maybe later. The receiver declines: the request just disappears."""
        if not self._remove(sender, receiver):
            return False, "No such request"
        return True, "Request declined"

    def cancel(self, sender, receiver):
        """The sender changes their mind and takes the request back."""
        if not self._remove(sender, receiver):
            return False, "No such request"
        return True, "Request cancelled"

    # ---------- questions we can ask ----------

    def pending_for(self, username):
        """Senders waiting for username's answer, oldest first (queue order)."""
        return list(self.incoming.get(username, []))

    def sent_by(self, username):
        """People username has asked and is still waiting on (A-Z)."""
        return sorted(self.outgoing.get(username, set()))