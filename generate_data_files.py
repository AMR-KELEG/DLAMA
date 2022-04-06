from constants import *
from filters import *
import utils
import data_generation_utils
from query import Query
import pandas as pd
from pathlib import Path

pd.set_option("display.max_rows", 2000)
pd.set_option("display.max_colwidth", 2000)

REGION = ARAB_REGION
SAMPLE_SIZE = 100


if __name__ == "__main__":
    q17 = Query(
        "P17",
        subject_field=CLUB,
        object_field=COUNTRY,
        wikipedia_langs=REGIONS_LANGS[REGION],
    )
    q17.add_filter("region_country", REGION)
    q17.add_filter("sports", "football")

    queries = [q17]
    for q in queries:
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
            .loc[:, ["size", CLUB, COUNTRY, "subject_article_ar", "subject_article_en"]]
            .head(SAMPLE_SIZE)
        )

        # TODO: Augment with page views as well?

        # Export the triples to jsonl files
        for lang in LANGS:
            filename = Path("data", f"{q.relation_id}_{REGION}_{lang}.json")
            data_generation_utils.generate_facts_jsonl(sample_df, q, lang, filename)
