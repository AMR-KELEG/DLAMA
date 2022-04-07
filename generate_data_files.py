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
    for domain in ["cinema_and_theatre", "politics", "sports", "music"]:
        # Country of citizenship
        q27 = Query(
            "P27",
            subject_field=PERSON,
            object_field=COUNTRY,
            domain=domain,
            region=REGION,
            wikipedia_langs=REGIONS_LANGS[REGION],
        )
        q27.add_filter("person", "occupation")
        q27.add_filter("occupation", domain)
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
        q106.add_filter("occupation", domain)
        q106.add_filter("person", "country_of_citizenship")
        q106.add_filter("region_country", REGION)
        queries.append(q106)

    ### SPORTS ###
    # Country of sports clubs
    q17 = Query(
        "P17",
        subject_field=CLUB,
        object_field=COUNTRY,
        domain="sports",
        region=REGION,
        wikipedia_langs=REGIONS_LANGS[REGION],
    )
    q17.add_filter("region_country", REGION)
    q17.add_filter("sports", "football")
    queries.append(q17)


    for q in queries:
        print(q.build_query())
        data = q.parse_query(find_count=False)
        parsed_data = utils.parse_sparql_results(data)

        # Form a dataframe to make it easier to add columns
        df = pd.DataFrame(parsed_data)

        # Query the articles' sizes
        for lang in q.wikipedia_langs:
            # Find list of urls
            urls = df[~df[f"subject_article_{lang}"].isnull()][
                f"subject_article_{lang}"
            ].tolist()
            # Find the articles' sizes of the urls
            wikipedia_views_dict = utils.get_wikipedia_article_sizes(urls, lang=lang)
            # Add the size column to the dataframe
            df[f"size_article_{lang}"] = df[f"subject_article_{lang}"].apply(
                lambda url: wikipedia_views_dict.get(url, 0)
            )

        df["size"] = df.apply(
            lambda row: max([row[col] for col in row.keys() if "size" in col]), axis=1
        )

        # Sample triples using articles' sizes
        sample_df = (
            df.sort_values(by="size", ascending=False)
            .loc[
                :,
                [
                    "size",
                    q.subject_field,
                    q.object_field,
                    "subject_article_ar",
                    "subject_article_en",
                ],
            ]
            .head(SAMPLE_SIZE)
        )
        sample_df.reset_index(drop=True, inplace=True)

        # TODO: Augment with page views as well?

        # Export the triples to jsonl files
        for lang in LANGS:
            filename = Path(
                BASE_DATA_DIR, lang, f"{q.relation_id}_{q.domain}_{q.region}.jsonl"
            )
            data_generation_utils.generate_facts_jsonl(sample_df, q, lang, filename)
