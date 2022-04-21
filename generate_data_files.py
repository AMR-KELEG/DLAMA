import time
from constants import *
from filters import *
import utils
import data_generation_utils
from query import Query, QueryFactory
import pandas as pd
from pathlib import Path
import os
import argparse
import logging
import sys

logger = logging.getLogger(__name__)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(levelname)s - %(filename)s:%(funcName)s:line %(lineno)d - %(message)s"
)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)

REMAINING_RETRIES = 5


def main(REGION, SAMPLE_SIZE, REGION_NAME, RELATIONS_SUBSET):
    # Create output data files
    BASE_DATA_DIR = str(Path("data", "cultlama_raw"))
    for lang in LANGS:
        os.makedirs(Path(BASE_DATA_DIR, lang), exist_ok=True)

    ### ALL DOMAINS ###
    queries = []
    query_factory = QueryFactory()
    for domain in [CINEMA_AND_THEATRE, POLITICS, SPORTS, MUSIC]:
        # Country of citizenship
        q27 = query_factory.create_query(
            "P27",
            subject_field=PERSON,
            object_field=COUNTRY,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        q27.add_filter(PERSON, OCCUPATION)
        q27.add_filter(OCCUPATION, domain)
        q27.add_filter("region_country", REGION)
        queries.append(q27)

        # Occupation
        q106 = query_factory.create_query(
            "P106",
            subject_field=PERSON,
            object_field=OCCUPATION,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        q106.add_filter(OCCUPATION, domain)
        q106.add_filter(PERSON, "country_of_citizenship")
        q106.add_filter("region_country", REGION)
        queries.append(q106)

    ### Entertainment ###
    # Country of origin
    for domain in [MUSIC, CINEMA_AND_THEATRE]:
        p495 = query_factory.create_query(
            "P495",
            subject_field=PIECE_OF_WORK,
            object_field=COUNTRY,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        p495.add_filter("region_country", REGION)
        p495.add_filter(PIECE_OF_WORK, domain)
        queries.append(p495)

    q1303 = query_factory.create_query(
        "P1303",
        subject_field=PERSON,
        object_field=INSTRUMENT,
        domain=MUSIC,
        region=REGION,
        region_name=REGION_NAME,
    )
    q1303.add_filter(PERSON, "country_of_citizenship")
    q1303.add_filter("region_country", REGION)
    q1303.add_filter(MUSIC, "not_voice")
    queries.append(q1303)

    q364 = query_factory.create_query(
        "P364",
        subject_field=PIECE_OF_WORK,
        object_field=LANGUAGE,
        domain=CINEMA_AND_THEATRE,
        region=REGION,
        region_name=REGION_NAME,
    )
    q364.add_filter(PIECE_OF_WORK, "country_of_origin")
    q364.add_filter("region_country", REGION)
    queries.append(q364)

    ### SPORTS ###
    # Country of sports clubs
    q17 = query_factory.create_query(
        "P17",
        subject_field=CLUB,
        object_field=COUNTRY,
        domain=SPORTS,
        region=REGION,
        region_name=REGION_NAME,
    )
    q17.add_filter("region_country", REGION)
    q17.add_filter(SPORTS, "football")
    queries.append(q17)

    ### GEOGRAPHY ###
    for region, region_name in zip([REGION, WORLDWIDE], [REGION_NAME, "WORLDWIDE"]):
        # Capital
        q36 = query_factory.create_query(
            "P36",
            subject_field=COUNTRY,
            object_field=CITY,
            domain=GEOGRAPHY,
            region=region,
            region_name=region_name,
        )
        if region != WORLDWIDE:
            q36.add_filter("region_country", region)
        q36.add_filter(GEOGRAPHY, "not_lost_city")
        q36.add_filter(GEOGRAPHY, "sovereign_state")
        queries.append(q36)

        # Capital of
        q1376 = query_factory.create_query(
            "P1376",
            subject_field=CITY,
            object_field=COUNTRY,
            domain=GEOGRAPHY,
            region=region,
            region_name=region_name,
        )
        if region != WORLDWIDE:
            q1376.add_filter("region_country", region)
        q1376.add_filter(GEOGRAPHY, "not_lost_city")
        q1376.add_filter(GEOGRAPHY, "sovereign_state")
        queries.append(q1376)

        #  Continent
        q30 = query_factory.create_query(
            "P30",
            subject_field=COUNTRY,
            object_field=CONTINENT,
            domain=GEOGRAPHY,
            region=region,
            region_name=region_name,
        )
        if region != WORLDWIDE:
            q30.add_filter("region_country", region)
        q30.add_filter(GEOGRAPHY, "sovereign_state")
        queries.append(q30)

        # Official lamguage
        q37 = query_factory.create_query(
            "P37",
            subject_field=COUNTRY,
            object_field=LANGUAGE,
            domain=POLITICS,
            region=region,
            region_name=region_name,
        )
        if region != WORLDWIDE:
            q37.add_filter("region_country", region)
        q37.add_filter(GEOGRAPHY, "sovereign_state")
        queries.append(q37)

    for q in queries:
        if RELATIONS_SUBSET and q.relation_id not in RELATIONS_SUBSET:
            continue
        remaining_retries = REMAINING_RETRIES
        while remaining_retries:
            try:
                data = q.get_data(find_count=False)

                # Form a dataframe to make it easier to add columns
                df = pd.DataFrame(data)

                # Sort the triples using the articles' sizes
                df.sort_values(by="size", ascending=False, inplace=True)

                if len(set(df[q.subject_field].tolist())) > SAMPLE_SIZE:
                    # Find the number of rows to have SAMPLE_SIZE unique subjects
                    size_lower, size_upper = 1, df.shape[0]
                    while size_lower < size_upper:
                        size_mid = (size_lower + size_upper) // 2
                        n_subjects_till_mid = len(
                            set(df.head(size_mid)[q.subject_field].tolist())
                        )
                        if n_subjects_till_mid < SAMPLE_SIZE:
                            size_lower = size_mid + 1
                        else:
                            size_upper = size_mid
                    n_subjects = (size_lower + size_upper) // 2
                    # TODO: Think of a better way to keep enough rows for sampling
                    df = df.head(n=n_subjects * 2)

                sample_df = df.loc[
                    :, ["size", q.subject_field, q.object_field,],
                ]
                sample_df.reset_index(drop=True, inplace=True)

                # TODO: Augment with page views as well?

                # Repeat the query to get all the valid objects!
                subjects_uris = sample_df[q.subject_field].unique().tolist()
                samples_query = query_factory.create_query(
                    q.relation_id,
                    q.subject_field,
                    q.object_field,
                    q.domain,
                    WORLDWIDE,
                    q.region_name,
                )
                samples_query.add_subjects_filter(subjects_uris)
                samples_data = samples_query.get_data(find_count=False)

                # Use the same order based on the size of the Wikipedia articles
                samples_data = sorted(
                    samples_data,
                    key=lambda sample: subjects_uris.index(
                        sample[samples_query.subject_field]
                    ),
                )

                # Form a dataframe to make it easier to add columns
                samples_df = pd.DataFrame(samples_data)

                # TODO: Do this progressively
                # Query the Wikidata labels
                subjects_ids = samples_df[samples_query.subject_field].tolist()
                objects_ids = samples_df[samples_query.object_field].tolist()
                subjects_labels = utils.get_wikidata_labels(subjects_ids)
                objects_labels = utils.get_wikidata_labels(objects_ids)

                # Drop the rows having missing labels
                samples_df["sub_label_missing"] = samples_df[
                    samples_query.subject_field
                ].apply(
                    lambda uri: any(
                        [subjects_labels[uri][lang] == None for lang in LANGS]
                    )
                )
                samples_df["obj_label_missing"] = samples_df[
                    samples_query.object_field
                ].apply(
                    lambda uri: any(
                        [objects_labels[uri][lang] == None for lang in LANGS]
                    )
                )
                samples_df = samples_df.loc[
                    ~(
                        samples_df["sub_label_missing"]
                        | samples_df["obj_label_missing"]
                    ),
                    :,
                ]

                # Sample the SAMPLE_SIZE articles with largest Wikidpedia articles
                samples_df = samples_df.head(n=SAMPLE_SIZE)

                # Make the objects a list instead of a single value
                samples_df[samples_query.object_field] = samples_df[
                    samples_query.object_field
                ].apply(lambda o: [o])

                # Export the triples to jsonl files
                for lang in LANGS:
                    filename = Path(
                        BASE_DATA_DIR,
                        lang,
                        f"{q.relation_id}_{q.domain}_{q.region_name}.jsonl",
                    )
                    samples_df["sub_label"] = samples_df[q.subject_field].apply(
                        lambda uri: subjects_labels[uri][lang]
                    )
                    samples_df["obj_label"] = samples_df[q.object_field].apply(
                        lambda uris_list: [
                            objects_labels[uri][lang] for uri in uris_list
                        ]
                    )
                    data_generation_utils.generate_facts_jsonl(samples_df, q, filename)

                logger.info(
                    f"Successfully generated '{q.relation_id}_{q.domain}_{q.region_name}.jsonl'"
                )
                break
            except Exception as e:
                logger.error(e)
                remaining_retries -= 1
                # Use delay of 30 seconds before retrying!
                time.sleep(30)
                if remaining_retries == 0:
                    logger.info(
                        f"Failed to generate '{q.relation_id}_{q.domain}_{q.region_name}.jsonl'"
                    )


if __name__ == "__main__":
    REGIONS = {
        "ARAB_REGION": ARAB_REGION,
        "WORLDWIDE": WORLDWIDE,
        "EASTERN_ASIA": EASTERN_ASIA,
        "WESTERN_EUROPEAN": WESTERN_EUROPEAN,
        "SOUTH_WESTERN_EUROPE": SOUTH_WESTERN_EUROPE,
        "NORTH_AMERICA_AND_AUSTRALIA": NORTH_AMERICA_AND_AUSTRALIA,
    }

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--region",
        choices=[
            "ARAB_REGION",
            "WORLDWIDE",
            "EASTERN_ASIA",
            "WESTERN_EUROPEAN",
            "SOUTH_WESTERN_EUROPE",
            "NORTH_AMERICA_AND_AUSTRALIA",
        ],
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
    args = parser.parse_args()

    main(
        REGION=REGIONS[args.region],
        SAMPLE_SIZE=args.n,
        REGION_NAME=args.region,
        RELATIONS_SUBSET=args.rel,
    )
