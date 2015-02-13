#!env python

from __future__ import division

from itertools import combinations
from fn.iters import grouper
from flask import Blueprint, g, redirect, render_template
from flask.ext import login

from models import ShredsDistances, User, Taggable

BULK_INSERT_SIZE = 100000
SHREDS_CAP = 10000
TAGS_REPEATS = 2


mod = Blueprint('metrics', __name__, template_folder='templates/metrics',
                url_prefix='/metrics')


@mod.route('/shred/pairs', defaults={'start': 0, 'end': 100})
@mod.route('/shred/pairs/<int:end>', defaults={'start': 0})
@mod.route('/shred/pairs/<int:start>/<int:end>')
@login.login_required
def dist_pairs(start, end):
    if not User.objects(pk=g.user.id).first()['admin']:
        redirect('/')
    dists = ShredsDistances.objects().order_by('distance')[start:end]
    return render_template('distance_pairs.html', dists=dists)


def jaccard_distance(tags_a, tags_b):
    """
    0 <= J <= 1
    0 - tags_a & tags_a sets are equal
    1 - tags_a have nothing in common with tags_b

    See http://en.wikipedia.org/wiki/Jaccard_index for details
    """
    return 1 - len(tags_a.intersection(tags_b)) / len(tags_a.union(tags_b))


def _jaccard_distances_iterator(shreds_tags):
    """Iterates over pairwise distances between given taggables.

    Args:
        shred_tags: dict {obj_id: [tags]}.

    Yields:
        3-tuples (shred_a_id, shred_b_id, distance).
    """
    for shred_a, shred_b in combinations(shreds_tags.items(), 2):
        shred_a_id, tags_a = shred_a
        shred_b_id, tags_b = shred_b
        yield shred_a_id, shred_b_id, jaccard_distance(set(tags_a), set(tags_b))


def _fetch_normalized_shreds_tags(repeats):
    """
    Returns dictionary where keys are shreds ids and values are sets of
    filtered normalized tags.
    """
    shreds = Taggable.objects().only('id', 'tags.tags')[:SHREDS_CAP]
    shreds_tags = {}
    for s in shreds:
        tags = s.get_repeated_tags(repeats)
        if tags:
            shreds_tags[s.id] = tags
    return shreds_tags


def churn_jaccard(drop=False, repeats=TAGS_REPEATS):
    """Creates ShredsDistance entries for every pair of Taggables.

    Args:
        drop: If True, clears the current data before starting.
    """
    if drop:
        ShredsDistances.objects(distance_type='jaccard').delete()

    shreds_tags = _fetch_normalized_shreds_tags(repeats=repeats)

    # Pre-create list of ShredsDistances documents. This saves some time on
    # creating and GCing instances.
    # It would be even more efficient to not create these documents at all
    # and insert raw data into mongo.
    s_distances = [ShredsDistances() for _ in xrange(BULK_INSERT_SIZE)]

    for distances in grouper(BULK_INSERT_SIZE, _jaccard_distances_iterator(shreds_tags)):
        for i, distance in enumerate(distances):
            if distance:
                # Assign data to pre-created ShredsDistances document.
                tag_a, tag_b, dist = distance
                s_d = s_distances[i]
                s_d.shreds_pair = [tag_a, tag_b]
                s_d.distance = dist
                s_d.distance_type = 'jaccard'
            else:
                # Cut the tail of pre-created documents from last bulk set
                s_distances[i] = None
        ShredsDistances.objects.insert(filter(None, s_distances), load_bulk=False)


if __name__ == '__main__':
    import app
    churn_jaccard()
