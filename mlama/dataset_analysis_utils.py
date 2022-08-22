import math
from natsort import natsorted
from collections import Counter


def compute_entropy(relation_triples):
    """Compute the least possible entropy for a relation triple."""
    #  Form the object counts (based on the uris!)
    obj_uris = Counter(
        [uri for triple in relation_triples for uri in triple["obj_uri"]]
    )

    #  Find the most common object for each triple
    #  In case of a tie, pick the one with the least uri value
    triples_most_common_obj = [
        natsorted([(-obj_uris[uri], uri) for uri in triple["obj_uri"]])[0][-1]
        for triple in relation_triples
    ]

    #  Compute the probabilities of these objects
    objs_counts = [t[1] for t in Counter(triples_most_common_obj).most_common()]
    assert sum(objs_counts) == len(relation_triples)
    n_objects = sum(objs_counts)
    p_objs = [obj_count / n_objects for obj_count in objs_counts]

    #  Compute the entropy
    entropy = sum([-p * math.log(p, 2) for p in p_objs])
    return entropy


def find_most_common_object(relation_triples):
    """Find the most common object within a list of relation triples."""

    return Counter(
        [
            (uri, obj_label)
            for triple in relation_triples
            for uri, obj_label in zip(triple["obj_uri"], triple["obj_label"])
        ]
    ).most_common()[0][0][1]
