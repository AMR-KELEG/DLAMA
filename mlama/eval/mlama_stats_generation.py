#!/usr/bin/env python
import glob
import json
import pickle
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats
from pathlib import Path
import matplotlib.pyplot as plt
from tqdm import tqdm
from pprint import pprint
from groups import models_groups


def load_wikidata_predicates_names():
    with open("data/wikidata-predicates.json", "r") as f:
        wikidata_predicates_list = json.load(f)["rows"]

    wikidata_predicates_df = pd.DataFrame(
        [
            {"predicate": l[0].strip(), "name": l[1].strip()}
            for l in wikidata_predicates_list
        ]
    )
    patterns_dict = {
        d["predicate"]: d["name"]
        for d in wikidata_predicates_df.to_dict(orient="records")
    }

    return patterns_dict


def load_model_results(model, path_compare, patterns_dict):
    """
    Aggregate the resuls from the pickle file.

    model: Path of model results.
    path_compare: Path of the other model to compare the results to.
    """
    relations = [
        relation.split("/")[-1] for relation in glob.glob(str(Path(model, "*")))
    ]

    model_name = model.split("/")[-2]

    # TODO: Handle this in a better way
    # Prepend language to model_name?
    if "mbert_base" in model or "gigabert" in model or model == "bert-base-uncased":
        model_name += "_" + model.split("/")[-1]

    model_results = {"model": model_name}

    for relation in relations:
        # Skip the date
        # TODO: Why?
        if "date" in relation:
            continue

        # Load the results of the model
        with open(Path(model, relation, "result.pkl"), "rb") as f:
            data = pickle.load(f)

        # Load the results of the reference model
        with open(Path(path_compare, relation, "result.pkl"), "rb") as f:
            data_reference = pickle.load(f)

        # Make sure the pickle file is valid
        assert len(data["list_of_results"]) > 0

        # Ignore one sample that is in Arabic data and not in English data
        # This is a bug in mlama's data
        reference_dict = {
            d["sample"]["uuid"]: [int(d["masked_topk"]["ranks"][0] == 0), d["sample"]]
            for d in data_reference["list_of_results"]
            if not (
                relation == "P20"
                and d["sample"]["uuid"] == "b683ca8a-4c15-4348-a7b7-5d700b5104c4"
            )
        }

        model_dict = {
            d["sample"]["uuid"]: [int(d["masked_topk"]["ranks"][0] == 0), d["sample"]]
            for d in data["list_of_results"]
            if d["sample"]["uuid"]
            in reference_dict  # Only keep the samples with Arabic equivalent
        }
        try:
            assert len(reference_dict) == len(model_dict)
        except Exception as e:
            print(relation)
            print(len(reference_dict), len(model_dict))
            raise e

        # TODO: Check these aggregations and rename columns' names
        relation_name = patterns_dict.get(relation, relation)
        relation = f"{relation}.{relation_name}"
        model_results[f"{relation}.model"] = sum([t[0] for t in model_dict.values()])
        model_results[f"{relation}.ref"] = sum([t[0] for t in reference_dict.values()])
        model_results[f"{relation}.model.P"] = model_results[f"{relation}.model"] / len(
            model_dict
        )
        model_results[f"{relation}.ref.P"] = model_results[f"{relation}.ref"] / len(
            reference_dict
        )
        model_results[f"{relation}.total"] = len(model_dict)

    # Compute micro/macro averaged scores here?
    n_triples = sum(
        [model_results[c] for c in model_results.keys() if c.endswith(".total")]
    )
    n_correct = sum(
        [model_results[c] for c in model_results.keys() if c.endswith(".model")]
    )
    p_performance = [
        model_results[c] for c in model_results.keys() if c.endswith(".model.P")
    ]
    model_results["micro_averaged_performance"] = n_correct / n_triples
    model_results["macro_averaged_performance"] = sum(p_performance) / len(
        p_performance
    )

    return model_results


def generate_heatmap(results_df):
    #  width, height
    # da_models = models_groups["Arabic_DA"]
    # results_df = results_df.loc[da_models, :]
    results_df = results_df.drop_duplicates()
    fig, axes = plt.subplots(figsize=results_df.shape)

    results_df = results_df.T
    print(results_df.columns)
    patterns_order = [
        c
        for c in results_df.sort_values(by="camel_msa").index.tolist()
        if "averaged_performance" not in c
    ]
    patterns_order = patterns_order + [
        "micro_averaged_performance",
        "macro_averaged_performance",
    ]
    results_df = results_df.reindex(patterns_order)

    sns.heatmap(
        results_df, cmap="Greens", fmt="0.2g", ax=axes, annot=True, cbar=False,
    )
    for tick in axes.get_xticklabels():
        tick.set_rotation(-45)

    # plt.tight_layout()
    # plt.show()
    plt.savefig("heatmap.pdf", bbox_inches="tight")


def main():
    # TODO: Is this enough to properly handle English models?
    # Configuration parameters
    # TODO: Move to args
    lang = "en"
    base_dir = "output_dlama"
    output_path = str(Path(base_dir, "results/*/ar/"))

    # Reference is only used to filter out samples
    # Set it to any of the Arabic models
    path_compare = str(Path(base_dir, "results/camel_msa/ar/"))

    # List of models to compute metrics for
    models = glob.glob(output_path) + glob.glob(
        str(Path(base_dir, f"results/*/{lang}/"))
    )
    # Load list of predicates ids with their names
    patterns_dict = load_wikidata_predicates_names()

    # Start computing metrics
    results = [
        load_model_results(model, path_compare, patterns_dict) for model in tqdm(models)
    ]

    # Transform results into a dataframe to make it easier to navigate through
    # Each row represents the results of a single model
    whole_results_df = pd.DataFrame(results)

    # Reformat results df for plotting
    columns = [
        c
        for c in whole_results_df.columns
        if c.endswith(".model.P") or c == "model" or "averaged_performance" in c
    ]
    print(whole_results_df)
    print(columns)
    results_df = whole_results_df.loc[:, columns].copy()
    results_df.sort_values(by="micro_averaged_performance", inplace=True)
    results_df.set_index("model", inplace=True)

    # Generate heatmap
    generate_heatmap(results_df)
    # TODO: Add support column

    # Print differences in scores
    # print(
    #     results_df.apply(lambda row: row["bert-base"] - row["camel_msa"], axis=1)
    #     .reset_index()
    #     .sort_values(by=0)
    # )

    # Finalize on Friday and share it
    # - camel_msa is different from camel_mix
    # - Dialectical models (camel_da, darijabert, dziribert) are similar to each other
    # - camel_msa and arabert are similar
    # - qarib, marbert, camel_mix, gigabert_v4_ar, arabert_large_v2, arabert_base_v2 are similar

    # Compute ttest values
    results_df = results_df.T
    ttest_columns = results_df.columns
    print(ttest_columns)
    results = [
        [0 for __ in range(len(ttest_columns))] for _ in range(len(ttest_columns))
    ]
    for row, c1 in enumerate(ttest_columns):
        for col, c2 in enumerate(ttest_columns):
            if c1 != c2:
                pvalue = stats.ttest_rel(results_df[c1], results_df[c2]).pvalue
            else:
                pvalue = np.nan
            results[row][col] = pvalue
            results[col][row] = pvalue

    results = np.array(results)

    annot_values = results.tolist()
    annot_values = [
        [round(v, 3) if not np.isnan(v) else 0 for v in l] for l in annot_values
    ]

    fig, ax = plt.subplots(1, 1, figsize=(10, 10))

    sns.heatmap(
        results < 0.05,
        xticklabels=ttest_columns,
        yticklabels=ttest_columns,
        annot=annot_values,
        fmt="0.3g",
        cmap="Greens",
        square=True,
        ax=ax,
        cbar=False,
    )
    # plt.show()
    plt.savefig("ttest.pdf", bbox_inches="tight")


if __name__ == "__main__":
    main()
