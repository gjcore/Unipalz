"""
persistent.py  -  Step 9b: An Engine that remembers

PersistentEngine is the normal Engine plus ONE extra habit:
  after every change that worked, also write that change to SQLite.

How it works:
  1. when it starts, it loads everything from the database into memory
  2. every method is "do the normal thing (super), then save it"

All thinking still happens in memory, in the core/ files. The database is
only the storeroom. Nothing in core/ had to be changed for this.
"""

from core.engine import Engine
from storage.db import Database


class PersistentEngine(Engine):

    def __init__(self, db_path="unipalz.db"):
        super().__init__()                 # build the empty in-memory structures
        self.db = Database(db_path)
        self.db.load_into(self)            # fill them from the database

    # ---------- accounts ----------

    def signup(self, username, password, name, programme="", year=1,
               bio="", skills=None, avatar="🦊"):
        ok, msg = super().signup(username, password, name, programme,
                                 year, bio, skills, avatar)
        if ok:
            self.db.add_user(self.users.get_user(username))
        return ok, msg

    def update_profile(self, username, name=None, programme=None, year=None,
                       bio=None, skills=None, avatar=None):
        ok, msg = super().update_profile(username, name, programme, year,
                                         bio, skills, avatar)
        if ok:
            self.db.update_user(self.users.get_user(username))
        return ok, msg

    # ---------- requests and connections ----------

    def send_request(self, sender, receiver):
        ok, msg = super().send_request(sender, receiver)
        if ok:
            s, r = self._norm(sender), self._norm(receiver)
            if self.graph.are_connected(s, r):
                # crossed requests: they became pals straight away
                self.db.add_connection(s, r)
                self.db.delete_request(r, s)
            else:
                self.db.add_request(s, r)
        return ok, msg

    def accept_request(self, receiver, sender):
        ok, msg = super().accept_request(receiver, sender)
        if ok:
            r, s = self._norm(receiver), self._norm(sender)
            self.db.delete_request(s, r)
            self.db.add_connection(s, r)
        return ok, msg

    def reject_request(self, receiver, sender):
        ok, msg = super().reject_request(receiver, sender)
        if ok:
            self.db.delete_request(self._norm(sender), self._norm(receiver))
        return ok, msg

    def cancel_request(self, sender, receiver):
        ok, msg = super().cancel_request(sender, receiver)
        if ok:
            self.db.delete_request(self._norm(sender), self._norm(receiver))
        return ok, msg

    def remove_connection(self, a, b):
        ok, msg = super().remove_connection(a, b)
        if ok:
            self.db.delete_connection(self._norm(a), self._norm(b))
        return ok, msg

    # ---------- posts ----------

    def create_post(self, username, text):
        ok, result = super().create_post(username, text)
        if ok:
            self.db.add_post(result)        # result is the new Post
        return ok, result

    def delete_post(self, username, post_id):
        ok, msg = super().delete_post(username, post_id)
        if ok:
            self.db.delete_post(post_id)
        return ok, msg