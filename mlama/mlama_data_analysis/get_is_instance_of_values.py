#!/usr/bin/env python
# coding: utf-8

import os
import re
import json
import time
from urllib import request
import requests
from tqdm import tqdm
from pprint import pprint
from collections import Counter
from fake_useragent import UserAgent
from glob import glob
from pathlib import Path

ENTITY_CATEGORIES_DIR = "wikidata-instance-of/"


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
            ua = UserAgent()
            headers = {"User-Agent": ua.random}
            r = requests.get(
                URL, params={"format": "json", "query": QUERY, "headers": headers}
            )
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


import argparse

if __name__ == "__main__":
    files = sorted(glob("../data/mlama1.1/ar/P*[0-9].jsonl"))
    uris = []
    parser = argparse.ArgumentParser("Collect is instance of information from Wikidata")
    parser.add_argument("--start", required=True, type=int)
    # parser.add_argument("--end", required=True, type=int)
    step = 1000
    args = parser.parse_args()
    start = args.start

    for file in files:
        with open(file, "r") as f:
            data = [json.loads(l) for l in f]
            uris.append([s["sub_uri"] for s in data])
            uris.append([s["obj_uri"] for s in data])

    unique_uris = sorted(set([u for l in uris for u in l]))

    for i, uri in enumerate(tqdm(unique_uris[start : start + step])):
        path = f"{ENTITY_CATEGORIES_DIR}/{uri}.json"
        try:
            with open(str(Path(ENTITY_CATEGORIES_DIR, f"{uri}.json")), "r") as f:
                data = json.load(f)
                data["id"]
        except:
            request_entity_categories(uri, 0.1 + (i % 10) / 10)
