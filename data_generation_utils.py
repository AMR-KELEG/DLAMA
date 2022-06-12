import json
import time
from tqdm import tqdm
from collections import Counter, deque
from utils import get_wikidata_triples, parse_sparql_results

#  This is used for P19, P20 only
def find_macro_territories(places):
    """
    Args:
    place - A list of wikidata entity IDs (e.g.: [Q127238, Q79])
    """

    sparql_query = (
        """SELECT DISTINCT ?micro_place ?macro_place
    WHERE
    {
        {
    """
        f"VALUES ?micro_place {{{' '.join([f'wd:{place}' for place in places])} }} .\n"
        f"?micro_place (wdt:P131*) ?macro_place . "
        """
        }
        MINUS
        {
            { ?macro_place wdt:P31 wd:Q3624078 } # Avoid countries
            UNION
            { ?macro_place wdt:P31 wd:Q3024240 } # Avoid historical countries
        }
    }"""
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
    time.sleep(5)
    return micro_to_macro_dict


def form_triple_from_shared_subject(subject_df, q):
    triple_dict = {}

    sub_uri = subject_df[q.subject_field].iloc[0]
    obj_uri = subject_df[q.object_field].tolist()
    sub_label = subject_df["sub_label"].iloc[0]
    obj_label_dict = {
        uri: label
        for uri, label in zip(
            sum(subject_df[q.object_field].tolist(), []),
            sum(subject_df["obj_label"].tolist(), []),
        )
    }
    triple_dict["sub_uri"] = sub_uri
    triple_dict["obj_uri"] = sorted(set(sum(obj_uri, [])))
    triple_dict["sub_label"] = sub_label
    triple_dict["obj_label"] = [obj_label_dict[uri] for uri in triple_dict["obj_uri"]]

    return triple_dict


def generate_facts_jsonl(df, q, output_filename):
    """TODO"""

    triples = []
    for i, (_, grouped_df) in enumerate(df.groupby(q.subject_field, sort=False)):
        triple_dict = form_triple_from_shared_subject(grouped_df, q)
        triple_dict["uuid"] = f"{q.relation_id}_{q.domain}_{q.region_name}_{i}"

        triples.append(triple_dict)

    # Export triples to a jsonl file
    with open(output_filename, "w") as f:
        for triple in triples:
            f.write(json.dumps(triple, ensure_ascii=False))
            f.write("\n")


class Graph:
    def __init__(self, nodes_labels):
        self.adj_list = {label: [] for label in nodes_labels}
        self.node_weights = {label: [] for label in nodes_labels}

    def add_edge(self, src, dis):
        # from sub to super
        self.adj_list[src].append(dis)

    def add_node_weight(self, node, weight):
        self.node_weights[node] = weight

    def find_ancestors(self, src):
        ancestors = [src]

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


def form_objects_ancestors_lists(objects_uris):
    # Build a graph between these entities
    uris_counts = Counter(objects_uris).most_common()

    uris = [uri for uri, count in uris_counts]
    uris_in_query = " ".join([f"wd:{uri}" for uri in uris])

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
                ?sub_uri wdt:P279+ ?super_uri .
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
