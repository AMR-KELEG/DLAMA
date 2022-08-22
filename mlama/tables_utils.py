import re
import glob
import pandas as pd
from pathlib import Path
from natsort import natsorted
from metrics_utils import load_model_results, compute_P_scores
from dataset_analysis_utils import (
    compute_entropy,
    normalize_region_name,
    load_jsonl_file,
    load_predicates_in_dataset,
    find_most_common_object,
    load_wikidata_predicates_names,
)

#  TODO: Merge these functions into 1
def generate_stats_table(results_dir, lang, aggregation_method):
    """
    Generate a list of the overall performance of models for prompts of a specific language as in Table 1,2.
    """
    models_names = [
        Path(p).parent.name for p in glob.glob(str(Path(results_dir, "*", lang)))
    ]
    model_results = []
    for model_name in models_names:
        results_df = load_model_results(results_dir, model_name=model_name, lang=lang)
        scores = compute_P_scores(results_df, aggregation_method=aggregation_method)
        scores["model_name"] = model_name
        model_results.append(scores)
    return sorted(model_results, key=lambda d: d["P@1_aggregated"])


def generate_detailed_predicate_table(results_dir, lang, model_name):
    model_results = []

    results_df = load_model_results(results_dir, model_name=model_name, lang=lang)
    scores = compute_P_scores(results_df, aggregation_method="split_by_domain")

    model_results.append(scores)
    return scores


def generate_entropy_table(dataset_dir):
    """
    Compute the least possible entropy of the different relation predicates within a dataset.
    """
    predicates = load_predicates_in_dataset(dataset_dir)

    entropy_values = []
    for predicate in predicates:
        predicate_file_paths = [p for p in Path(dataset_dir).glob(f"{predicate}_*")]
        triples = sum(
            [load_jsonl_file(file_path) for file_path in predicate_file_paths], []
        )
        entropy_values.append(
            {
                "Predicate": predicate,
                "Entropy": round(compute_entropy(triples), 3),
                "Support": len(triples),
            }
        )
    entropy_df = pd.DataFrame(entropy_values)
    return entropy_df


def generate_detailed_entropy_table(dataset_dir):
    # TODO: Avoid hardcoding the domain names
    DOMAINS = [
        "sports",
        "politics",
        "music",
        "cinema_and_theatre",
        "history",
        "geography",
    ]

    predicates = load_predicates_in_dataset(dataset_dir)
    relation_predicate_id_to_name = load_wikidata_predicates_names()
    entropy_values = []
    for domain in DOMAINS:
        domain_file_information = []
        for filename in Path(dataset_dir).glob(f"*_{domain}_*"):
            values = list(
                re.findall(r"^(P[0-9]+)_([a-z_]+)_([A-Z_]+).jsonl", filename.name)[0]
            )
            values.append(normalize_region_name(values[-1]))
            values.append(str(filename))
            domain_file_information.append(values)
        predicates = [
            file_information[0] for file_information in domain_file_information
        ]
        regions = [file_information[3] for file_information in domain_file_information]
        for predicate in natsorted(set(predicates)):
            predicate_values = {}
            predicate_values["domain"] = domain
            predicate_values[
                "predicate"
            ] = f"{predicate} ({relation_predicate_id_to_name.get(predicate, predicate)})"
            for region in sorted(set(regions)):
                filepaths = [
                    file_information[-1]
                    for file_information in domain_file_information
                    if predicate == file_information[0]
                    and region == file_information[3]
                ]
                triples = sum([load_jsonl_file(filepath) for filepath in filepaths], [])
                predicate_values[f"entropy_{region}"] = round(
                    compute_entropy(triples), 3
                )
                #             predicate_values[f"support_{region}"] = len(triples)
                predicate_values[f"most_common_{region}"] = find_most_common_object(
                    triples
                )

            filepaths = [
                file_information[-1]
                for file_information in domain_file_information
                if predicate == file_information[0]
            ]
            triples = sum([load_jsonl_file(filepath) for filepath in filepaths], [])
            predicate_values[f"entropy_aggregated"] = round(compute_entropy(triples), 3)
            #         predicate_values[f"support_aggregated"] = len(triples)
            predicate_values[f"most_common_aggregated"] = find_most_common_object(
                triples
            )
            entropy_values.append(predicate_values)
    entropy_df = pd.DataFrame(entropy_values)
    return entropy_df
