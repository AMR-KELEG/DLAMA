import re
import json
from pprint import pprint
from collections import Counter


def get_entities_count(relation_id, lang):
    relation_templates = {}
    with open(f"../data/mlama1.1/{lang}/templates.jsonl", "r") as f:
        for l in f:
            relation_data = json.loads(l)
            relation_templates[relation_data["relation"]] = relation_data["template"]

    with open(f"../data/mlama1.1/{lang}/{relation_id}.jsonl", "r") as f:
        data = [json.loads(l) for l in f]

    template = relation_templates[relation_id]
    template = re.sub("X", data[0]["sub_label"], template)
    template = re.sub("Y", data[0]["obj_label"], template)
    pprint(template)

    return (
        Counter([sample["obj_label"] for sample in data]).most_common(),
        Counter([sample["sub_label"] for sample in data]).most_common(),
    )


if __name__ == "__main__":
    # "P1412", "P140"
    relation_id = input("Enter relation ID: ")
    lang = input("Enter language: ")
    relation_counts = get_entities_count(relation_id, lang)
    pprint(relation_counts[0])
    pprint(relation_counts[1])
