"""Implements tfidf metric computing routines."""
import collections
import math


def get_tf_idf_vector(tags, all_terms, idf_map):
    """Computes a tf-idf vector for a given set of tags.

    Args:
        tags: list of string object tags.

        all_terms: global list of all known terms
        idf_map: string->float idf map.

    Returns:
        List of float tf-idf vector coordinates.
    """
    return [(1 if term in tags else 0) * idf_map[term] for term in all_terms]


def compute_one_tfidf_distance(arg):
    """Computes a distance between a pair of clusters.

    Args:
        arg: ComputeDistanceArg instance.

    Returns:
        3-tuple (a_id, b_id, distance).
    """
    all_terms = arg.global_state['all_terms']
    idf_map = arg.global_state['idf_map']

    vec_a = get_tf_idf_vector(arg.tags_a, all_terms, idf_map)
    vec_b = get_tf_idf_vector(arg.tags_b, all_terms, idf_map)
    # Cosine of angle between term vectors.
    dot_product = sum(x * y for x, y in zip(vec_a, vec_b))
    norms_product = (math.sqrt(sum(x*x for x in vec_a)) *
                     math.sqrt(sum(y*y for y in vec_b)))
    return (arg.shred_a_id, arg.shred_b_id, 1 -  dot_product / norms_product)


def make_global_state(self, shreds_tags):
    """Precomputes TF-DF global state.

    Args:
        shreds_tags: dict {obj_id: [tags]}

    Returns:
        A dict with two keys: 'idf_map' and 'all_terms'. idf_map maps terms to
            their idf values. all_terms is a sorted list of all terms.
    """
    doc_counts = collections.defaultdict(int)

    for doc, tags in shreds_tags.items():
        for tag in tags:
            doc_counts[tag] += 1

    num_docs = float(len(shreds_tags))

    idf = {}
    for tag, count in doc_counts.items():
        idf[tag] = math.log(num_docs / count)
    return {
        'idf_map': idf,
        'all_terms': sorted(idf.keys()),
    }

