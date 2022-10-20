import json


def form_triple_from_shared_subject(subject_df, q):
    """
    Group the triples by subjects such that each subject is linked to a list of valid objects.
    """
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
    """
    Dump the dataframe of triples into a jsonl file.
    """

    triples = []
    for i, (_, grouped_df) in enumerate(df.groupby(q.subject_field, sort=False)):
        triple_dict = form_triple_from_shared_subject(grouped_df, q)
        #  Provide a unique id for each triple
        triple_dict["uuid"] = f"{q.relation_id}_{q.domain}_{q.region_name}_{i}"
        triples.append(triple_dict)

    # Export triples to a jsonl file
    with open(output_filename, "w") as f:
        for triple in triples:
            f.write(json.dumps(triple, ensure_ascii=False))
            f.write("\n")
