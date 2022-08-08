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
import time

logger = logging.getLogger(__name__)
ch = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    "%(levelname)s - %(filename)s:%(funcName)s:line %(lineno)d - %(message)s"
)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.DEBUG)

NO_RETRIES = 5


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

        # Native language
        q103 = query_factory.create_query(
            "P103",
            subject_field=PERSON,
            object_field=LANGUAGE,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        q103.add_filter(OCCUPATION, domain)
        q103.add_filter(PERSON, "country_of_citizenship")
        q103.add_filter(PERSON, OCCUPATION)
        q103.add_filter("region_country", REGION)
        queries.append(q103)

        # Languages spoken or published
        q1412 = query_factory.create_query(
            "P1412",
            subject_field=PERSON,
            object_field=LANGUAGE,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        q1412.add_filter(OCCUPATION, domain)
        q1412.add_filter(PERSON, "country_of_citizenship")
        q1412.add_filter(PERSON, OCCUPATION)
        q1412.add_filter("region_country", REGION)
        queries.append(q1412)

        # Place of birth
        q19 = query_factory.create_query(
            "P19",
            subject_field=PERSON,
            object_field=CITY,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        q19.add_filter(OCCUPATION, domain)
        q19.add_filter(PERSON, OCCUPATION)
        q19.add_filter(GEOGRAPHY, "lies_in_country")
        q19.add_filter(GEOGRAPHY, "city_not_historical_state")
        q19.add_filter(GEOGRAPHY, "city_not_sovereign_state")
        q19.add_filter(GEOGRAPHY, "city_not_country_within_the_UK")
        q19.add_filter("region_country", REGION)
        queries.append(q19)

        # Place of death
        q20 = query_factory.create_query(
            "P20",
            subject_field=PERSON,
            object_field=CITY,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        q20.add_filter(OCCUPATION, domain)
        q20.add_filter(PERSON, OCCUPATION)
        q20.add_filter(GEOGRAPHY, "lies_in_country")
        q20.add_filter(GEOGRAPHY, "city_not_historical_state")
        q20.add_filter(GEOGRAPHY, "city_not_sovereign_state")
        q20.add_filter(GEOGRAPHY, "city_not_country_within_the_UK")
        q20.add_filter("region_country", REGION)
        queries.append(q20)

    ### Entertainment ###
    for domain in [MUSIC, CINEMA_AND_THEATRE]:
        # Country of origin
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

        # Language of work or name
        p407 = query_factory.create_query(
            "P407",
            subject_field=PIECE_OF_WORK,
            object_field=LANGUAGE,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        p407.add_filter(PIECE_OF_WORK, domain)
        p407.add_filter(PIECE_OF_WORK, "country_of_origin")
        p407.add_filter("region_country", REGION)
        queries.append(p407)

    # Instrument
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

    # Genre
    q136 = query_factory.create_query(
        "P136",
        subject_field=PERSON,
        object_field=GENRE,
        domain=MUSIC,
        region=REGION,
        region_name=REGION_NAME,
    )
    q136.add_filter(PERSON, "country_of_citizenship")
    q136.add_filter(PERSON, OCCUPATION)
    q136.add_filter(OCCUPATION, MUSIC)
    q136.add_filter("region_country", REGION)
    queries.append(q136)

    # Record Label
    q264 = query_factory.create_query(
        "P264",
        subject_field=PERSON,
        object_field=RECORD_LABEL,
        domain=MUSIC,
        region=REGION,
        region_name=REGION_NAME,
    )
    q264.add_filter(PERSON, "country_of_citizenship")
    q264.add_filter("region_country", REGION)
    queries.append(q264)

    # Official language of film or tv show
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

    # Original Network
    p449 = query_factory.create_query(
        "P449",
        subject_field=PIECE_OF_WORK,
        object_field=ORIGINAL_NETWORK,
        domain=domain,
        region=REGION,
        region_name=REGION_NAME,
    )
    p449.add_filter(PIECE_OF_WORK, domain)
    p449.add_filter(PIECE_OF_WORK, "country_of_origin")
    p449.add_filter("region_country", REGION)
    queries.append(p449)

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

    for region, region_name in zip([REGION], [REGION_NAME]):
        ### GEOGRAPHY ###
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

        # Shares borders with
        q47 = query_factory.create_query(
            "P47",
            subject_field=COUNTRY,
            object_field=COUNTRY1,
            domain=GEOGRAPHY,
            region=region,
            region_name=region_name,
        )
        if region != WORLDWIDE:
            q47.add_filter("region_country", region)
        q47.add_filter(GEOGRAPHY, "sovereign_state")
        q47.add_filter(GEOGRAPHY, "sovereign_state1")
        queries.append(q47)

        # Country (landforms)
        q17 = query_factory.create_query(
            "P17",
            subject_field=PLACE,
            object_field=COUNTRY,
            domain=GEOGRAPHY,
            region=region,
            region_name=region_name,
        )
        if region != WORLDWIDE:
            q17.add_filter("region_country", region)
        q17.add_filter(GEOGRAPHY, "sovereign_state")
        q17.add_filter(GEOGRAPHY, "a_landform")
        q17.add_filter(GEOGRAPHY, "not_an_archaeological_site")
        queries.append(q17)

        ### HISTORY ###
        # Country (touristic sites)
        q17 = query_factory.create_query(
            "P17",
            subject_field=PLACE,
            object_field=COUNTRY,
            domain=HISTORY,
            region=region,
            region_name=region_name,
        )
        if region != WORLDWIDE:
            q17.add_filter("region_country", region)
        q17.add_filter(GEOGRAPHY, "sovereign_state")
        q17.add_filter(HISTORY, "a_touristic_place")
        queries.append(q17)

        ### POLITICS ###
        # Official language
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

        # Diplomatic relations
        q530 = query_factory.create_query(
            "P530",
            subject_field=COUNTRY,
            object_field=COUNTRY1,
            domain=POLITICS,
            region=region,
            region_name=region_name,
        )
        if region != WORLDWIDE:
            q530.add_filter("region_country", region)
        q530.add_filter(GEOGRAPHY, "sovereign_state")
        q530.add_filter(GEOGRAPHY, "sovereign_state1")
        queries.append(q530)

        # Sister city
        q190 = query_factory.create_query(
            "P190",
            subject_field=CITY,
            object_field=CITY1,
            domain=POLITICS,
            region=region,
            region_name=region_name,
        )
        if region != WORLDWIDE:
            q190.add_filter("region_country", region)
        q190.add_filter(GEOGRAPHY, "lies_in_country")
        q190.add_filter(GEOGRAPHY, "big_city")
        q190.add_filter(GEOGRAPHY, "big_city1")
        queries.append(q190)

    ### SCIENCE ###
    # Has part (for chemical compounds)
    q527 = query_factory.create_query(
        "P527",
        subject_field=CHEMICAL_COMPOUND,
        object_field=CHEMICAL_ELEMENT,
        domain=SCIENCE,
        region=WORLDWIDE,
        region_name=WORLDWIDE,
    )
    q527.add_filter(SCIENCE, "is_a_chemical_compound")
    queries.append(q527)

    for q in queries:
        if RELATIONS_SUBSET and q.relation_id not in RELATIONS_SUBSET:
            continue
        logger.info(
            f"Querying data for '{q.relation_id}_{q.domain}_{q.region_name}.jsonl'"
        )
        start_time = time.time()
        data = q.get_data(find_count=False, no_retries=NO_RETRIES)

        # Form a dataframe to make it easier to add columns
        df = pd.DataFrame(data)

        # Sort the triples using the articles' sizes
        df.sort_values(by="size", ascending=False, inplace=True)

        logger.info(f"Total number of subjects: {len(df[q.subject_field].unique())}")

        df.drop_duplicates(subset=[q.subject_field], inplace=True)
        df.reset_index(drop=True, inplace=True)

        # Start finding all the valid objects and the labels progressively
        BATCH_SIZE = 50
        complete_samples_df = None
        all_subjects_labels = {}
        all_objects_labels = {}
        for i in range(0, df.shape[0], BATCH_SIZE):
            batch_df = df.iloc[i : i + BATCH_SIZE]
            logger.info(
                f"Total number of subjects within the batch for getting labels: {len(batch_df[q.subject_field])}"
            )

            sample_df = batch_df.loc[
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

            # Query the Wikidata labels
            subjects_ids = samples_df[samples_query.subject_field].tolist()
            objects_ids = samples_df[samples_query.object_field].tolist()
            subjects_labels = utils.get_wikidata_labels(subjects_ids)
            objects_labels = utils.get_wikidata_labels(objects_ids)

            # Add the labels to their respective dictionaries
            all_subjects_labels = dict(
                list(all_subjects_labels.items()) + list(subjects_labels.items())
            )
            all_objects_labels = dict(
                list(all_objects_labels.items()) + list(objects_labels.items())
            )

            # Drop the rows having missing labels
            samples_df["sub_label_missing"] = samples_df[
                samples_query.subject_field
            ].apply(
                lambda uri: any([subjects_labels[uri][lang] == None for lang in LANGS])
            )
            samples_df["obj_label_missing"] = samples_df[
                samples_query.object_field
            ].apply(
                lambda uri: any([objects_labels[uri][lang] == None for lang in LANGS])
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

            if len(set(complete_samples_df[q.subject_field].tolist())) > SAMPLE_SIZE:
                # Find the number of rows to have SAMPLE_SIZE unique subjects
                size_lower, size_upper = 1, complete_samples_df.shape[0]
                while size_lower < size_upper:
                    size_mid = (size_lower + size_upper) // 2 + (
                        size_lower + size_upper
                    ) % 2
                    n_subjects_till_mid = len(
                        set(
                            complete_samples_df.head(size_mid)[q.subject_field].tolist()
                        )
                    )
                    if n_subjects_till_mid > SAMPLE_SIZE:
                        size_upper = size_mid - 1
                    else:
                        size_lower = size_mid

                n_subjects = (size_lower + size_upper) // 2 + (
                    size_lower + size_upper
                ) % 2
                complete_samples_df = complete_samples_df.head(n=n_subjects)
                break

        logger.info(
            f"Final number of subjects: {len(complete_samples_df[q.subject_field].unique())}"
        )

        # Make the objects a list instead of a single value
        complete_samples_df[samples_query.object_field] = complete_samples_df[
            samples_query.object_field
        ].apply(lambda o: [o])

        # Export the triples to jsonl files
        for lang in LANGS:
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
            ].apply(
                lambda uris_list: [all_objects_labels[uri][lang] for uri in uris_list]
            )
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
    args = parser.parse_args()

    main(
        REGION=REGIONS[args.region],
        SAMPLE_SIZE=args.n,
        REGION_NAME=args.region,
        RELATIONS_SUBSET=args.rel,
    )
