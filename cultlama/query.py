from constants import *
from filters import FILTERS_DICTIONARY
import utils
import logging
import sys
import time
from tqdm import tqdm

logger = logging.getLogger(__name__)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(levelname)s - %(filename)s:%(funcName)s:line %(lineno)d - %(message)s"
)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)


class Query:
    """A Wikidata SPARQL query object."""

    def __init__(
        self,
        relation_id,
        subject_field,
        object_field,
        domain,
        region,
        region_name,
        sorting_function,
        filters=None,
    ):

        assert sorting_function in ["size", "edits"]
        self.relation_id = relation_id
        self.subject_field = subject_field
        self.object_field = object_field
        self.domain = domain
        self.region = region
        self.region_name = region_name
        self.sorting_function = sorting_function
        self.filters = [] if not filters else filters

        self.wikipedia_langs = REGIONS_LANGS[region]

        assert relation_id.startswith("P")

    def add_filter(self, filter_domain, filter_name):
        """Populate the list of filters to be used for the query.

        Args:
            filter_domain: The main domain of the filter of FILTERS_DICTIONARY.
            filter_name: The name of the filter to use within the domain.
        """
        filters = []
        filters_dict = FILTERS_DICTIONARY[filter_domain]

        filters.append(filters_dict[filter_name])

        #  Add the filter to the list of filters
        self.filters = self.filters + filters

    def add_subjects_filter(self, subjects_uris):
        """Add a filter for specifying a set of uris for the Subject field.

        Args:
            subjects_uris: A list of subject uris.
        """
        subjects_uris = " ".join([f"wd:{uri}" for uri in subjects_uris])
        self.filters.append(f"VALUES ?{self.subject_field} {{{subjects_uris}}}.")

    def build_query(self, find_count=False, limit=None):
        """Form the query while ordering the filters in an optimized way.

        Args:
            find_count: Only return the count of the entries fulfilling the conditions.
            limit: The number of entries to return.

        Returns:
            A SPARQL query in the form of a string.
        """
        sparql_query_lines = []
        if find_count:
            fields_to_return = "SELECT (COUNT(*) as ?count)"
        else:
            fields_to_return = f"SELECT ?{self.subject_field} ?{self.object_field} "
            # Avoid returning the same field twice as it causes SPAQRL errors
            if "country" not in [self.subject_field, self.object_field]:
                fields_to_return += "?country "
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
        """Execute the SPARQL query.

        Args:
            find_count: Only return the count of the entries fulfilling the conditions.
            limit: The number of entries to return.

        Returns:
            A list of dictionaries representing the results.
        """
        sparql_query = self.build_query(find_count, limit)
        relation_triples = utils.get_wikidata_triples(sparql_query)
        parsed_data = utils.parse_sparql_results(relation_triples)

        return parsed_data

    def get_data(self, find_count=False, limit=None, no_retries=10):
        """Execute the SPARQL query with the ability to retry in case of failure.

        Args:
            find_count: Only return the count of the entries fulfilling the conditions.
            limit: The number of entries to return.
            no_retries: The number of times to retry executing the query before giving up.

        Returns:
            A list of dictionaries representing the results.
        """
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
                    if self.sorting_function == "size":
                        wikipedia_sizes_dict = utils.get_wikipedia_article_sizes(
                            urls, lang=lang
                        )
                    else:
                        wikipedia_sizes_dict = {
                            url: utils.get_wikipedia_article_edits(
                                url, wikipedia_lang=lang
                            )
                            for url in tqdm(urls)
                        }

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
    """An object of a list of Wikidata SPARQL queries."""

    def __init__(
        self,
        relation_id,
        subject_field,
        object_field,
        domain,
        region,
        region_name,
        sorting_function,
    ):
        self.relation_id = relation_id
        self.subject_field = subject_field
        self.object_field = object_field
        self.domain = domain
        self.region = region
        self.region_name = region_name
        self.sorting_function = sorting_function
        self.lazy_filters = (
            []
        )  # Lazy filters are filters that are used only on forming each subquery
        self.subqueries = None

        assert relation_id.startswith("P")

    def add_filter(self, filter_domain, filter_name):
        """Populate the list of filters to be used for the query.

        Args:
            filter_domain: The main domain of the filter of FILTERS_DICTIONARY.
            filter_name: The name of the filter to use within the domain.
        """
        self.lazy_filters.append(
            {"filter_domain": filter_domain, "filter_name": filter_name}
        )

    def form_subqueries(self):
        """Form separate SPARQL queries for each country within the region."""
        self.subqueries = []
        for country in self.region:
            #  Build a subquery
            subquery = Query(
                relation_id=self.relation_id,
                subject_field=self.subject_field,
                object_field=self.object_field,
                domain=self.domain,
                region=country,
                region_name=self.region_name,
                sorting_function=self.sorting_function,
            )
            # Add the lazy filters
            for filter in self.lazy_filters:
                filter_domain = filter["filter_domain"]
                filter_name = filter["filter_name"]

                if filter_name == self.region:
                    subquery.add_filter(
                        filter_domain=filter_domain, filter_name=country
                    )
                else:
                    subquery.add_filter(
                        filter_domain=filter_domain, filter_name=filter_name
                    )

            self.subqueries.append(subquery)

    def get_data(self, find_count=False, limit=None, no_retries=10):
        """Execute the SPARQL subqueries in series.

        Args:
            find_count: Only return the count of the entries fulfilling the conditions.
            limit: The number of entries to return.
            no_retries: The number of times to retry executing the query before giving up.

        Returns:
            A list of dictionaries representing the results for the whole region.
        """
        self.form_subqueries()
        data = []
        for subquery in self.subqueries:
            subquery_data = subquery.get_data(find_count, limit, no_retries)
            data += subquery_data
        return data


class QueryFactory:
    """A class for forming queries based on the type of the region used."""

    def create_query(
        self, relation_id, subject_field, object_field, domain, region, region_name
    ):
        #  The region is a list of countries
        if type(region) == type([]):
            return GroupedQuery(
                relation_id, subject_field, object_field, domain, region, region_name
            )
        #  The region is a single country/ a single group of countries (e.g.: Arab region)
        else:
            return Query(
                relation_id, subject_field, object_field, domain, region, region_name
            )
