from constants import *
from filters import FILTERS_DICTIONARY
from utils import get_wikidata_triples


class Query:
    # TODO: Add docstrings
    def __init__(
        self,
        relation_id,
        subject_field,
        object_field,
        domain,
        region,
        wikipedia_langs=None,
        filters=None,
    ):
        self.relation_id = relation_id
        self.subject_field = subject_field
        self.object_field = object_field
        self.domain = domain
        self.region = region
        self.filters = [] if not filters else filters
        # Default to English
        # TODO: Is this the best way to do it?
        self.wikipedia_langs = wikipedia_langs if wikipedia_langs else ["en"]

        assert relation_id.startswith("P")

    def add_filter(self, filter_type, filter_value):
        filters = []
        filters_dict = FILTERS_DICTIONARY[filter_type]

        filters.append(filters_dict[filter_value])

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
        return get_wikidata_triples(sparql_query)
