#!/usr/bin/env python
import re
import json
import pandas as pd
from glob import glob
from tqdm import tqdm

for filename in glob("json-files/*.json"):
    with open(filename, "r") as f:
        data = json.load(f)

    for data_sample in tqdm(data):
        for triple in data_sample["triples"]:
            subj = re.findall(r"Q\d+", triple["subject"]["uri"])
            pred = re.findall(r"P\d+", triple["predicate"]["uri"])
            obj = re.findall(r"Q\d+", triple["object"]["uri"])

            # Make sure the predicate information is not missing
            if subj and pred and obj:
                with open(f"parsed-data/{pred[0]}.jsonl", "a") as f:
                    f.write(json.dumps({"sub_uri": subj[0], "obj_uri": obj[0]}) + "\n")
