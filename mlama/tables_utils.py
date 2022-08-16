import glob
from pathlib import Path
from metrics_utils import load_model_results, compute_P_scores

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
