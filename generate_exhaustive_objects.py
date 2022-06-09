import os
import re
import glob
import json
import time
import constants
import pandas as pd
from tqdm import tqdm
from pathlib import Path
import utils
import data_generation_utils
import argparse


def generate_exhaustive_objects_lists(LIST_OF_RELATIONS):
    BASE_DATA_DIR = str(Path("data", "cultlama_raw"))
    OUTPUT_DATA_DIR = str(Path("data", "cultlama"))
    for lang in constants.LANGS:
        os.makedirs(Path(OUTPUT_DATA_DIR, lang), exist_ok=True)

    # TODO: Don't repeat the same query multiple times for each language!
    for lang in constants.LANGS:
        files = glob.glob(str(Path(BASE_DATA_DIR, lang, "*")))
        relations = [re.findall(r"P[0-9]+", file)[0] for file in files]
        relations = [r for r in relations if r in LIST_OF_RELATIONS]

        for relation in tqdm(
            sorted(set(relations)), desc=f"Generate relation's '{lang}' files"
        ):
            relation_files = glob.glob(str(Path(BASE_DATA_DIR, lang, f"{relation}_*")))
            relation_triples = []
            for relation_file in relation_files:
                with open(relation_file, "r") as f:
                    relation_triples += [json.loads(l) for l in f]

            samples_df = pd.DataFrame(relation_triples)
            objects_uris = [o for o_l in samples_df["obj_uri"].tolist() for o in o_l]
            objects_labels = [
                o for o_l in samples_df["obj_label"].tolist() for o in o_l
            ]

            if relation in ["P19", "P20"]:
                NO_OF_RETRIES = 5
                while NO_OF_RETRIES:
                    try:
                        # Find all intermediate cities as well that aren't countries
                        step = 50
                        unique_object_uris = sorted(set(objects_uris))
                        objects_ancestors_dicts = [
                            data_generation_utils.find_macro_terrotories(
                                unique_object_uris[i : i + step]
                            )
                            for i in range(0, len(unique_object_uris), step)
                        ]

                        objects_ancestors_dict = {
                            obj_uri: d[obj_uri]
                            for d in objects_ancestors_dicts
                            for obj_uri in d
                        }
                        objects_uris = [
                            uri
                            for k in objects_ancestors_dict
                            for uri in objects_ancestors_dict[k]
                        ]
                        objects_labels = utils.get_wikidata_labels(objects_uris)

                        #  Some of the labels will be missing!
                        uris_to_labels = {
                            uri: objects_labels[uri][lang]
                            for uri in objects_uris
                            if objects_labels.get(uri, {}).get(lang, None)
                        }
                        objects_ancestors_dict = {
                            obj_uri: [
                                ancestor
                                for ancestor in objects_ancestors_dict[obj_uri]
                                if ancestor in uris_to_labels
                            ]
                            for obj_uri in objects_ancestors_dict
                        }
                        break
                    except:
                        print("Rate limited")
                        time.sleep(5)
                        NO_OF_RETRIES -= 1

            else:
                objects_ancestors_dict = data_generation_utils.form_objects_ancestors_lists(
                    set(objects_uris)
                )

                uris_to_labels = {
                    uri: label for uri, label in zip(objects_uris, objects_labels)
                }

            for relation_file in relation_files:
                with open(relation_file, "r") as f:
                    with open(
                        Path(OUTPUT_DATA_DIR, lang, Path(relation_file).name), "w"
                    ) as of:
                        for l in f:
                            triple = json.loads(l)
                            exhaustive_objects_uris = sorted(
                                set(
                                    sum(
                                        [
                                            objects_ancestors_dict[uri]
                                            for uri in triple["obj_uri"]
                                        ],
                                        [],
                                    )
                                )
                            )

                            exhaustive_objects_labels = [
                                uris_to_labels[uri] for uri in exhaustive_objects_uris
                            ]
                            triple["obj_uri"] = exhaustive_objects_uris
                            triple["obj_label"] = exhaustive_objects_labels
                            of.write(json.dumps(triple, ensure_ascii=False))
                            of.write("\n")


def main(LIST_OF_RELATIONS):
    generate_exhaustive_objects_lists(LIST_OF_RELATIONS)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Generate a list of exhaustive objects")
    parser.add_argument(
        "--rel",
        nargs="*",
        default=None,
        help="A white-space separated list of subset Wikidata relations to query (e.g.: 'P17 P20')",
    )
    args = parser.parse_args()
    main(args.rel)
