"""
suggestions.py  -  Step 4: "Introductions" (people you may know)

DSA used: graph traversal (pals of pals) + SETS + a similarity score + sorting

Idea in plain words:
  1. Candidates = pals of my pals who are NOT already my pals (and not me).
     This is the same as running BFS but stopping after 2 steps.
  2. Score each candidate with JACCARD'S COEFFICIENT:
         score = (pals we share) / (all different pals we two have together)
     score 1.0 means identical circles, 0 means nothing in common.
  3. Sort: highest score first (ties: more shared pals, then A-Z).
"""


def people_you_may_know(graph, username, limit=5):
    """Return a list of (candidate, mutual_count, score), best first.
    graph is a Graph object from network.py."""
    if username not in graph.adj:
        return []

    my_pals = graph.adj[username]            # a set

    # 1. find candidates: pals of pals, minus me, minus people I already know
    candidates = set()
    for pal in my_pals:
        for friend_of_pal in graph.adj[pal]:
            if friend_of_pal != username and friend_of_pal not in my_pals:
                candidates.add(friend_of_pal)

    # 2. score every candidate with Jaccard
    scored = []
    for person in candidates:
        their_pals = graph.adj[person]
        mutual = len(my_pals & their_pals)       # & = intersection (shared pals)
        total = len(my_pals | their_pals)        # | = union (everyone either knows)
        score = mutual / total
        scored.append((person, mutual, round(score, 2)))

    # 3. sort: best score first, then most mutual pals, then name A-Z
    scored.sort(key=lambda item: (-item[2], -item[1], item[0]))
    return scored[:limit]