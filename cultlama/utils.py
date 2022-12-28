import re
import time
import requests
from tqdm import tqdm
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


def graceful_get_wikidata_triples(query, max_retries=5):
    graceful_delay = 1
    while max_retries > 0:
        try:
            return get_wikidata_triples(query)
        except Exception as e:
            print(e)
            time.sleep(graceful_delay)
            max_retries -= 1
            graceful_delay *= 2


def get_wikidata_triples(query):
    """Query wikidata using a SPARQL query"""
    url = "https://query.wikidata.org/sparql"
    r = requests.post(url, params={"format": "json"}, data={"query": query})
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


def get_wikidata_labels(wikidata_entities_ids, list_of_languages):
    """Get labels of wikidata entities using their IDs"""
    MAX_BATCH_SIZE = (
        50  # https://www.wikidata.org/wiki/Wikidata:Data_access#MediaWiki_Action_API
    )
    labels = {}
    langs = "|".join(list_of_languages)
    for start in tqdm(
        range(0, len(wikidata_entities_ids), MAX_BATCH_SIZE),
        desc="Query labels of Wikidata entities",
    ):
        ids = wikidata_entities_ids[start : start + MAX_BATCH_SIZE]
        wikidata_ids = "|".join([id for id in ids if not id.startswith("http")])
        url = (
            "https://www.wikidata.org/w/api.php?"
            "action=wbgetentities"
            f"&ids={wikidata_ids}"
            f"&languages={langs}&format=json&props=labels"
        )

        additional_headers = {"content-encoding": "gzip"}
        r = requests.get(url, headers=additional_headers)
        data = r.json()["entities"]
        time.sleep(0.1)

        for entity in data:
            labels[entity] = {
                lang: data[entity].get("labels", {}).get(lang, {}).get("value", None)
                for lang in list_of_languages
            }

        # Skipped entities
        for entity in [id for id in ids if id.startswith("http")]:
            labels[entity] = {lang: None for lang in list_of_languages}
    return labels


def get_article_sizes(articles_titles, lang):
    titles_to_query = "|".join(articles_titles)
    url = (
        f"https://{lang}.wikipedia.org/w/api.php?action=query&format=json&titles="
        f"{titles_to_query}&prop=revisions&rvprop=size&redirects"
    )
    additional_headers = {"content-encoding": "gzip"}
    response = requests.get(url, headers=additional_headers).json()

    pages_responses = response["query"]["pages"]
    redirects = (
        response["query"]["redirects"] if "redirects" in response["query"] else []
    )

    redirected_titles_to_original_titles = {
        redirect["to"]: redirect["from"] for redirect in redirects
    }
    time.sleep(0.1)

    return pages_responses, redirected_titles_to_original_titles


def get_wikipedia_article_sizes(articles_urls, lang):
    """Get the size of wikipedia articles in bytes"""

    MAX_BATCH_SIZE = 50  # https://www.mediawiki.org/wiki/API:Query#Additional_notes
    # A dictionary of url -> article size
    articles_sizes = {}
    for start in tqdm(
        range(0, len(articles_urls), MAX_BATCH_SIZE),
        desc=f"Query sizes of Wikipedia articles in '{lang}'",
    ):
        cur_batch_articles_urls = articles_urls[start : start + MAX_BATCH_SIZE]
        HTML_encoded_titles = [url.split("/")[-1] for url in cur_batch_articles_urls]

        # Get the articles' normalized titles from the urls
        normalized_titles_to_urls = {
            # Replace "_" in titles with " "
            requests.utils.unquote(re.sub("_", " ", url.split("/")[-1])): url
            for url in cur_batch_articles_urls
        }

        start = 0
        cur_BATCH_SIZE = MAX_BATCH_SIZE
        pages_responses = {}
        redirected_titles_to_original_titles = {}

        while start < MAX_BATCH_SIZE:
            try:
                cur_batch_titles = HTML_encoded_titles[start : start + cur_BATCH_SIZE]
                (
                    cur_batch_pages_responses,
                    cur_batch_redirected_titles_to_original_titles,
                ) = get_article_sizes(cur_batch_titles, lang)

                #  Join the minibatch results to the whole set of results
                pages_responses = dict(
                    list(pages_responses.items())
                    + list(cur_batch_pages_responses.items())
                )
                redirected_titles_to_original_titles = dict(
                    list(redirected_titles_to_original_titles.items())
                    + list(cur_batch_redirected_titles_to_original_titles.items())
                )
                start += cur_BATCH_SIZE

            except Exception as e:
                cur_BATCH_SIZE = max(1, cur_BATCH_SIZE // 2)
                logger.debug(e)
                logger.info(f"Falling back to batch size of {cur_BATCH_SIZE} articles.")

        page_ids = list(pages_responses.keys())
        for page_id in page_ids:
            # "missing" field indicates that the API failed in retrieving the page's size
            # "invalid" field indicates that the title has problems (e.g.: empty)
            if not any([k in pages_responses[page_id] for k in ["missing", "invalid"]]):
                article_size = pages_responses[page_id]["revisions"][0]["size"]
            else:
                article_size = 0

            # Link the article size to the url of the page
            try:
                normalized_page_title = pages_responses[page_id]["title"]

                if normalized_page_title in normalized_titles_to_urls:
                    articles_sizes[
                        normalized_titles_to_urls[normalized_page_title]
                    ] = article_size

                # Redirects have new page titles that slightly differ from the original title
                elif normalized_page_title in redirected_titles_to_original_titles:
                    original_page_title = redirected_titles_to_original_titles[
                        normalized_page_title
                    ]
                    articles_sizes[
                        normalized_titles_to_urls[original_page_title]
                    ] = article_size

                else:
                    raise Exception()
            except:
                logger.warning(
                    f"There is an issue with querying the page size for page of id '{page_id}'"
                )
                logger.warning(pages_responses[page_id],)

    return articles_sizes
