from __future__ import division

from itertools import chain, combinations, islice, izip_longest
from app import db
from models import Shreds, ShredsDistances

BULK_INSERT_SIZE = 1000
SHREDS_CAP = 1000

# Performance stats
# 100 shreds -> 8 sec
# 1000 shreds -> 3 min
# 2800 shreds -> 24 min


def grouper(n, iterable, fillvalue=None):
    """Collect data into fixed-length chunks or blocks, so
    grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx

    http://docs.python.org/3.4/library/itertools.html#itertools-recipes

    Shameless copypaste from https://github.com/kachayev/fn.py/blob/master/fn/iters.py#L113
    """
    args = [iter(iterable)] * n
    return izip_longest(*args, fillvalue=fillvalue)


def jaccard_distance(tags_a, tags_b):
    """
    0 <= J <= 1
    0 - tags_a & tags_a sets are equal
    1 - tags_a have nothing in common with tags_b

    See http://en.wikipedia.org/wiki/Jaccard_index for details
    """
    return 1 - len(tags_a.intersection(tags_b)) / len(tags_a.union(tags_b))


def jaccard_distances_iterator(shreds_tags):
    for shred_a, shred_b in combinations(islice(shreds_tags.items(), 0, SHREDS_CAP), 2):
        shred_a_id, tags_a = shred_a
        shred_b_id, tags_b = shred_b
        yield shred_a_id, shred_b_id, jaccard_distance(tags_a, tags_b)


def fetch_normalized_shreds_tags():
    """
    Returns dictionary where keys are shreds ids and values are sets of
    filtered(soon) normalized tags.
    """
    shreds = Shreds.objects().only('id', 'tags.tags')
    # import ipdb; ipdb.set_trace()
    shreds_tags = {}
    for s in shreds:
        # TODO: Add filtering and extract as Shreds.filtered_normalized_tags method/property
        shreds_tags[s.id] = set(map(lambda _: unicode(_.lower()), chain(*[st['tags'] for st in s.tags])))
    return shreds_tags


def churn_jaccard():
    shreds_tags = fetch_normalized_shreds_tags()
    for distances in grouper(BULK_INSERT_SIZE, jaccard_distances_iterator(shreds_tags)):
        s_distances = []
        # import ipdb; ipdb.set_trace()
        for dist in distances:
            if dist:
                a, b, d = dist
                s_distances.append(ShredsDistances(shreds_pair=[a, b], distance=d, distance_type='jaccard'))
        ShredsDistances.objects.insert(s_distances, load_bulk=True)


if __name__ == '__main__':
    churn_jaccard()
