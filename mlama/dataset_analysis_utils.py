import re
import json
import math
from pathlib import Path
from natsort import natsorted
from collections import Counter


def load_wikidata_predicates_names():
    """Load Wikidata predicate names."""

    with open("data/wikidata-predicates.json", "r") as f:
        data = json.load(f)
        relation_id_to_name = {k: v for k, v in data["rows"]}

    return relation_id_to_name


def load_jsonl_file(filename):
    with open(filename, "r") as f:
        return [json.loads(l) for l in f]


def load_predicates_in_dataset(dataset_dir):
    """Load the list of predicates within a dataset."""
    dataset_files = [f.name for f in Path(dataset_dir).glob("P*")]
    predicates = [re.findall(r"^P\d+", f)[0] for f in dataset_files]
    # TODO: Don't ignore P527
    return natsorted(set([p for p in predicates if p != "P527"]))


def normalize_region_name(region):
    """Unify subregion names into a single normalized name."""
    # TODO: Fix this!
    if any([r in region for r in ["ASIA", "JAPAN", "CHINA"]]):
        return "ASIA"
    if "ARAB" in region:
        return region
    if "SOUTH_AMERICA" in region:
        return "SOUTH_AMERICA"
    return "WEST"


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


def compute_subject_entropy(relation_triples):
    """Compute the least possible entropy for a relation triple."""
    # TODO: Fix this!
    #  Form the object counts (based on the uris!)
    countries_uris = Counter([triple["country"][0] for triple in relation_triples])
    # countries_uris = Counter(
    #     [uri[0] for triple in relation_triples for uri in triple["country"]]
    # )

    #  Compute the probabilities of these objects
    countries_counts = [t[1] for t in countries_uris.most_common()]
    n_countries = sum(countries_counts)
    assert n_countries == len(relation_triples)
    p_countries = [
        country_count[1] / n_countries for country_count in countries_uris.most_common()
    ]

    #  Compute the entropy
    entropy = sum([-p * math.log(p, 2) for p in p_countries])
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
