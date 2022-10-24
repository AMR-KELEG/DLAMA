from constants import *
from filters import FILTERS_DICTIONARY
import utils
import logging
import sys
import time

logger = logging.getLogger(__name__)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(levelname)s - %(filename)s:%(funcName)s:line %(lineno)d - %(message)s"
)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)


class Query:
    # TODO: Add docstrings
    def __init__(
        self,
        relation_id,
        subject_field,
        object_field,
        domain,
        region,
        region_name,
        filters=None,
    ):
        self.relation_id = relation_id
        self.subject_field = subject_field
        self.object_field = object_field
        self.domain = domain
        self.region = region
        self.region_name = region_name
        self.filters = [] if not filters else filters

        self.wikipedia_langs = REGIONS_LANGS[region]

        assert relation_id.startswith("P")

    def add_filter(self, filter_name, filter_key):
        filters = []
        filters_dict = FILTERS_DICTIONARY[filter_name]

        filters.append(filters_dict[filter_key])

        # Add the common filter for this filter type
        if "common" in filters_dict:
            filters.append(filters_dict["common"])

        #  Add the filter to the list of filters
        self.filters = self.filters + filters

    def add_subjects_filter(self, subjects_uris):
        subjects_uris = " ".join([f"wd:{uri}" for uri in subjects_uris])
        self.filters.append(f"VALUES ?{self.subject_field} {{{subjects_uris}}}.")

        # TODO: Find a better place to add this filter!
        # Filter out historical countries
        if self.object_field == COUNTRY or self.subject_field == COUNTRY:
            self.add_filter(GEOGRAPHY, "sovereign_state")
            self.add_filter(GEOGRAPHY, "not_historical_country")
        if self.object_field == COUNTRY1 or self.subject_field == COUNTRY1:
            self.add_filter(GEOGRAPHY, "sovereign_state1")
            self.add_filter(GEOGRAPHY, "not_historical_country1")
        if self.object_field == CITY:
            self.add_filter(GEOGRAPHY, "not_lost_city")
            self.add_filter(GEOGRAPHY, "city_not_sovereign_state")
            self.add_filter(GEOGRAPHY, "city_not_historical_state")
            self.add_filter(GEOGRAPHY, "city_not_country_within_the_UK")
        if self.object_field == INSTRUMENT:
            self.add_filter(MUSIC, "not_voice")
        if self.object_field == LANGUAGE:
            self.add_filter(LANGUAGE, "not_sign_language")

    def build_query(self, find_count=False, limit=None):
        sparql_query_lines = []
        if find_count:
            fields_to_return = "SELECT (COUNT(*) as ?count)"
        else:
            fields_to_return = f"SELECT ?{self.subject_field} ?{self.object_field} "
            fields_to_return += "".join(
                [f"?subject_article_{lang} " for lang in self.wikipedia_langs]
            )

        sparql_query_lines.append(fields_to_return)
        sparql_query_lines.append("WHERE\n{")
        filters_added = [False for _ in range(len(self.filters))]
        # Add filters specifying specific values
        for i, f in enumerate(self.filters):
            if "VALUES" in f:
                filters_added[i] = True
                for l in f.split("\n"):
                    sparql_query_lines.append(f"\t{l.strip()}")

        # Add filters related to object only
        for i, f in enumerate(self.filters):
            if (
                "VALUES" not in f
                and "MINUS" not in f
                and self.object_field in f
                and self.subject_field not in f
            ):
                filters_added[i] = True
                for l in f.split("\n"):
                    sparql_query_lines.append(f"\t{l.strip()}")

        # Subject and object of the relation tuple
        sparql_query_lines.append(
            f"\t?{self.subject_field} wdt:{self.relation_id} ?{self.object_field} ."
        )

        # Add filters related to subject only
        for i, f in enumerate(self.filters):
            if (
                "VALUES" not in f
                and "MINUS" not in f
                and self.object_field not in f
                and self.subject_field in f
            ):
                filters_added[i] = True
                for l in f.split("\n"):
                    sparql_query_lines.append(f"\t{l.strip()}")

        #  Add the remaining filters
        for f, filter_added in zip(self.filters, filters_added):
            if not filter_added:
                for l in f.split("\n"):
                    sparql_query_lines.append(f"\t{l.strip()}")

        # Get the urls of the Wikipedia articles
        for lang in self.wikipedia_langs:
            #  Missing one wikipedia page is fine as long as the labels can be recovered later
            wikipedia_page_url = f"""\tOPTIONAL {{?subject_article_{lang} schema:about ?{self.subject_field} .
                ?subject_article_{lang} schema:inLanguage "{lang}" .
                ?subject_article_{lang} schema:isPartOf <https://{lang}.wikipedia.org/> .}} ."""
            sparql_query_lines.append(wikipedia_page_url)

        # Terminate the query
        sparql_query_lines.append("}")

        # Set a limit on the number of results
        if limit:
            sparql_query_lines.append(f"LIMIT {limit}")

        return "\n".join(sparql_query_lines).expandtabs(4)

    def parse_query(self, find_count=False, limit=None):
        sparql_query = self.build_query(find_count, limit)
        relation_triples = utils.get_wikidata_triples(sparql_query)
        parsed_data = utils.parse_sparql_results(relation_triples)

        return parsed_data

    def get_data(self, find_count=False, limit=None, no_retries=10):
        while no_retries:
            try:
                print(self.build_query(find_count, limit))
                parsed_data = self.parse_query(find_count, limit)
                parsed_data = [
                    dict(y) for y in set(tuple(x.items()) for x in parsed_data)
                ]
                parsed_data = sorted(parsed_data, key=lambda d: d[self.subject_field])

                # Query the articles' sizes
                for lang in self.wikipedia_langs:
                    # Find list of urls
                    article_url_key = f"subject_article_{lang}"

                    urls = sorted(
                        set(
                            [
                                triple[article_url_key]
                                for triple in parsed_data
                                if article_url_key in triple
                            ]
                        )
                    )
                    # Find the articles' sizes of the urls
                    wikipedia_sizes_dict = utils.get_wikipedia_article_sizes(
                        urls, lang=lang
                    )

                    # Add the size column to the dataframe
                    for triple in parsed_data:
                        if not article_url_key in triple:
                            size = 0
                        else:
                            size = wikipedia_sizes_dict.get(triple[article_url_key], 0)
                        triple[f"size_article_{lang}"] = size
                        triple["size"] = max(size, triple.get("size", 0))
                return parsed_data
            except Exception as e:
                logger.error(e)
                no_retries -= 1
                # Use delay of 30 seconds before retrying!
                time.sleep(30)
                if no_retries == 0:
                    logger.info(
                        f"Failed to generate '{self.relation_id}_{self.domain}_{self.region_name}.jsonl'"
                    )
                    raise (e)


class GroupedQuery:
    def __init__(
        self, relation_id, subject_field, object_field, domain, region, region_name,
    ):
        self.relation_id = relation_id
        self.subject_field = subject_field
        self.object_field = object_field
        self.domain = domain
        self.region = region
        self.region_name = region_name
        self.lazy_filters = []
        self.subqueries = None

        assert relation_id.startswith("P")

    def add_filter(self, filter_name, filter_key):
        self.lazy_filters.append({"filter_name": filter_name, "filter_key": filter_key})

    def form_subqueries(self):
        self.subqueries = []
        for region in self.region:
            #  Build a subquery
            subquery = Query(
                relation_id=self.relation_id,
                subject_field=self.subject_field,
                object_field=self.object_field,
                domain=self.domain,
                region=region,
                region_name=self.region_name,
            )
            # Add the lazy filters
            for filter in self.lazy_filters:
                filter_name = filter["filter_name"]
                filter_key = filter["filter_key"]

                if filter_key == self.region:
                    subquery.add_filter(filter_name=filter_name, filter_key=region)
                else:
                    subquery.add_filter(filter_name=filter_name, filter_key=filter_key)

            self.subqueries.append(subquery)

    def get_data(self, find_count=False, limit=None, no_retries=10):
        self.form_subqueries()
        data = []
        for subquery in self.subqueries:
            subquery_data = subquery.get_data(find_count, limit, no_retries)
            data += subquery_data
        return data


class QueryFactory:
    def create_query(
        self, relation_id, subject_field, object_field, domain, region, region_name
    ):
        if type(region) == type([]):
            return GroupedQuery(
                relation_id, subject_field, object_field, domain, region, region_name
            )
        else:
            return Query(
                relation_id, subject_field, object_field, domain, region, region_name
            )
