import time
import requests
from tqdm import tqdm
from constants import LANGS


def get_wikidata_triples(query):
    """Query wikidata using a SPARQL query"""
    url = "https://query.wikidata.org/sparql"
    r = requests.get(url, params={"format": "json", "query": query})
    data = r.json()
    return data["results"]["bindings"]


def parse_sparql_results(results_list):
    """Parse the results into flattened list of dictionaries"""
    parsed_results = []
    for result in results_list:
        parsed_result = {}
        for k in result.keys():
            field = result[k]
            field_value = field["value"]
            field_type = field["type"]

            # Get the raw Wikidata id for the entity
            if field_type == "uri" and "wikidata.org/entity/Q" in field_value:
                field_value = field_value.split("/")[-1]
            parsed_result[k] = field_value
        parsed_results.append(parsed_result)
    return parsed_results


def get_wikidata_labels(wikidata_entities_ids):
    """Get labels of wikidata entities using their IDs"""
    batch_size = 50
    labels = {}
    langs = "|".join(LANGS)
    for start in tqdm(range(0, len(wikidata_entities_ids), batch_size)):
        wikidata_ids = "|".join(wikidata_entities_ids[start : start + batch_size])
        url = (
            "https://www.wikidata.org/w/api.php?"
            "action=wbgetentities"
            f"&ids={wikidata_ids}"
            f"&languages={langs}&format=json&props=labels"
        )
        r = requests.get(url)
        data = r.json()["entities"]
        time.sleep(0.1)
        for entity in data:
            labels[entity] = {
                lang: data[entity].get("labels", {}).get(lang, {}).get("value", None)
                for lang in LANGS
            }
    return labels



