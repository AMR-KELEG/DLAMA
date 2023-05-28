import re
import json
import pandas as pd
from natsort import natsort_keygen

with open("../mlama/data/wikidata-predicates.json", "r") as f:
    data = json.load(f)["rows"]
    wikidata_predicates = {
        predicate_id: predicate_name.capitalize()
        for predicate_id, predicate_name in data
    }


def form_proper_highlight(percentage, text):
    return text if percentage < 50 else f"\\underline{{{text}}}"


def load_stats(dataset_name):
    """Aggregate the stats for the dataset"""
    with open(dataset_name, "r") as f:
        df = pd.DataFrame([json.loads(l) for l in f])
        sum_values = df.sum().to_dict()
        df = pd.concat(
            [
                df,
                pd.DataFrame(
                    [
                        {
                            "predicate": "Total",
                            "no_western": sum_values["no_western"],
                            "no_others": sum_values["no_others"],
                        }
                    ]
                ),
            ]
        )

    df["no_total"] = df["no_western"] + df["no_others"]
    df.sort_values(by="predicate", key=natsort_keygen(), inplace=True)
    df["Predicate"] = (
        df["predicate"]
        .apply(lambda p: f"{p} ({wikidata_predicates.get(p, '')})")
        .apply(lambda s: re.sub(r"\(\)$", "", s))
    )
    df["Per_western"] = df.apply(
        lambda row: round(100 * row["no_western"] / row["no_total"], 1), axis=1
    )
    df["Per_non_western"] = df.apply(
        lambda row: round(100 * row["no_others"] / row["no_total"], 1), axis=1
    )

    df["Western"] = df.apply(
        lambda row: f"{row['no_western']} ({row['Per_western']}%)", axis=1
    )
    df["Non western"] = df.apply(
        lambda row: f"{row['no_others']} ({row['Per_non_western']}%)", axis=1
    )

    df["Western"] = df.apply(
        lambda row: form_proper_highlight(row["Per_western"], row["Western"]), axis=1
    )
    df["Non western"] = df.apply(
        lambda row: form_proper_highlight(row["Per_non_western"], row["Non western"]),
        axis=1,
    )

    return df[["Predicate", "Western", "Non western"]]


trex_df = load_stats("benchmarks_stats/stats_trex.jsonl")
lama_df = load_stats("benchmarks_stats/stats_mlama.jsonl")
xfactr_df = load_stats("benchmarks_stats/stats_xfactr.jsonl")

columns = ["Western", "Non western"]
merged_df = pd.concat([trex_df, lama_df[columns], xfactr_df[columns]], axis=1)
table_text = merged_df.to_latex(index=False)
table_text = re.sub(r"textbackslash ", r"", table_text)
table_text = re.sub(r"underline\\", r"underline", table_text)
print(re.sub(r"textbackslash ", r"", table_text))
