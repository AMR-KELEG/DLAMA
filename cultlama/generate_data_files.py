import time
from constants import *
from query import QueryFactory
from filters import *
import utils
import data_generation_utils
import cultlama_queries
import pandas as pd
from pathlib import Path
import os
import argparse
import logging
import sys
import json

logger = logging.getLogger(__name__)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(levelname)s - %(filename)s:%(funcName)s:line %(lineno)d - %(message)s"
)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)

NO_RETRIES = 5


def query_labels_for_triples(triples_df, q, LIST_OF_LANGS, SAMPLE_SIZE):
    # Start finding all the valid objects and the labels progressively
    BATCH_SIZE = 50
    complete_samples_df = None
    all_subjects_labels = {}
    all_objects_labels = {}
    subjects_uris = triples_df[q.subject_field].unique().tolist()

    for i in range(0, len(subjects_uris), BATCH_SIZE):
        batch_start_index = triples_df[
            triples_df[q.subject_field] == subjects_uris[i]
        ].index[0]
        batch_end_index = triples_df[
            triples_df[q.subject_field]
            == subjects_uris[min(i + BATCH_SIZE - 1, len(subjects_uris) - 1)]
        ].index[-1]

        columns = ["size", q.subject_field, q.object_field] + (
            ["country"] if "country" not in [q.subject_field, q.object_field] else []
        )
        samples_df = triples_df.loc[batch_start_index:batch_end_index, columns]
        logger.info(
            f"Total number of subjects within the batch for getting labels: {len(samples_df[q.subject_field])}"
        )

        samples_df.reset_index(drop=True, inplace=True)
        # TODO: Augment with page views as well?

        # Repeat the query to get all the valid objects!
        batch_subjects_uris = samples_df[q.subject_field].unique().tolist()
        samples_query = QueryFactory().create_query(
            q.relation_id,
            q.subject_field,
            q.object_field,
            q.domain,
            WORLDWIDE,
            q.region_name,
            q.sorting_function,
        )
        samples_query.add_subjects_filter(batch_subjects_uris)
        samples_data = samples_query.get_data(find_count=False)

        # Use the same order based on the size of the Wikipedia articles
        samples_data = sorted(
            samples_data,
            key=lambda sample: batch_subjects_uris.index(
                sample[samples_query.subject_field]
            ),
        )
        samples_df = pd.DataFrame(samples_data)
        samples_df.drop(["size"], inplace=True, axis=1)
        samples_df = pd.merge(
            samples_df,
            triples_df[
                [q.subject_field, "size"]
                + (
                    ["country"]
                    if "country" not in [q.subject_field, q.object_field]
                    else []
                )
            ],
            on=q.subject_field,
            how="left",
        )

        # Query the Wikidata labels
        subjects_ids = samples_df[q.subject_field].tolist()
        objects_ids = samples_df[q.object_field].tolist()
        subjects_labels = utils.get_wikidata_labels(subjects_ids, LIST_OF_LANGS)
        objects_labels = utils.get_wikidata_labels(objects_ids, LIST_OF_LANGS)

        # Add the labels to their respective dictionaries
        all_subjects_labels = dict(
            list(all_subjects_labels.items()) + list(subjects_labels.items())
        )
        all_objects_labels = dict(
            list(all_objects_labels.items()) + list(objects_labels.items())
        )

        # Drop the rows having missing labels in any of the languages specified
        samples_df["sub_label_missing"] = samples_df[q.subject_field].apply(
            lambda uri: any(
                [subjects_labels[uri][lang] == None for lang in LIST_OF_LANGS]
            )
        )
        samples_df["obj_label_missing"] = samples_df[q.object_field].apply(
            lambda uri: any(
                [objects_labels[uri][lang] == None for lang in LIST_OF_LANGS]
            )
        )
        samples_df = samples_df.loc[
            ~(samples_df["sub_label_missing"] | samples_df["obj_label_missing"]), :,
        ]

        logger.info(
            f"Number of subjects within the batch after dropping entities with missing labels: {len(samples_df[q.subject_field].unique())}"
        )

        if i == 0:
            complete_samples_df = samples_df
        else:
            complete_samples_df = pd.concat([complete_samples_df, samples_df])

        # Pick the top SAMPLE_SIZE tuples in case the queried tuples exceed the limit
        if len(set(complete_samples_df[q.subject_field].tolist())) > SAMPLE_SIZE:
            # Find the number of rows to have SAMPLE_SIZE unique subjects
            size_lower, size_upper = 1, complete_samples_df.shape[0]
            while size_lower < size_upper:
                size_mid = (size_lower + size_upper) // 2 + (
                    size_lower + size_upper
                ) % 2
                n_subjects_till_mid = len(
                    set(complete_samples_df.head(size_mid)[q.subject_field].tolist())
                )
                if n_subjects_till_mid > SAMPLE_SIZE:
                    size_upper = size_mid - 1
                else:
                    size_lower = size_mid

            n_subjects = (size_lower + size_upper) // 2 + (size_lower + size_upper) % 2
            complete_samples_df = complete_samples_df.head(n=n_subjects)
            break

    return complete_samples_df, all_subjects_labels, all_objects_labels


def main(
    REGION, SAMPLE_SIZE, REGION_NAME, RELATIONS_SUBSET, LIST_OF_LANGS, sorting_function
):
    # Create output data files
    BASE_DATA_DIR = str(Path("data", "cultlama_raw"))
    DATA_DUMP_DIR = str(Path("data", "cultlama_dump"))
    for lang in LIST_OF_LANGS:
        os.makedirs(Path(BASE_DATA_DIR, lang), exist_ok=True)
    os.makedirs(DATA_DUMP_DIR, exist_ok=True)

    for q in cultlama_queries.populate_queries(REGION, REGION_NAME, sorting_function):
        if RELATIONS_SUBSET and q.relation_id not in RELATIONS_SUBSET:
            continue
        logger.info(
            f"Querying data for '{q.relation_id}_{q.domain}_{q.region_name}.jsonl'"
        )
        start_time = time.time()
        data = q.get_data(find_count=False, no_retries=NO_RETRIES)

        # Form a dataframe to make it easier to add columns
        df = pd.DataFrame(data)

        #  Filter out Wikidata triples having no articles on Wikipedia
        df = df[df["size"] != 0].reset_index(drop=True)

        # Sort the triples using the articles' sizes
        df.sort_values(by="size", ascending=False, inplace=True)

        logger.info(f"Total number of subjects: {len(df[q.subject_field].unique())}")
        df.reset_index(drop=True, inplace=True)

        # Dump the raw data to a jsonl file
        filename = Path(
            DATA_DUMP_DIR, f"{q.relation_id}_{q.domain}_{q.region_name}.jsonl",
        )
        with open(filename, "w") as f:
            for line in json.loads(df.to_json(orient="records")):
                f.write(json.dumps(line) + "\n")

        (
            complete_samples_df,
            all_subjects_labels,
            all_objects_labels,
        ) = query_labels_for_triples(df, q, LIST_OF_LANGS, SAMPLE_SIZE)
        logger.info(
            f"Final number of subjects: {len(complete_samples_df[q.subject_field].unique())}"
        )

        # Export the triples to jsonl files
        for lang in LIST_OF_LANGS:
            filename = Path(
                BASE_DATA_DIR,
                lang,
                f"{q.relation_id}_{q.domain}_{q.region_name}.jsonl",
            )
            complete_samples_df["sub_label"] = complete_samples_df[
                q.subject_field
            ].apply(lambda uri: all_subjects_labels[uri][lang])
            complete_samples_df["obj_label"] = complete_samples_df[
                q.object_field
            ].apply(lambda uri: all_objects_labels[uri][lang])

            data_generation_utils.generate_facts_jsonl(complete_samples_df, q, filename)

            logger.info(
                f"Successfully generated '{q.relation_id}_{q.domain}_{q.region_name}.jsonl'"
            )
        logger.info(f"Time elapsed is: {time.time() - start_time} seconds")


if __name__ == "__main__":
    REGIONS = {
        "ARAB_REGION": ARAB_REGION,
        "WORLDWIDE": WORLDWIDE,
        "EASTERN_ASIA": EASTERN_ASIA,
        "SOUTHERN_EAST_ASIA": SOUTHERN_EAST_ASIA,
        "JAPAN": JAPAN,
        "CHINA": CHINA,
        "ASIA": ASIA,
        "WESTERN_EUROPEAN": WESTERN_EUROPEAN,
        "SOUTH_WESTERN_EUROPE": SOUTH_WESTERN_EUROPE,
        "NORTH_AMERICA_AND_AUSTRALIA": NORTH_AMERICA_AND_AUSTRALIA,
        "SOUTH_AMERICA": SOUTH_AMERICA,
        "SOUTHERN_AFRICA": SOUTHERN_AFRICA,
        "WESTERN_COUNTRIES": WESTERN_COUNTRIES,
    }

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--region",
        choices=list(REGIONS.keys()),
        required=True,
        help="The region representing the facts.",
    )
    parser.add_argument(
        "--n",
        type=int,
        default=100,
        required=True,
        help="Number of samples to query for each relation.",
    )
    parser.add_argument(
        "--rel",
        nargs="*",
        default=None,
        help="A white-space separated list of subset Wikidata relations to query (e.g.: 'P17 P20')",
    )
    parser.add_argument(
        "--langs",
        nargs="*",
        default=None,
        required=True,
        help="A white-space separated list of Wikipedia languages (e.g.: 'en ko')",
    )
    parser.add_argument(
        "--sorting_function",
        default="size",
        choices=["size", "edits"],
        required=True,
        help="The metric used to sort the queried triples before sampling",
    )
    args = parser.parse_args()

    main(
        REGION=REGIONS[args.region],
        SAMPLE_SIZE=args.n,
        REGION_NAME=args.region,
        RELATIONS_SUBSET=args.rel,
        LIST_OF_LANGS=args.langs,
        sorting_function=args.sorting_function,
    )
