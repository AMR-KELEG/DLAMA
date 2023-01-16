from constants import *
from filters import *
from query import QueryFactory


def populate_queries(REGION, REGION_NAME, sorting_function):
    """Form the queries with their respective filters.

    Args:
        REGION: A single country/ group of countries or a list of countries.
        REGION_NAME: A string to be used for naming the results files of the queries after execution.

    Returns:
        A list of SPAQRL query objects.
    """
    ### ALL DOMAINS ###
    CultLAMA_queries = []
    query_factory = QueryFactory()

    # TODO: Reconsider whether having a domain for each query is useful.
    DOMAIN = "general"

    # Country of citizenship
    q27 = query_factory.create_query(
        "P27",
        subject_field=PERSON,
        object_field=COUNTRY,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    q27.add_filter("region_country", REGION)
    CultLAMA_queries.append(q27)

    # Occupation
    q106 = query_factory.create_query(
        "P106",
        subject_field=PERSON,
        object_field=OCCUPATION,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    q106.add_filter(PERSON, "country_of_citizenship")
    q106.add_filter("region_country", REGION)
    CultLAMA_queries.append(q106)

    # Native language
    q103 = query_factory.create_query(
        "P103",
        subject_field=PERSON,
        object_field=LANGUAGE,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    q103.add_filter(PERSON, "country_of_citizenship")
    q103.add_filter("region_country", REGION)
    CultLAMA_queries.append(q103)

    # Languages spoken or published
    q1412 = query_factory.create_query(
        "P1412",
        subject_field=PERSON,
        object_field=LANGUAGE,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    q1412.add_filter(PERSON, "country_of_citizenship")
    q1412.add_filter("region_country", REGION)
    CultLAMA_queries.append(q1412)

    # Place of birth
    q19 = query_factory.create_query(
        "P19",
        subject_field=PERSON,
        object_field=CITY,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    q19.add_filter(GEOGRAPHY, "city_lies_in_country")
    q19.add_filter(GEOGRAPHY, "city_not_sovereign_state")
    q19.add_filter(GEOGRAPHY, "city_not_country_within_the_UK")
    q19.add_filter("region_country", REGION)
    CultLAMA_queries.append(q19)

    # Place of death
    q20 = query_factory.create_query(
        "P20",
        subject_field=PERSON,
        object_field=CITY,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    q20.add_filter(GEOGRAPHY, "city_lies_in_country")
    q20.add_filter(GEOGRAPHY, "city_not_sovereign_state")
    q20.add_filter(GEOGRAPHY, "city_not_country_within_the_UK")
    q20.add_filter("region_country", REGION)
    CultLAMA_queries.append(q20)

    # Country of a place
    q17 = query_factory.create_query(
        "P17",
        subject_field=PLACE,
        object_field=COUNTRY,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    q17.add_filter("region_country", REGION)
    CultLAMA_queries.append(q17)

    ### Entertainment ###
    # Country of origin
    p495 = query_factory.create_query(
        "P495",
        subject_field=PIECE_OF_WORK,
        object_field=COUNTRY,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    p495.add_filter("region_country", REGION)
    CultLAMA_queries.append(p495)

    # Language of work or name
    p407 = query_factory.create_query(
        "P407",
        subject_field=PIECE_OF_WORK,
        object_field=LANGUAGE,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    p407.add_filter(PIECE_OF_WORK, "country_of_origin")
    p407.add_filter("region_country", REGION)
    CultLAMA_queries.append(p407)

    # Instrument
    q1303 = query_factory.create_query(
        "P1303",
        subject_field=PERSON,
        object_field=INSTRUMENT,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    q1303.add_filter(PERSON, "country_of_citizenship")
    q1303.add_filter("region_country", REGION)
    CultLAMA_queries.append(q1303)

    # Genre
    q136 = query_factory.create_query(
        "P136",
        subject_field=PERSON,
        object_field=GENRE,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    q136.add_filter(PERSON, "country_of_citizenship")
    q136.add_filter("region_country", REGION)
    CultLAMA_queries.append(q136)

    # Record Label
    q264 = query_factory.create_query(
        "P264",
        subject_field=PERSON,
        object_field=RECORD_LABEL,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    q264.add_filter(PERSON, "country_of_citizenship")
    q264.add_filter("region_country", REGION)
    CultLAMA_queries.append(q264)

    # Official language of film or tv show
    q364 = query_factory.create_query(
        "P364",
        subject_field=PIECE_OF_WORK,
        object_field=LANGUAGE,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    q364.add_filter(PIECE_OF_WORK, "country_of_origin")
    q364.add_filter("region_country", REGION)
    CultLAMA_queries.append(q364)

    # Original Network
    p449 = query_factory.create_query(
        "P449",
        subject_field=PIECE_OF_WORK,
        object_field=ORIGINAL_NETWORK,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    p449.add_filter(PIECE_OF_WORK, "country_of_origin")
    p449.add_filter("region_country", REGION)
    CultLAMA_queries.append(p449)

    ### GEOGRAPHY ###
    # Capital
    q36 = query_factory.create_query(
        "P36",
        subject_field=COUNTRY,
        object_field=CITY,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    if REGION != WORLDWIDE:
        q36.add_filter("region_country", REGION)
    q36.add_filter(GEOGRAPHY, "sovereign_state")
    CultLAMA_queries.append(q36)

    # Capital of
    q1376 = query_factory.create_query(
        "P1376",
        subject_field=CITY,
        object_field=COUNTRY,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    if REGION != WORLDWIDE:
        q1376.add_filter("region_country", REGION)
    q1376.add_filter(GEOGRAPHY, "sovereign_state")
    CultLAMA_queries.append(q1376)

    #  Continent
    q30 = query_factory.create_query(
        "P30",
        subject_field=COUNTRY,
        object_field=CONTINENT,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    if REGION != WORLDWIDE:
        q30.add_filter("region_country", REGION)
    q30.add_filter(GEOGRAPHY, "sovereign_state")
    CultLAMA_queries.append(q30)

    # Shares borders with
    q47 = query_factory.create_query(
        "P47",
        subject_field=COUNTRY,
        object_field=COUNTRY1,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    if REGION != WORLDWIDE:
        q47.add_filter("region_country", REGION)
    q47.add_filter(GEOGRAPHY, "sovereign_state")
    q47.add_filter(GEOGRAPHY, "sovereign_state1")
    CultLAMA_queries.append(q47)

    ### POLITICS ###
    # Official language
    q37 = query_factory.create_query(
        "P37",
        subject_field=COUNTRY,
        object_field=LANGUAGE,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    if REGION != WORLDWIDE:
        q37.add_filter("region_country", REGION)
    q37.add_filter(GEOGRAPHY, "sovereign_state")
    CultLAMA_queries.append(q37)

    # Diplomatic relations
    q530 = query_factory.create_query(
        "P530",
        subject_field=COUNTRY,
        object_field=COUNTRY1,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    if REGION != WORLDWIDE:
        q530.add_filter("region_country", REGION)
    q530.add_filter(GEOGRAPHY, "sovereign_state")
    q530.add_filter(GEOGRAPHY, "sovereign_state1")
    CultLAMA_queries.append(q530)

    # Sister city
    q190 = query_factory.create_query(
        "P190",
        subject_field=CITY,
        object_field=CITY1,
        domain=DOMAIN,
        region=REGION,
        region_name=REGION_NAME,
        sorting_function=sorting_function,
    )
    if REGION != WORLDWIDE:
        q190.add_filter("region_country", REGION)
    q190.add_filter(GEOGRAPHY, "city_lies_in_country")
    q190.add_filter(GEOGRAPHY, "big_city")
    q190.add_filter(GEOGRAPHY, "big_city1")
    CultLAMA_queries.append(q190)

    ### SCIENCE ###
    # Has part (for chemical compounds)
    q527 = query_factory.create_query(
        "P527",
        subject_field=CHEMICAL_COMPOUND,
        object_field=CHEMICAL_ELEMENT,
        domain=DOMAIN,
        region=WORLDWIDE,
        region_name=WORLDWIDE,
        sorting_function=sorting_function,
    )
    q527.add_filter(SCIENCE, "is_a_chemical_compound")
    CultLAMA_queries.append(q527)

    return CultLAMA_queries
