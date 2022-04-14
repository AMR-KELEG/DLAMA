from csv import excel_tab
import re
import time
import requests
from tqdm import tqdm
from constants import LANGS
import logging
import sys

logger = logging.getLogger(__name__)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(levelname)s - %(filename)s:%(funcName)s:line %(lineno)d - %(message)s"
)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)


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
    for start in tqdm(
        range(0, len(wikidata_entities_ids), batch_size),
        desc="Query labels of Wikidata entities",
    ):
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


def get_wikipedia_article_sizes(articles_urls, lang):
    """Get the size of wikipedia articles in bytes"""
    batch_size = 50
    # A dictionary of url -> article size
    articles_sizes = {}
    for start in tqdm(
        range(0, len(articles_urls), batch_size),
        desc=f"Query sizes of Wikipedia articles in '{lang}'",
    ):
        # Get the articles' titles from the urls
        # TODO: Find a better format for this dictionary
        titles = {
            # Replace "_" in titles with " "
            requests.utils.unquote(re.sub("_", " ", url.split("/")[-1])): url
            for url in articles_urls[start : start + batch_size]
        }
        titles_to_query = "|".join(titles.keys())
        url = (
            f"https://{lang}.wikipedia.org/w/api.php?action=query&format=json&titles="
            f"{titles_to_query}&prop=revisions&rvprop=size"
        )
        response = requests.get(url).json()
        time.sleep(0.1)
        pages_responses = response["query"]["pages"]

        page_ids = list(pages_responses.keys())
        for page_id in page_ids:
            # "missing" field indicates that the API failed in retrieving the page's size
            # "invalid" field indicates that the title has problems (e.g.: empty)
            if not any([k in pages_responses[page_id] for k in ["missing", "invalid"]]):
                article_size = pages_responses[page_id]["revisions"][0]["size"]
            else:
                article_size = 0

            # Wikipedia has problems if the page's title contains "&"
            try:
                articles_sizes[titles[pages_responses[page_id]["title"]]] = article_size
            except:
                logger.warn("Title contains '&' causing problems with Wikipedia's API")
                logger.warn(pages_responses[page_id],)

    return articles_sizes
