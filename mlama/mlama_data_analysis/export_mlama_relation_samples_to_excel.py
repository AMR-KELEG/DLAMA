#!/usr/bin/env python
import re
import json
import random
import pandas as pd

if __name__ == "__main__":
    templates = {}

    for lang in ["ar", "en"]:
        #  Load the templates
        with open(f"../data/mlama1.1/{lang}/templates.jsonl", "r") as f:
            for l in f:
                template_info = json.loads(l)
                template_text = template_info["template"]
                relation = template_info["relation"]

                if not relation in templates:
                    templates[relation] = {}

                templates[relation][f"template_{lang}"] = template_text
                try:
                    # Fill in the template with one sample
                    with open(f"../data/mlama1.1/{lang}/{relation}.jsonl", "r") as f:
                        triple_info = json.loads(f.readline())
                    template_text = re.sub(
                        r"\[X\]", triple_info["sub_label"], template_text
                    )
                    template_text = re.sub(
                        r"\[Y\]", triple_info["obj_label"], template_text
                    )
                    sub_uri = triple_info["sub_uri"]
                    obj_uri = triple_info["obj_uri"]
                except:
                    print(f"Missing data for relation {relation} in {lang}")
                    template_text = None
                    sub_uri = None
                    obj_uri = None
                templates[relation][f"template_{lang}_sample"] = template_text
                templates[relation][f"sub_uri"] = sub_uri
                templates[relation][f"obj_uri"] = obj_uri

    # Load the list of subjects/ objects
    for lang in ["ar", "en"]:
        with open(f"../data/TREx_multilingual_objects/{lang}.json", "r") as f:
            data = json.load(f)
            for relation in data.keys():
                if relation in templates:
                    random.shuffle(data[relation]["subjects"])
                    random.shuffle(data[relation]["objects"])
                    templates[relation][f"subjects_{lang}"] = " | ".join(
                        data[relation]["subjects"]
                    )
                    templates[relation][f"objects_{lang}"] = " | ".join(
                        data[relation]["objects"]
                    )

    df = pd.DataFrame(templates).T
    df.reset_index(inplace=True)
    df.rename(columns={"index": "relation"}, inplace=True)

    output_df = df.loc[
        :,
        [
            "relation",
            "sub_uri",
            "obj_uri",
            "template_ar",
            "template_ar_sample",
            "template_en",
            "template_en_sample",
            "objects_ar",
            "objects_en",
            "subjects_ar",
            "subjects_en",
        ],
    ]

    output_df.to_excel("templates_info.xlsx", index=False)
