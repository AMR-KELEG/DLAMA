import json
from collections import Counter, deque
from utils import get_wikidata_triples, parse_sparql_results


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
    # TODO: Do I need to add the Region as well?
    # TODO: What is the use of lineid, uuid?
    # Keys:
    # {obj/sub}_uri, {obj/sub}_label, lineid, uuid

    triples = []
    for i, (_, grouped_df) in enumerate(df.groupby(q.subject_field, sort=False)):
        triple_dict = form_triple_from_shared_subject(grouped_df, q)
        # TODO: Add the region to the id or any unique identifier to avoid collisions
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

    def add_edge(self, src, dis):
        # from sub to super
        self.adj_list[src].append(dis)

    def find_isolated_nodes(self, src):
        #  TODO: Handle cycles?
        isolated_nodes = []
        visited = dict()
        queue = deque()
        queue.append(src)
        while queue:
            cur_node = queue.pop()
            if len(self.adj_list[cur_node]) == 0:
                isolated_nodes.append(cur_node)
            else:
                for next_node in self.adj_list[cur_node]:
                    if not visited.get(next_node):
                        queue.append(next_node)
                        visited[next_node] = True

        return isolated_nodes


def form_objects_merging_dict(objects_uris):
    # Build a graph between these entities
    uris_counts = Counter(objects_uris).most_common()

    # Filter out rare objects?
    #  Not valid for all relations!
    uris = [uri for uri, count in uris_counts if count != 1]
    uris_in_query = " ".join([f"wd:{uri}" for uri in uris])

    query = f"""SELECT DISTINCT ?sub_uri ?super_uri
    WHERE
    {{
        VALUES ?sub_uri {{{uris_in_query}}} .
        VALUES ?super_uri {{{uris_in_query}}} .
        ?sub_uri wdt:P279+ ?super_uri .
    }}"""

    data = get_wikidata_triples(query)
    parsed_data = parse_sparql_results(data)

    #  Build the graph from sub/super relation edges
    graph = Graph(objects_uris)
    for edge in parsed_data:
        graph.add_edge(edge["sub_uri"], edge["super_uri"])

    # TODO: Do I need to filter out outliers as well?
    return {uri: graph.find_isolated_nodes(uri) for uri in objects_uris}
