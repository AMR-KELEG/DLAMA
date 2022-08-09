# Copyright (c) Facebook, Inc. and its affiliates.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#
import argparse
from copy import deepcopy
from modules import build_model_by_name
import pprint
import json
import sys
from model_config import LANG_TO_LMs
from utils import load_jsonl
from eval_utils import run_evaluation
from pathlib import Path
import glob


def run_experiments(
    relations_templates,
    data_path_pre,
    language,
    input_param={
        "lm": "bert",
        "label": "bert_large",
        "model_name": "bert",
        "bert_model_name": "bert-large-cased",
        "bert_model_dir": "pre-trained_language_models/bert/cased_L-24_H-1024_A-16",
    },
    use_cultlama=False,
):
    """
    TODO

    Args:
    - relations_templates: List of strings representing prompts
    - input_param: A model configuration dictionary
    """
    pp = pprint.PrettyPrinter(width=41, compact=True)

    # Load the model
    model = build_model_by_name(
        lm=input_param["model_name"], hf_model_name=input_param["bert_model_name"]
    )

    LOGDIR = "output" if not use_cultlama else "output_cultlama"
    # Add the configuration parameters into a dictionary
    BASIC_CONFIGURATION_PARAMETERS = {
        "template": "",
        "batch_size": 4,
        "logdir": LOGDIR,
        "lowercase": False,
        "threads": -1,
        "interactive": False,
    }
    # Add model information to the configuration parameters
    BASIC_CONFIGURATION_PARAMETERS.update(input_param)

    for relation in relations_templates:
        relation_name = relation["relation"]

        # Build the list of candidate objects
        if use_cultlama:
            # Load all objects from cultlama
            data_files = glob.glob(
                f"./data/cultlama/{language}/{relation_name}_*.jsonl"
            )
        else:
            # Load all objects from mlama
            data_files = glob.glob(f"./data/mlama1.1/{language}/{relation_name}.jsonl")

        relation_triples = []
        for file in set(data_files):
            with open(file, "r") as f:
                relation_triples += [json.loads(line) for line in f]

        # TODO: Augment valid objects with normalized values
        candidate_objects = [
            triple["obj_label"]
            if type(triple["obj_label"]) == list
            else [triple["obj_label"]]
            for triple in relation_triples
        ]
        candidate_objects = sorted(set(sum(candidate_objects, [])))

        configuration_parameters = deepcopy(BASIC_CONFIGURATION_PARAMETERS)
        configuration_parameters["template"] = relation["template"]

        if use_cultlama:
            # The relation can have multiple subsets
            relation_files = str(Path(data_path_pre, f"{relation_name}_*.jsonl"))
        else:
            relation_files = str(Path(data_path_pre, f"{relation_name}.jsonl"))

        if glob.glob(relation_files):
            configuration_parameters["dataset_filename"] = relation_files
        else:
            print("Relation {} excluded.".format(relation["relation"]))
            continue

        configuration_parameters["full_logdir"] = str(
            Path(
                LOGDIR,
                "results",
                configuration_parameters["label"],
                language,
                relation["relation"],
            )
        )

        pp.pprint(relation)
        print(configuration_parameters)

        # TODO: Why is this parsing done?!
        args = argparse.Namespace(**configuration_parameters)

        max_length = max(
            [len(model.tokenizer.tokenize(obj)) for obj in candidate_objects]
        )

        # Split objects according to their length?!
        dict_num_mask = {}
        for l in range(1, max_length + 1):
            dict_num_mask[l] = {}

        #  Form list of candidates split by length
        for obj in candidate_objects:
            # TODO: What is get_id?
            dict_num_mask[len(model.tokenizer.tokenize(obj))][obj] = model.get_id(obj)

        # Run the experiments
        # TODO: Don't send the whole args dictionary
        run_evaluation(args, max_length, dict_num_mask, model=model)


def run_experiment_on_list_of_lms(
    relations_templates, data_path_pre, language, language_models, use_cultlama
):
    for lm in language_models:
        print(lm["label"])
        try:
            run_experiments(
                relations_templates,
                data_path_pre,
                language,
                input_param=lm,
                use_cultlama=use_cultlama,
            )
        except Exception as e:
            print(e)
            print(f'Failed for: {lm["label"]}', file=sys.stderr)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", "-l", type=str, default="fr", help="language")
    parser.add_argument(
        "--cultlama", "-c", action="store_true", help="Evaluate on cultlama data",
    )
    parser.add_argument(
        "--rel",
        nargs="*",
        default=None,
        help="Specify a set of Wikidata relations to evaluate on",
    )
    parser.add_argument(
        "--dataset_dir",
        required=True,
        help="Directory containing jsonl files of tuples",
    )

    args = parser.parse_args()
    language = args.lang
    language_models = LANG_TO_LMs[language]

    data_path_pre = str(Path("./data/mlama1.1/", language))

    # Load the templates file and point to other files
    # TODO: Make a change here to use another templates file here
    # after adding an argument
    relations_templates = load_jsonl(Path(data_path_pre, "templates.jsonl"))

    if args.rel:
        relations_templates = [
            relation_template
            for relation_template in relations_templates
            if relation_template["relation"] in args.rel
        ]

    run_experiment_on_list_of_lms(
        relations_templates,
        str(Path(args.dataset_dir, language)),
        language,
        language_models,
        use_cultlama=args.cultlama,
    )


if __name__ == "__main__":
    main()
