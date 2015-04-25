"""Implements jaccard metric computing routines."""

def compute_one_jaccard_distance(arg):
    """Computes a distance between a pair of clusters.

    Args:
        arg: ComputeDistanceArg instance.

    Returns:
        3-tuple (a_id, b_id, distance).
    """
    distance = jaccard_distance(set(arg.tags_a), set(arg.tags_b))
    return (arg.shred_a_id, arg.shred_b_id, distance)

def jaccard_distance(tags_a, tags_b):
    """
    0 <= J <= 1
    0 - tags_a & tags_a sets are equal
    1 - tags_a have nothing in common with tags_b

    See http://en.wikipedia.org/wiki/Jaccard_index for details
    """
    return 1 - len(tags_a.intersection(tags_b)) / len(tags_a.union(tags_b))

