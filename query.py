from constants import *
from filters import FILTERS_DICTIONARY
import utils


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

    def build_query(self, find_count=False, limit=None):
        sparql_query_lines = []
        if find_count:
            fields_to_return = "SELECT (COUNT(*) as ?count)"
        else:
            fields_to_return = (
                f"SELECT DISTINCT ?{self.subject_field} ?{self.object_field} "
            )
            fields_to_return += "".join(
                [f"?subject_article_{lang} " for lang in self.wikipedia_langs]
            )

        sparql_query_lines.append(fields_to_return)
        sparql_query_lines.append("WHERE\n{")

        # Add filters related to object only
        for f in self.filters:
            if (
                "MINUS" not in f
                and self.object_field in f
                and self.subject_field not in f
            ):
                for l in f.split("\n"):
                    sparql_query_lines.append(f"\t{l.strip()}")

        # Subject and object of the relation tuple
        sparql_query_lines.append(
            f"\t?{self.subject_field} wdt:{self.relation_id} ?{self.object_field} ."
        )

        # Add filters related to subject only
        for f in self.filters:
            if (
                "MINUS" not in f
                and self.object_field not in f
                and self.subject_field in f
            ):
                for l in f.split("\n"):
                    sparql_query_lines.append(f"\t{l.strip()}")

        #  Add the remaining filters
        for f in self.filters:
            if (
                "MINUS" in f
                or not (self.object_field in f and self.subject_field not in f)
                and not (self.object_field not in f and self.subject_field in f)
            ):
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

    def get_data(self, find_count=False, limit=None):
        print(self.build_query(find_count, limit))
        parsed_data = self.parse_query(find_count, limit)

        # Query the articles' sizes
        for lang in self.wikipedia_langs:
            # Find list of urls
            article_url_key = f"subject_article_{lang}"

            urls = [
                triple[article_url_key]
                for triple in parsed_data
                if article_url_key in triple
            ]
            # Find the articles' sizes of the urls
            wikipedia_sizes_dict = utils.get_wikipedia_article_sizes(urls, lang=lang)

            # Add the size column to the dataframe
            for triple in parsed_data:
                if not article_url_key in triple:
                    size = 0
                else:
                    size = wikipedia_sizes_dict.get(triple[article_url_key], 0)
                triple[f"size_article_{lang}"] = size
                triple["size"] = max(size, triple.get("size", 0))
        return parsed_data


class GroupedQuery:
    def __init__(
        self, relation_id, subject_field, object_field, domain, region, region_name,
    ):
        self.relation_id = relation_id
        self.subject_field = subject_field
        self.object_field = object_field
        self.domain = domain
        self.regions = region
        self.region_name = region_name
        self.lazy_filters = []
        self.subqueries = None

        assert relation_id.startswith("P")

    def add_filter(self, filter_name, filter_key):
        self.lazy_filters.append({"filter_name": filter_name, "filter_key": filter_key})

    def form_subqueries(self):
        self.subqueries = []
        for region in self.regions:
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

                if filter_key == self.regions:
                    subquery.add_filter(filter_name=filter_name, filter_key=region)
                else:
                    subquery.add_filter(filter_name=filter_name, filter_key=filter_key)

            self.subqueries.append(subquery)

    def get_data(self, find_count=False, limit=None):
        self.form_subqueries()
        data = []
        for subquery in self.subqueries:
            subquery_data = subquery.get_data(find_count, limit)
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
