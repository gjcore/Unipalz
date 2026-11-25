"""
test_step5.py - checks pending requests (queue + accept / reject / cancel).
"""

from core.network import Graph
from core.requests_q import RequestManager

g = Graph()
for name in ["asha", "ravi", "meena", "zoya"]:
    g.add_user(name)
rm = RequestManager(g)

# 1. send requests: they wait in the receiver's queue, in order
assert rm.send_request("ravi", "asha")[0]
assert rm.send_request("meena", "asha")[0]
assert rm.pending_for("asha") == ["ravi", "meena"]       # first come, first served
assert rm.sent_by("ravi") == ["asha"]
print("1. queue order:", rm.pending_for("asha"))

# 2. not friends yet: a request is NOT a connection
assert not g.are_connected("ravi", "asha")
print("2. pending is not a connection yet")

# 3. rules
assert not rm.send_request("asha", "asha")[0]            # self
assert not rm.send_request("ravi", "asha")[0]            # duplicate
assert not rm.send_request("ravi", "ghost")[0]           # unknown user
print("3. rules OK")

# 4. accept: request leaves the queue and a line appears in the graph
assert rm.accept("asha", "ravi")[0]
assert g.are_connected("asha", "ravi") and g.are_connected("ravi", "asha")
assert rm.pending_for("asha") == ["meena"]
assert rm.sent_by("ravi") == []
print("4. accept OK")

# 5. can't send a request to someone you are already pals with
assert not rm.send_request("asha", "ravi")[0]
print("5. already pals blocked")

# 6. reject: request disappears, no connection
assert rm.reject("asha", "meena")[0]
assert not g.are_connected("asha", "meena")
assert rm.pending_for("asha") == []
print("6. reject OK")

# 7. cancel: the sender takes it back
assert rm.send_request("zoya", "ravi")[0]
assert rm.cancel("zoya", "ravi")[0]
assert rm.pending_for("ravi") == []
assert not rm.cancel("zoya", "ravi")[0]                  # nothing left to cancel
print("7. cancel OK")

# 8. both sides asked each other: they become pals straight away
assert rm.send_request("zoya", "meena")[0]
ok, msg = rm.send_request("meena", "zoya")
assert ok and g.are_connected("zoya", "meena")
assert rm.pending_for("meena") == [] and rm.pending_for("zoya") == []
print("8. crossed requests ->", msg)

# 9. after removing a connection, a new request is allowed again
g.remove_connection("asha", "ravi")
assert rm.send_request("asha", "ravi")[0]
print("9. can ask again after removal")

print("\nAll Step 5 tests passed!")