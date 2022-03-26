import requests


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
