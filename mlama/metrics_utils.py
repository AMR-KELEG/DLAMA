import glob
import re
import pickle
import numpy as np
import pandas as pd
from pathlib import Path

#  TODO: Load this list from the constants.py file within cultlama
DOMAINS = [
    "sports",
    "politics",
    "music",
    "cinema_and_theatre",
    "history",
    "science",
    "geography",
]


def normalize_region_name(region):
    """Unify subregion names into a single normalized name."""
    # TODO: Fix this!
    if any([r in region for r in ["ASIA", "JAPAN", "CHINA"]]):
        return "ASIA"
    if "ARAB" in region:
        return region
    if "SOUTH_AMERICA" in region:
        return "SOUTH_AMERICA"
    return "WEST"


def load_predicate_results(results_dir, relation_id, model_name, lang):
    """
    Return a dataframe of a model's predictions for a specific relation in a specific language.
    """

    def compute_probs(logits):
        exps = np.exp(logits)
        return exps / exps.sum()

    # Load the pickle file
    file_path = str(Path(results_dir, model_name, lang, relation_id, "result.pkl"))
    with open(file_path, "rb") as f:
        results = pickle.load(f)

    predictions_list = []

    for sample in results["list_of_results"]:
        # Remove the "_REGION" from the sample name
        sample_id = re.sub(r"_REGION", "", sample["uuid"])
        fields = sample_id.split("_")

        # Infer the domain from the sample ID
        domains = [d for d in DOMAINS if d in sample_id]
        assert len(domains) == 1
        domain = domains[0]

        region = (
            normalize_region_name(fields[-2])
            if not "SOUTH_AMERICA" in sample_id
            else "SOUTH_AMERICA"
        )
        sample_id = int(fields[-1])
        try:
            rank = sample["masked_topk"]["ranks"][0]
        except Exception as e:
            from pprint import pprint

            pprint(sample)
            exit(0)
        probs = compute_probs(sample["masked_topk"]["probs"])

        predictions_list.append(
            {
                "region": region,
                "domain": domain,
                "predicate": relation_id,
                "id": sample_id,
                "rank": rank,
                "subject": sample["sample"]["sub_label"],
                "valid_objects": sample["sample"]["obj_label"],
                "predictions": sample["masked_topk"]["predicted"],
                "probabilities": probs,
            }
        )

    df = pd.DataFrame(predictions_list)

    return df


def load_model_results(results_dir, model_name, lang, relation_predicates=None):

    #  Infer the predicates if not provided
    if not relation_predicates:
        relation_predicates = [
            Path(p).name
            for p in glob.glob(str(Path(results_dir, model_name, lang, "*")))
        ]

    predicates_results_df = [
        load_predicate_results(results_dir, predicate, model_name, lang)
        for predicate in relation_predicates
    ]

    return pd.concat(predicates_results_df)


def compute_P_at_1(df):
    """Compute P@1 score for a dataframe of predictions."""
    number_correct = int((df["rank"] == 0).sum())
    n_samples = int(df.shape[0])
    return round(100 * (number_correct / n_samples), 3)


def compute_P_scores(
    df, aggregation_method="split_by_predicate", regions=None, skip_predicates=["P527"]
):
    """Aggregate scores from a results dataframe for different relation predicates."""

    assert aggregation_method in [
        "all",
        "split_by_predicate",
        "split_by_region",
        "split_by_domain",
    ]

    # Skip predicates
    if skip_predicates:
        df = df[~df["predicate"].isin(skip_predicates)]

    if aggregation_method == "all":
        return {"P@1_aggregated": compute_P_at_1(df), "Support_aggregated": df.shape[0]}

    #  Infer regions in case they are not provided
    if not regions:
        regions = sorted(df["region"].unique())
    else:
        assert all([region in sorted(df["region"].unique()) for region in regions])

    if aggregation_method == "split_by_region":
        scores = {}
        for region in regions:
            region_df = df[df["region"] == region]

            scores[f"P@1_{region}"] = compute_P_at_1(region_df)
            scores[f"Support_{region}"] = region_df.shape[0]
        scores["P@1_aggregated"] = compute_P_at_1(df)
        scores["Support_aggregated"] = df.shape[0]
        return scores

    relation_predicates = [
        p for p in sorted(df["predicate"].unique()) if p not in skip_predicates
    ]

    if aggregation_method == "split_by_region":
        results = []
        for relation_predicate in relation_predicates:
            relation_predicate_metrics = {}
            relation_predicate_metrics["predicate"] = relation_predicate

            scores = {}
            for region in regions:
                region_df = df[
                    (df["predicate"] == relation_predicate) & (df["region"] == region)
                ]
                scores[f"P@1_{region}"] = compute_P_at_1(region_df)
                scores[f"Support_{region}"] = region_df.shape[0]

            relation_df = df[df["predicate"] == relation_predicate]
            scores["P@1_aggregated"] = compute_P_at_1(relation_df)
            scores["Support_aggregated"] = relation_df.shape[0]

            relation_predicate_metrics["P@1"] = scores
            results.append(relation_predicate_metrics)

        return results

    if aggregation_method == "split_by_domain":
        pass
