import re
import json
from tqdm import tqdm
from pathlib import Path
from argparse import ArgumentParser

# TODO: Avoid having this hack!
import sys

sys.path.append("./")
sys.path.append("cultlama")
from cultlama.filters import FILTERS_DICTIONARY
from cultlama.constants import WESTERN_COUNTRIES
from cultlama.utils import graceful_get_wikidata_triples, parse_sparql_results


def get_country_uri(country_name):
    return re.findall(r"Q\d+", FILTERS_DICTIONARY["region_country"][country_name])[0]


def items_belonging_to_countries(items_uris, countries_uris):
    countries_uris_str = " ".join(
        [f"wd:{country_uri}" for country_uri in countries_uris]
    )
    items_uris_str = " ".join([f"wd:{item_uri}" for item_uri in items_uris])
    sparql_query = "\n".join(
        [
            "SELECT DISTINCT ?item",
            "WHERE",
            "{",
            "   {",
            "     {",
            "       ?item wdt:P27 ?country # Country of citizenship is one of the countries listed",
            "     }",
            "     UNION",
            "     {",
            "       ?item (wdt:P131|wdt:P17)* ?country # Located in territorial entity or Country",
            "     }",
            "   } .",
            f"  VALUES ?item {{{items_uris_str}}} .",
            f"  VALUES ?country {{{countries_uris_str}}}",
            "}",
        ]
    )

    relation_triples = graceful_get_wikidata_triples(sparql_query)
    parsed_data = parse_sparql_results(relation_triples)
    items_belonging = set([d["item"] for d in parsed_data])
    return items_belonging


if __name__ == "__main__":
    parser = ArgumentParser(
        "Measure the percentage of tuples belonging to Western countries"
    )
    parser.add_argument("--dataset_dir", required=True)
    parser.add_argument("--output_stats_file", required=True)
    args = parser.parse_args()

    # Get the Wikidata URIs of the Western countries
    western_countries_names = WESTERN_COUNTRIES
    western_countries_uris = [
        get_country_uri(country_name) for country_name in western_countries_names
    ]

    # Predicates having places as subjects or objects
    place_relation_predicates = [
        "P17",
        "P19",
        "P20",
        "P27",
        #     "P30", # Continent
        "P36",
        "P47",
        "P131",
        "P159",
        "P190",  #  Sister City
        "P276",
        "P463",
        "P495",
        "P530",  # Diplomatic relation
        "P740",
        "P937",
        "P1001",
        "P1376",
    ]

    # Predicates having persons as subjects or objects
    person_relation_predicates = [
        "P39",
        "P101",
        "P103",
        "P106",
        "P108",
        "P136",
        "P140",
        "P413",
        "P1412",
    ]

    relation_predicates = place_relation_predicates + person_relation_predicates

    # Find all uris of subjects and objects
    all_uris = []
    filenames = [f for f in Path(args.dataset_dir).glob("P*.jsonl")]
    for filename in filenames:
        with open(filename, "r") as f:
            if not filename.stem in relation_predicates:
                continue
            data = [json.loads(l) for l in f]
            uris = [s["sub_uri"] for s in data] + [s["obj_uri"] for s in data]
            all_uris += uris
    all_uris = list(set(all_uris))

    # Classify the unique uris to "Western" or "Others"
    uris_dict = {}
    batch_size = 1000
    for start_index in tqdm(range(0, len(all_uris), batch_size)):
        batch_uris = all_uris[start_index : start_index + batch_size]
        uris_belonging = items_belonging_to_countries(
            batch_uris, western_countries_uris
        )
        for uri in batch_uris:
            if uri in uris_belonging:
                uris_dict[uri] = "Western"
            else:
                uris_dict[uri] = "Others"

    # Compute the statistics
    stats = []
    for filename in filenames:
        with open(filename, "r") as f:
            if not filename.stem in relation_predicates:
                continue
            data = [json.loads(l) for l in f]
        tuples = [(sample["sub_uri"], sample["obj_uri"]) for sample in data]
        tuples_within = [
            t for t in tuples if any([uris_dict[uri] == "Western" for uri in t])
        ]
        stats.append(
            {
                "predicate": filename.stem,
                "no_western": len(tuples_within),
                "no_others": len(tuples) - len(tuples_within),
            }
        )

    with open(args.output_stats_file, "w") as f:
        for stat in stats:
            f.write(json.dumps(stat, ensure_ascii=False) + "\n")
