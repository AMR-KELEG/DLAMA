from constants import *
from filters import *
from query import QueryFactory


def populate_queries(REGION, REGION_NAME):
    ### ALL DOMAINS ###
    CultLAMA_queries = []
    query_factory = QueryFactory()

    # for domain in [CINEMA_AND_THEATRE, POLITICS, SPORTS, MUSIC]:
    for domain in ["general"]:
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
        q27.add_filter("region_country", REGION)
        CultLAMA_queries.append(q27)

        # Occupation
        q106 = query_factory.create_query(
            "P106",
            subject_field=PERSON,
            object_field=OCCUPATION,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        q106.add_filter(PERSON, "country_of_citizenship")
        q106.add_filter("region_country", REGION)
        CultLAMA_queries.append(q106)

        # Native language
        q103 = query_factory.create_query(
            "P103",
            subject_field=PERSON,
            object_field=LANGUAGE,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        q103.add_filter(PERSON, "country_of_citizenship")
        q103.add_filter(PERSON, OCCUPATION)
        q103.add_filter("region_country", REGION)
        CultLAMA_queries.append(q103)

        # Languages spoken or published
        q1412 = query_factory.create_query(
            "P1412",
            subject_field=PERSON,
            object_field=LANGUAGE,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        q1412.add_filter(PERSON, "country_of_citizenship")
        q1412.add_filter(PERSON, OCCUPATION)
        q1412.add_filter("region_country", REGION)
        CultLAMA_queries.append(q1412)

        # Place of birth
        q19 = query_factory.create_query(
            "P19",
            subject_field=PERSON,
            object_field=CITY,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        q19.add_filter(PERSON, OCCUPATION)
        q19.add_filter(GEOGRAPHY, "lies_in_country")
        q19.add_filter(GEOGRAPHY, "city_not_sovereign_state")
        q19.add_filter(GEOGRAPHY, "city_not_country_within_the_UK")
        q19.add_filter("region_country", REGION)
        CultLAMA_queries.append(q19)

        # Place of death
        q20 = query_factory.create_query(
            "P20",
            subject_field=PERSON,
            object_field=CITY,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        q20.add_filter(PERSON, OCCUPATION)
        q20.add_filter(GEOGRAPHY, "lies_in_country")
        q20.add_filter(GEOGRAPHY, "city_not_sovereign_state")
        q20.add_filter(GEOGRAPHY, "city_not_country_within_the_UK")
        q20.add_filter("region_country", REGION)
        CultLAMA_queries.append(q20)

        # Country of a place
        q17 = query_factory.create_query(
            "P17",
            subject_field=PLACE,
            object_field=COUNTRY,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        q17.add_filter("region_country", REGION)
        CultLAMA_queries.append(q17)

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
            CultLAMA_queries.append(p495)

            # Language of work or name
            p407 = query_factory.create_query(
                "P407",
                subject_field=PIECE_OF_WORK,
                object_field=LANGUAGE,
                domain=domain,
                region=REGION,
                region_name=REGION_NAME,
            )
            p407.add_filter(PIECE_OF_WORK, "country_of_origin")
            p407.add_filter("region_country", REGION)
            CultLAMA_queries.append(p407)

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
        CultLAMA_queries.append(q1303)

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
        q136.add_filter("region_country", REGION)
        CultLAMA_queries.append(q136)

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
        CultLAMA_queries.append(q264)

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
        CultLAMA_queries.append(q364)

        # Original Network
        p449 = query_factory.create_query(
            "P449",
            subject_field=PIECE_OF_WORK,
            object_field=ORIGINAL_NETWORK,
            domain=domain,
            region=REGION,
            region_name=REGION_NAME,
        )
        p449.add_filter(PIECE_OF_WORK, "country_of_origin")
        p449.add_filter("region_country", REGION)
        CultLAMA_queries.append(p449)

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
            q36.add_filter(GEOGRAPHY, "sovereign_state")
            CultLAMA_queries.append(q36)

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
            q1376.add_filter(GEOGRAPHY, "sovereign_state")
            CultLAMA_queries.append(q1376)

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
            CultLAMA_queries.append(q30)

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
            CultLAMA_queries.append(q47)

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
            CultLAMA_queries.append(q37)

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
            CultLAMA_queries.append(q530)

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
            CultLAMA_queries.append(q190)

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
        CultLAMA_queries.append(q527)

    return CultLAMA_queries
