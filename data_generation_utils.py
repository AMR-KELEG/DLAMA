import json
import utils


def generate_facts_jsonl(df, q, lang, output_filename):
    """TODO"""
    # Query the Wikidata labels
    subjects_ids = df[q.subject_field].tolist()
    subjects_labels = utils.get_wikidata_labels(subjects_ids)

    objects_ids = df[q.object_field].tolist()
    objects_labels = utils.get_wikidata_labels(objects_ids)

    # TODO: Do I need to add the Region as well?
    # TODO: What is the use of lineid, uuid?
    # Keys:
    # {obj/sub}_uri, {obj/sub}_label, lineid, uuid

    triples = []
    for i, row in df.iterrows():
        triple_dict = {}
        sub_uri = row[q.subject_field]
        obj_uri = row[q.object_field]
        triple_dict["sub_uri"] = sub_uri
        triple_dict["obj_uri"] = obj_uri
        # TODO: Handle missing labels?
        triple_dict["sub_label"] = subjects_labels[sub_uri][lang]
        triple_dict["obj_label"] = objects_labels[obj_uri][lang]
        # TODO: Add the region to the id or any unique identifier to avoid collisions
        triple_dict["uuid"] = f"{q.relation_id}_{q.domain}_{q.region}_{i}"
        triples.append(triple_dict)

    # Export triples to a jsonl file
    with open(output_filename, "w") as f:
        for triple in triples:
            f.write(json.dumps(triple, ensure_ascii=False))
            f.write("\n")
