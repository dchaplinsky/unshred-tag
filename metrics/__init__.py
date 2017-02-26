import collections
import multiprocessing
import logging
from itertools import combinations

from flask import Blueprint, g, redirect, render_template
import flask_login
from fn.iters import grouper

from models import User, Cluster, ShredsDistances

from . import jaccard
from . import tfidf


BULK_INSERT_SIZE = 10000
SHREDS_CAP = 10000

TAGS_REPEATS = 2

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s')

mod = Blueprint('metrics', __name__, template_folder='templates/metrics',
                url_prefix='/metrics')


@mod.route('/shred/pairs', defaults={'start': 0, 'end': 100})
@mod.route('/shred/pairs/<int:end>', defaults={'start': 0})
@mod.route('/shred/pairs/<int:start>/<int:end>')
@flask_login.login_required
def dist_pairs(start, end):
    if not User.objects(pk=g.user.id).first()['admin']:
        redirect('/')
    dists = ShredsDistances.objects().order_by('distance')[start:end]
    return render_template('distance_pairs.html', dists=dists)


# Used for passing arguments to a distance function running in a subprocess.
ComputeDistanceArg = collections.namedtuple("ComputeDistanceArg",
        "global_state shred_a_id tags_a shred_b_id tags_b")


class DistanceComputer(object):
    """Incapsulates the common behaviour for generating cluster pair distances.

    The particular distance metric is specified using two callback __init__
    arguments.
    """

    def __init__(self, type_name, prepare_global_state, compute_one_distance):
        """Constructs a DistanceComputer.

        Args:
          type_name: string name of the metric type.
          prepare_global_state: A 1-argument function that performs the
              necessary precomputations. It's called once and passed a
              dict {obj_id: [tags]}. The resulting global state is then passed
              to every distance computing call.
          compute_one_distance: A 1-argument function, which is passed
              a ComputeDistanceArg instance.
        """
        self.type_name = type_name
        self._prepare_global_state = prepare_global_state
        self._compute_one_distance = compute_one_distance

    def churn(self, drop=False, repeats=TAGS_REPEATS):
        """Creates ShredsDistance entries for every pair of Clusters.

        Args:
            drop: If True, clears the current data before starting.
            repeats: Optional int minimum number the tag should be mentioned to
                be considered.
        """
        if drop:
            # Too slow.
            #ShredsDistances.objects(distance_type=self.type_name).delete()
            ShredsDistances.drop_collection()

        shreds_tags = _fetch_normalized_shreds_tags(repeats=repeats)
        total_num_pairs = len(shreds_tags) * (len(shreds_tags) - 1) / 2

        distances = self._distances_iterator(shreds_tags)
        batches_of_distances = grouper(BULK_INSERT_SIZE, distances)
        insert_args = ((batch, self.type_name)
                       for batch in batches_of_distances)

        wrote_total = 0
        inserting_pool = multiprocessing.Pool()
        for _ in inserting_pool.imap_unordered(insert_batch, insert_args):
            wrote_total += BULK_INSERT_SIZE
            wrote_total = min(wrote_total, total_num_pairs)
            logging.info("Wrote another %d documents. Total complete: %d/%d %.2f%%",
                         BULK_INSERT_SIZE, wrote_total, total_num_pairs,
                         float(wrote_total)/total_num_pairs * 100)
        inserting_pool.close()
        inserting_pool.join()

    def _distances_iterator(self, shreds_tags):
        """Iterates over pairwise distances between given clusters.

        Args:
            shred_tags: dict {obj_id: [tags]}.

        Yields:
            3-tuples (shred_a_id, shred_b_id, distance).
        """

        global_state = self._prepare_global_state(shreds_tags)

        # Number of pairs to delegate to a single multiprocessing worker at a time.
        chunk_size = 2000

        all_pairs = combinations(shreds_tags.items(), 2)
        all_args = (ComputeDistanceArg(global_state, pair[0][0], pair[0][1],
                                                     pair[1][0], pair[1][1])
                    for pair in all_pairs)

        pool = multiprocessing.Pool()
        for chunk_distance in pool.imap_unordered(self._compute_one_distance,
                                                  all_args, chunksize=chunk_size):
            yield chunk_distance
        logging.info("Computed all distances")
        pool.close()
        pool.join()


def insert_batch(arg):
    """Inserts a bunch of ShredsDistances documents to the database.

    This supposed to be parallelized with multiprocessing.

    Args:
        distances: iterable of (cluster_1_id, cluster_2_id, distance).
    """
    distances, distance_type = arg
    documents = []
    for distance in distances:
        if not distance:
            continue
        # Assign data to pre-created ShredsDistances document.
        tag_a, tag_b, dist = distance
        s_d = ShredsDistances(shreds_pair=[tag_a, tag_b], distance=dist,
                              distance_type=distance_type)
        documents.append(s_d)
    ShredsDistances.objects.insert(documents, load_bulk=False)


def _fetch_normalized_shreds_tags(repeats):
    """Gets normalized tags for every cluster.

    Args:
        repeats: minimum number of tag occurences to be included in the result.

    Returns:
        Dict {obj_id: set(tags)} mapping cluster ids to sets of string tags.
    """

    shreds = Cluster.objects().timeout(False).only(
        'id', 'tags.tags', 'members.shred')[:SHREDS_CAP]
    shreds_tags = {}
    # TODO: on every iteration queries mongodb for
    # cluster->member->shred->auto_tags. That's too slow.
    for s in shreds:
        tags = s.get_repeated_tags(repeats)
        if tags:
            shreds_tags[s.id] = frozenset(tags)
    return shreds_tags


JaccardComputer = DistanceComputer(
        'jaccard', lambda *args: None, jaccard.compute_one_jaccard_distance)
TFIDFComputer = DistanceComputer(
        'tfidf', tfidf.make_global_state, tfidf.compute_one_tfidf_distance)


churn_jaccard = JaccardComputer.churn
churn_tfidf = TFIDFComputer.churn
