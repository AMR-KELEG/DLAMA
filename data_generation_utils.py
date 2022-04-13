import json


def form_triple_from_shared_subject(subject_df, q):
    triple_dict = {}

    sub_uri = subject_df[q.subject_field].iloc[0]
    obj_uri = subject_df[q.object_field].tolist()
    sub_label = subject_df["sub_label"].iloc[0]
    obj_label = subject_df["obj_label"].tolist()
    triple_dict["sub_uri"] = sub_uri
    triple_dict["obj_uri"] = obj_uri
    triple_dict["sub_label"] = sub_label
    triple_dict["obj_label"] = obj_label

    return triple_dict


def generate_facts_jsonl(df, q, lang, output_filename):
    """TODO"""
    # TODO: Do I need to add the Region as well?
    # TODO: What is the use of lineid, uuid?
    # Keys:
    # {obj/sub}_uri, {obj/sub}_label, lineid, uuid

    triples = []
    for i, (_, grouped_df) in enumerate(df.groupby(q.subject_field)):
        triple_dict = form_triple_from_shared_subject(grouped_df, q)
        # TODO: Add the region to the id or any unique identifier to avoid collisions
        triple_dict["uuid"] = f"{q.relation_id}_{q.domain}_{q.region}_{i}"

        triples.append(triple_dict)

    # Export triples to a jsonl file
    with open(output_filename, "w") as f:
        for triple in triples:
            f.write(json.dumps(triple, ensure_ascii=False))
            f.write("\n")
