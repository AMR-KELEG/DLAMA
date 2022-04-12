from constants import *
from filters import *
import utils
import data_generation_utils
from query import Query
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
    for domain in [CINEMA_AND_THEATRE, POLITICS, SPORTS, MUSIC]:
        # Country of citizenship
        q27 = Query(
            "P27",
            subject_field=PERSON,
            object_field=COUNTRY,
            domain=domain,
            region=REGION,
            wikipedia_langs=REGIONS_LANGS[REGION],
        )
        q27.add_filter(PERSON, OCCUPATION)
        q27.add_filter(OCCUPATION, domain)
        q27.add_filter("region_country", REGION)
        queries.append(q27)

        # Occupation
        q106 = Query(
            "P106",
            subject_field=PERSON,
            object_field=OCCUPATION,
            domain=domain,
            region=REGION,
            wikipedia_langs=REGIONS_LANGS[REGION],
        )
        q106.add_filter(OCCUPATION, domain)
        q106.add_filter(PERSON, "country_of_citizenship")
        q106.add_filter("region_country", REGION)
        queries.append(q106)

    ### Entertainment ###
    q1303 = Query(
        "P1303",
        subject_field=PERSON,
        object_field=INSTRUMENT,
        domain=MUSIC,
        region=REGION,
        wikipedia_langs=REGIONS_LANGS[REGION],
    )
    q1303.add_filter(PERSON, "country_of_citizenship")
    q1303.add_filter("region_country", REGION)
    q1303.add_filter(MUSIC, "not_voice")
    queries.append(q1303)

    q364 = Query(
        "P364",
        subject_field=PIECE_OF_WORK,
        object_field=LANGUAGE,
        domain=CINEMA_AND_THEATRE,
        region=REGION,
        wikipedia_langs=REGIONS_LANGS[REGION],
    )
    q364.add_filter(PIECE_OF_WORK, "country_of_origin")
    q364.add_filter("region_country", REGION)
    queries.append(q364)

    ### SPORTS ###
    # Country of sports clubs
    q17 = Query(
        "P17",
        subject_field=CLUB,
        object_field=COUNTRY,
        domain=SPORTS,
        region=REGION,
        wikipedia_langs=REGIONS_LANGS[REGION],
    )
    q17.add_filter("region_country", REGION)
    q17.add_filter(SPORTS, "football")
    queries.append(q17)

    ### GEOGRAPHY ###
    for region in [REGION, WORLDWIDE]:
        # Capital
        q36 = Query(
            "P36",
            subject_field=COUNTRY,
            object_field=CITY,
            domain=GEOGRAPHY,
            region=region,
            wikipedia_langs=REGIONS_LANGS[region],
        )
        if region != WORLDWIDE:
            q36.add_filter("region_country", region)
        q36.add_filter(GEOGRAPHY, "not_ancient")
        q36.add_filter(GEOGRAPHY, "sovereign_state")
        queries.append(q36)

        # Capital of
        q1376 = Query(
            "P1376",
            subject_field=CITY,
            object_field=COUNTRY,
            domain=GEOGRAPHY,
            region=region,
            wikipedia_langs=REGIONS_LANGS[region],
        )
        if region != WORLDWIDE:
            q1376.add_filter("region_country", region)
        q1376.add_filter(GEOGRAPHY, "not_ancient")
        q1376.add_filter(GEOGRAPHY, "sovereign_state")
        queries.append(q1376)

        #  Continent
        q30 = Query(
            "P30",
            subject_field=COUNTRY,
            object_field=CONTINENT,
            domain=GEOGRAPHY,
            region=region,
            wikipedia_langs=REGIONS_LANGS[region],
        )
        if region != WORLDWIDE:
            q30.add_filter("region_country", region)
        q30.add_filter(GEOGRAPHY, "sovereign_state")
        queries.append(q30)

        # Official lamguage
        q37 = Query(
            "P37",
            subject_field=COUNTRY,
            object_field=LANGUAGE,
            domain=POLITICS,
            region=region,
            wikipedia_langs=REGIONS_LANGS[region],
        )
        if region != WORLDWIDE:
            q37.add_filter("region_country", region)
        q37.add_filter(GEOGRAPHY, "sovereign_state")
        queries.append(q37)

    for q in queries:
        print(q.build_query())
        data = q.parse_query(find_count=False)
        parsed_data = utils.parse_sparql_results(data)

        # Form a dataframe to make it easier to add columns
        df = pd.DataFrame(parsed_data)

        # Query the articles' sizes
        for lang in q.wikipedia_langs:
            # Find list of urls
            article_url_col = f"subject_article_{lang}"
            if article_url_col not in df.columns:
                continue
            urls = df[~df[article_url_col].isnull()][article_url_col].tolist()

            # Find the articles' sizes of the urls
            wikipedia_views_dict = utils.get_wikipedia_article_sizes(urls, lang=lang)
            # Add the size column to the dataframe
            df[f"size_article_{lang}"] = df[article_url_col].apply(
                lambda url: wikipedia_views_dict.get(url, 0)
            )

        df["size"] = df.apply(
            lambda row: max([row[col] for col in row.keys() if "size" in col]), axis=1
        )

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
        ].head(n=SAMPLE_SIZE)

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
