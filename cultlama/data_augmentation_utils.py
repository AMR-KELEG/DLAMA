import time
from tqdm import tqdm
from collections import Counter, deque
from utils import get_wikidata_triples, parse_sparql_results

#  This is used for P19, P20 only
def find_macro_territories(places):
    """
    Find supersets of places (to the level just below the country) for the provided places.

    Args:
    place - A list of wikidata entity IDs (e.g.: [Q127238, Q79])
    """

    sparql_query = (
        """
    SELECT DISTINCT ?micro_place ?macro_place
    WHERE
    {
        {
    """
        f"VALUES ?micro_place {{{' '.join([f'wd:{place}' for place in places])} }} .\n"
        f"?micro_place (wdt:P131*) ?macro_place . # located in the administrative territorial entity"
        """
        }
        MINUS
        {
            { ?macro_place wdt:P31 wd:Q3624078 } # Avoid countries
            UNION
            { ?macro_place wdt:P31 wd:Q3024240 } # Avoid historical countries
            UNION
            { ?macro_place wdt:P31 wd:Q3336843 } # Avoid countries within the UK
        }
    }
    """
    )

    relation_triples = get_wikidata_triples(sparql_query)
    parsed_data = parse_sparql_results(relation_triples)

    #  Some parsing is needed here
    micro_to_macro_dict = {}
    for tuple in parsed_data:
        micro_place = tuple["micro_place"]
        macro_place = tuple["macro_place"]
        if micro_place not in micro_to_macro_dict:
            micro_to_macro_dict[micro_place] = []
        micro_to_macro_dict[micro_place].append(macro_place)
    return micro_to_macro_dict


class Graph:
    def __init__(self, nodes_labels):
        self.adj_list = {label: [] for label in nodes_labels}
        self.node_weights = {label: [] for label in nodes_labels}

    def add_edge(self, src, dis):
        # from sub to super
        self.adj_list[src].append(dis)

    def find_ancestors(self, src):
        """Find all the ancestor nodes for the `src` one."""
        ancestors = [src]

        # Apply bfs for finding all the ancestors for the node `src`
        visited = dict()
        queue = deque()
        visited[src] = True
        queue.append(src)

        while queue:
            cur_node = queue.pop()
            for next_node in self.adj_list[cur_node]:
                if visited.get(next_node):
                    continue
                visited[next_node] = True
                queue.append(next_node)
                ancestors.append(next_node)

        return ancestors


def augment_objects_with_ancestors(objects_uris):
    """Augment the objects with all their ancestors"""

    # Build a graph between these entities
    uris = list(set(objects_uris))

    BATCH_SIZE = 50
    data = []

    # Query the sub/super relationship in batches to handle query length limits
    for sub_batch_start in tqdm(
        range(0, len(uris), BATCH_SIZE), desc="Query the sub/sup relations"
    ):
        sub_uris = " ".join(
            [
                f"wd:{uri}"
                for uri in uris[sub_batch_start : sub_batch_start + BATCH_SIZE]
            ]
        )

        for super_batch_start in tqdm(range(0, len(uris), BATCH_SIZE)):
            super_uris = " ".join(
                [
                    f"wd:{uri}"
                    for uri in uris[super_batch_start : super_batch_start + BATCH_SIZE]
                ]
            )
            query = f"""SELECT DISTINCT ?sub_uri ?super_uri
            WHERE
            {{
                VALUES ?sub_uri {{{sub_uris}}} .
                VALUES ?super_uri {{{super_uris}}} .
                ?sub_uri wdt:P279+ ?super_uri . # sub_uri is subclass of super_uri
            }}"""
            remaining_retries = 3
            while remaining_retries:
                try:
                    data += get_wikidata_triples(query)
                    break
                except:
                    time.sleep(10)
                    remaining_retries -= 1
            time.sleep(0.1)
    parsed_data = parse_sparql_results(data)

    #  Build the graph from sub/super relation edges
    graph = Graph(objects_uris)
    for edge in parsed_data:
        graph.add_edge(edge["sub_uri"], edge["super_uri"])

    return {uri: graph.find_ancestors(uri) for uri in objects_uris}
