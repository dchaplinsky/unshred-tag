# Soooo lame
def unique(a):
    seen = set()
    return [seen.add(x) or x for x in a if x not in seen]
