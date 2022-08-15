import glob
from pathlib import Path
from metrics_utils import load_model_results, compute_P_scores

#  TODO: Merge these functions into 1
def generate_aggregated_stats_table(results_dir, lang):
    """
    Generate a list of the overall performance of models for prompts of a specific language as in Table 1.
    """
    models_names = [
        Path(p).parent.name for p in glob.glob(str(Path(results_dir, "*", lang)))
    ]
    model_results = []
    for model_name in models_names:
        results_df = load_model_results(results_dir, model_name=model_name, lang=lang)
        scores = compute_P_scores(results_df, aggregation_method="all")
        scores["model_name"] = model_name
        model_results.append(scores)
    return sorted(model_results, key=lambda d: d["P@1_aggregated"])


def generate_region_stats_table(results_dir, lang):
    """
    Generate a list of the performance of models split by Region for prompts of a specific language as in Table 2.
    """
    models_names = [
        Path(p).parent.name for p in glob.glob(str(Path(results_dir, "*", lang)))
    ]
    model_results = []
    for model_name in models_names:
        results_df = load_model_results(results_dir, model_name=model_name, lang=lang)
        scores = compute_P_scores(results_df, aggregation_method="split_by_region")
        scores["model_name"] = model_name
        model_results.append(scores)
    return sorted(model_results, key=lambda d: d["P@1_aggregated"])
