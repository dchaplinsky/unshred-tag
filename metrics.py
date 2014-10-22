from __future__ import division

from itertools import chain, combinations, islice, izip_longest
from app import db
from models import Shreds, ShredsDistances

BULK_INSERT_SIZE = 100000
SHREDS_CAP = 10000

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


def jaccard_distances_iterator(shreds_tags, input_cap=SHREDS_CAP):
    """
    You can take only first `input_cap` items from `shreds_tags` iterable.
    Usefull for debugging and test runs.
    """

    for shred_a, shred_b in combinations(islice(shreds_tags.items(), 0, input_cap), 2):
        shred_a_id, tags_a = shred_a
        shred_b_id, tags_b = shred_b
        yield shred_a_id, shred_b_id, jaccard_distance(tags_a, tags_b)


def fetch_normalized_shreds_tags():
    """
    Returns dictionary where keys are shreds ids and values are sets of
    filtered(soon) normalized tags.
    """
    shreds = Shreds.objects().only('id', 'tags.tags')
    shreds_tags = {}
    for s in shreds:
        # TODO: Add filtering and extract as Shreds.filtered_normalized_tags method/property
        shreds_tags[s.id] = set(map(lambda _: unicode(_.lower()), chain(*[st.tags for st in s.tags])))
    return shreds_tags


def churn_jaccard():
    """
    We'll be working with pre-created list of ShredsDistances documents - s_distances
    This way we don't spend CPU cycles & mallocs to create millions of
    objects to be thrown away.

    It would be even more efficient to not create these documents at all
    and insert raw data into mongo, but I haven't dug deep enough.
    """

    shreds_tags = fetch_normalized_shreds_tags()
    s_distances = [ShredsDistances() for _ in xrange(BULK_INSERT_SIZE)]

    for distances in grouper(BULK_INSERT_SIZE, jaccard_distances_iterator(shreds_tags)):
        for i, dist in enumerate(distances):
            if dist:
                a, b, d = dist

                # assign data to pre-created ShredsDistances document
                s_d = s_distances[i]
                s_d.shreds_pair = [a, b]
                s_d.distance = d
                s_d.distance_type = 'jaccard'
            else:
                # Cut the tail of pre-created documents from last bulk set
                s_distances[i] = None
        ShredsDistances.objects.insert(filter(None, s_distances), load_bulk=False)


if __name__ == '__main__':
    churn_jaccard()
