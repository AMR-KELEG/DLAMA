#  Translate a DLAMA dataset into another language
import copy
import glob
import json
from tqdm import tqdm
from utils import get_wikidata_labels
from os import makedirs
from pathlib import Path
from argparse import ArgumentParser


def load_file(filename):
    with open(filename, "r") as f:
        data = [json.loads(l) for l in f]
    return data


def main(BASE_DIR, other_lang):
    """Translate data files of DLAMA into a new language"""
    makedirs(str(Path(BASE_DIR, other_lang)), exist_ok=True)
    files = sorted([f for f in glob.glob(str(Path(BASE_DIR, "en", "*")))])

    for file in tqdm(files):
        samples = load_file(file)
        subjects_uris = [s["sub_uri"] for s in samples]
        objects_uris = [obj_uri for s in samples for obj_uri in s["obj_uri"]]

        # Find translation dictionaries
        subjects_labels = get_wikidata_labels(subjects_uris, [other_lang])
        objects_labels = get_wikidata_labels(objects_uris, [other_lang])

        # Translate samples
        translated_samples = []
        for sample in samples:
            sub_uri, obj_uris = sample["sub_uri"], sample["obj_uri"]
            if not subjects_labels[sub_uri]:
                # TODO: Generate an error message instead of silently dropping the triple
                continue
            translated_sample = copy.deepcopy(sample)
            translated_sample["sub_label"] = subjects_labels[sub_uri][other_lang]
            obj_uris = [obj_uri for obj_uri in obj_uris if obj_uri in objects_labels]
            translated_sample["obj_label"] = [
                objects_labels[obj_uri][other_lang]
                for obj_uri in obj_uris
                if objects_labels[obj_uri][other_lang]
            ]
            translated_sample["obj_uri"] = [
                obj_uri for obj_uri in obj_uris if objects_labels[obj_uri][other_lang]
            ]
            if not translated_sample["obj_uri"]:
                # TODO: Generate an error message instead of silently dropping the triple
                continue
            translated_samples.append(translated_sample)

        # Export translated file
        filename = file.split("/")[-1]
        output_filename = str(Path(BASE_DIR, other_lang, filename))
        with open(output_filename, "w") as f:
            for sample in translated_samples:
                f.write(json.dumps(sample, ensure_ascii=False))
                f.write("\n")


if __name__ == "__main__":
    args_parser = ArgumentParser("Translate the labels of a dataset to a new langauges")
    args_parser.add_argument(
        "--lang", required=True, help="New language to translate labels to"
    )
    args_parser.add_argument(
        "--dir", required=True, help="Base directory of the dataset"
    )
    args = args_parser.parse_args()

    main(BASE_DIR=args.dir, other_lang=args.lang)
