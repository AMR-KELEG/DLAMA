import os
import re
import json
import time
import argparse
from parso import parse
import requests
from tqdm import tqdm
from pathlib import Path
from pprint import pprint
from collections import Counter

ENTITY_CATEGORIES_DIR = "wikidata-instance-of/"


def load_entity_categories(wikidata_entity_id):
    """Load the categories of an entity"""
    while True:
        try:
            with open(
                str(Path(ENTITY_CATEGORIES_DIR, f"{wikidata_entity_id}.json")), "r"
            ) as f:
                data = json.load(f)
                data["id"]
            break
        except Exception as e:
            request_entity_categories(wikidata_entity_id, 0.1)
    return data


def request_entity_categories(wikidata_entity_id, wait_time_after_request=0.1):
    """Get the categories of an entity using the P31 'is_instance_of' Wikidata relation from SPARQL"""

    #  TODO: Make this function generalize to langauges other than ar, en
    URL = "https://query.wikidata.org/sparql"
    QUERY = (
        "SELECT ?types ?types_en ?types_ar WHERE {"
        f"""wd:{wikidata_entity_id} wdt:P31 ?types .
        ?types rdfs:label ?types_en filter (lang(?types_en) = 'en') .
        ?types rdfs:label ?types_ar filter (lang(?types_ar) = 'ar') .
        """
        "}"
    )

    while True:
        try:
            r = requests.get(URL, params={"format": "json", "query": QUERY})
            data = r.json()["results"]["bindings"]
            #  Wait between successive requests!
            time.sleep(wait_time_after_request)

            # Parse the data
            categories_id = [
                re.findall(r"Q[0-9]+$", t["types"]["value"])[0] for t in data
            ]
            categories_en = [t["types_en"]["value"] for t in data]
            categories_ar = [t["types_ar"]["value"] for t in data]
            categories = {"en": categories_en, "ar": categories_ar, "id": categories_id}
            break

        except Exception as e:
            print(f"Rate limited on getting the categories of {wikidata_entity_id}!")
            # Quadruple the wait time after getting rate limited!
            wait_time_after_request *= 4
            time.sleep(wait_time_after_request)

    with open(str(Path(ENTITY_CATEGORIES_DIR, f"{wikidata_entity_id}.json")), "w") as f:
        json.dump(categories, f, ensure_ascii=False)

    return categories


def get_entities_count(relation_id, lang):
    relation_templates = {}
    # Load the templates for all the relations
    with open(f"../data/mlama1.1/{lang}/templates.jsonl", "r") as f:
        for l in f:
            relation_data = json.loads(l)
            relation_templates[relation_data["relation"]] = relation_data["template"]

    # Load the triples of this relation
    with open(f"../data/mlama1.1/{lang}/{relation_id}.jsonl", "r") as f:
        data = [json.loads(l) for l in f]

    # Form a single example of the template
    template = relation_templates[relation_id]
    template = re.sub("X", data[0]["sub_label"], template)
    template = re.sub("Y", data[0]["obj_label"], template)
    pprint(template)

    subjects = [sample["sub_uri"] for sample in data]
    objects = [sample["obj_uri"] for sample in data]

    subjects_categories_dicts = [load_entity_categories(sub) for sub in tqdm(subjects)]
    objects_categories_dicts = [load_entity_categories(obj) for obj in tqdm(objects)]
    subjects_all_categories = [
        [(id, sub) for id, sub in zip(sub_dict["id"], sub_dict[lang])]
        for sub_dict in tqdm(subjects_categories_dicts)
    ]
    objects_all_categories = [
        [(id, obj) for id, obj in zip(obj_dict["id"], obj_dict[lang])]
        for obj_dict in tqdm(objects_categories_dicts)
    ]
    subjects_types = Counter(
        [
            category
            for categories_list in subjects_all_categories
            for category in categories_list
        ]
    )
    objects_types = Counter(
        [
            category
            for categories_list in objects_all_categories
            for category in categories_list
        ]
    )
    # Assign each value to the type that is more common in the dataset
    # to filter out infrequent microcategorization tags
    subjects_categories = [
        sorted([(subjects_types[category], category) for category in categories_list])[
            -1
        ][-1]
        if categories_list
        else "N/A"
        for categories_list in subjects_all_categories
    ]
    objects_categories = [
        sorted([(objects_types[category], category) for category in categories_list])[
            -1
        ][-1]
        if categories_list
        else "N/A"
        for categories_list in objects_all_categories
    ]

    return {
        "subjects_values": Counter(
            [sample["sub_label"] for sample in data]
        ).most_common(),
        "objects_values": Counter(
            [sample["obj_label"] for sample in data]
        ).most_common(),
        "subjects_types": Counter(subjects_categories).most_common(),
        "objects_types": Counter(objects_categories).most_common(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Inspect the relations of LAMA")
    parser.add_argument(
        "-l", "--lang", default="en", choices=["ar", "en"], required=False
    )
    parser.add_argument(
        "-P", help="The numeric value of a Wikidata relation in LAMA", required=True
    )
    args = parser.parse_args()
    LANG = args.lang
    RELATION_ID = f"P{args.P}"

    # Create output directory
    os.makedirs(ENTITY_CATEGORIES_DIR, exist_ok=True)

    relation_counts = get_entities_count(RELATION_ID, LANG)

    if input("Print subjects?: [y]/n") != "n":
        pprint(relation_counts["subjects_values"])
    if input("Print objects?: [y]/n") != "n":
        pprint(relation_counts["objects_values"])

    if input("Print subjects categories?: [y]/n") != "n":
        pprint(relation_counts["subjects_types"])
    if input("Print objects categories?: [y]/n") != "n":
        pprint(relation_counts["objects_types"])
