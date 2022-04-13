from constants import *
from filters import *
import utils
import data_generation_utils
from query import QueryFactory
import pandas as pd
from pathlib import Path
import os

pd.set_option("display.max_rows", 2000)
pd.set_option("display.max_colwidth", 2000)

REGION = ARAB_REGION
SAMPLE_SIZE = 100


if __name__ == "__main__":
    # Create output data files
    BASE_DATA_DIR = str(Path("data", "cultlama"))
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
    )
    q364.add_filter(PIECE_OF_WORK, "country_of_origin")
    q364.add_filter("region_country", REGION)
    queries.append(q364)

    ### SPORTS ###
    # Country of sports clubs
    q17 = query_factory.create_query(
        "P17", subject_field=CLUB, object_field=COUNTRY, domain=SPORTS, region=REGION,
    )
    q17.add_filter("region_country", REGION)
    q17.add_filter(SPORTS, "football")
    queries.append(q17)

    ### GEOGRAPHY ###
    for region in [REGION, WORLDWIDE]:
        # Capital
        q36 = query_factory.create_query(
            "P36",
            subject_field=COUNTRY,
            object_field=CITY,
            domain=GEOGRAPHY,
            region=region,
        )
        if region != WORLDWIDE:
            q36.add_filter("region_country", region)
        q36.add_filter(GEOGRAPHY, "not_ancient")
        q36.add_filter(GEOGRAPHY, "sovereign_state")
        queries.append(q36)

        # Capital of
        q1376 = query_factory.create_query(
            "P1376",
            subject_field=CITY,
            object_field=COUNTRY,
            domain=GEOGRAPHY,
            region=region,
        )
        if region != WORLDWIDE:
            q1376.add_filter("region_country", region)
        q1376.add_filter(GEOGRAPHY, "not_ancient")
        q1376.add_filter(GEOGRAPHY, "sovereign_state")
        queries.append(q1376)

        #  Continent
        q30 = query_factory.create_query(
            "P30",
            subject_field=COUNTRY,
            object_field=CONTINENT,
            domain=GEOGRAPHY,
            region=region,
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
        )
        if region != WORLDWIDE:
            q37.add_filter("region_country", region)
        q37.add_filter(GEOGRAPHY, "sovereign_state")
        queries.append(q37)

    for q in queries:
        data = q.get_data(find_count=False)

        # Form a dataframe to make it easier to add columns
        df = pd.DataFrame(data)

        # TODO: Think of a better way to keep enough rows for sampling
        # Sort the triples using the articles' sizes
        # Keep the top 10*SAMPLE_SIZE rows for sampling
        sample_df = (
            df.sort_values(by="size", ascending=False)
            .loc[:, ["size", q.subject_field, q.object_field,],]
            .head(n=10 * SAMPLE_SIZE)
        )
        sample_df.reset_index(drop=True, inplace=True)

        # TODO: Augment with page views as well?

        # TODO: Do this progressively
        # Query the Wikidata labels
        subjects_ids = sample_df[q.subject_field].tolist()
        objects_ids = sample_df[q.object_field].tolist()
        subjects_labels = utils.get_wikidata_labels(subjects_ids)
        objects_labels = utils.get_wikidata_labels(objects_ids)

        # Drop the rows having missing labels
        sample_df["sub_label_missing"] = sample_df[q.subject_field].apply(
            lambda uri: any([subjects_labels[uri][lang] == None for lang in LANGS])
        )
        sample_df["obj_label_missing"] = sample_df[q.object_field].apply(
            lambda uri: any([objects_labels[uri][lang] == None for lang in LANGS])
        )
        sample_df = sample_df.loc[
            ~(sample_df["sub_label_missing"] | sample_df["obj_label_missing"]), :
        ]

        if len(set(sample_df[q.subject_field].tolist())) > SAMPLE_SIZE:
            # Find the number of rows to have SAMPLE_SIZE unique subjects
            size_lower, size_upper = 1, sample_df.shape[0]
            while size_lower < size_upper:
                size_mid = (size_lower + size_upper) // 2
                n_subjects_till_mid = len(
                    set(sample_df.head(size_mid)[q.subject_field].tolist())
                )
                if n_subjects_till_mid < SAMPLE_SIZE:
                    size_lower = size_mid + 1
                else:
                    size_upper = size_mid
            sample_df = sample_df.head(n=(size_lower + size_upper) // 2)

        # Export the triples to jsonl files
        for lang in LANGS:
            filename = Path(
                BASE_DATA_DIR, lang, f"{q.relation_id}_{q.domain}_{q.region}.jsonl"
            )
            sample_df["sub_label"] = sample_df[q.subject_field].apply(
                lambda uri: subjects_labels[uri][lang]
            )
            sample_df["obj_label"] = sample_df[q.object_field].apply(
                lambda uri: objects_labels[uri][lang]
            )
            data_generation_utils.generate_facts_jsonl(sample_df, q, lang, filename)
