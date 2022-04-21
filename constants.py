# Fields
PERSON = "person"
COUNTRY = "country"
CLUB = "club"
OCCUPATION = "occupation"
LANGUAGE = "language"
CITY = "city"
CONTINENT = "continent"
PIECE_OF_WORK = "piece_of_work"
INSTRUMENT = "instrument"

# Domains
POLITICS = "politics"
SPORTS = "sports"
CINEMA_AND_THEATRE = "cinema_and_theatre"
MUSIC = "music"
GEOGRAPHY = "geography"

# Regions
ANDORRA = "Andorra"
AUSTRALIA = "Australia"
AUSTRIA = "Austria"
BELGIUM = "Belgium"
CANADA = "Canada"
CHINA = "China"
FRANCE = "France"
GERMANY = "Germany"
IRELAND = "Ireland"
ITALY = "Italy"
JAPAN = "Japan"
LIECHTENSTEIN = "Liechtenstein"
LUXEMBOURG = "Luxembourg"
MONACO = "Monaco"
NETHERLANDS = "Netherlands"
NEW_ZEALAND = "New Zealand"
NORTH_KOREA = "North Korea"
PORTUGAL = "Portugal"
SAN_MARINO = "San Marino"
SOUTH_KOREA = "South Korea"
SPAIN = "Spain"
SWITZERLAND = "Switzerland"
UK = "UK"
USA = "USA"

ARAB_REGION = "Arab"
EASTERN_ASIA = [CHINA, JAPAN, NORTH_KOREA, SOUTH_KOREA]
NORTH_AMERICA_AND_AUSTRALIA = [AUSTRALIA, CANADA, NEW_ZEALAND, USA]
SOUTH_WESTERN_EUROPE = [
    ITALY,
    SPAIN,
    PORTUGAL,
    ANDORRA,
    LIECHTENSTEIN,
    SAN_MARINO,
    MONACO,
]
WESTERN_EUROPEAN = [
    AUSTRIA,
    BELGIUM,
    FRANCE,
    GERMANY,
    IRELAND,
    LUXEMBOURG,
    NETHERLANDS,
    SWITZERLAND,
    UK,
]
WORLDWIDE = "Worldwide"

#  LANGS for links of wikipedia
REGIONS_LANGS = {
    ANDORRA: ["ca", "en"],
    ARAB_REGION: ["ar", "en", "fr"],
    AUSTRALIA: ["en"],
    AUSTRIA: ["de", "en"],
    BELGIUM: ["de", "fr", "nl", "en"],
    CANADA: ["en", "fr"],
    CHINA: ["zh", "en"],  # "zh-yue", "zh-classical", "en"],
    FRANCE: ["fr", "en"],
    GERMANY: ["de", "en"],
    IRELAND: ["ga", "en"],
    ITALY: ["it", "en"],
    JAPAN: ["ja", "en"],
    LIECHTENSTEIN: ["de", "en"],
    LUXEMBOURG: ["lb", "fr", "de", "en"],
    MONACO: ["fr", "en"],
    NETHERLANDS: ["nl", "en"],
    NEW_ZEALAND: ["en", "mi"],
    NORTH_KOREA: ["ko", "en"],
    PORTUGAL: ["pt", "en"],
    SAN_MARINO: ["it", "en"],
    SOUTH_KOREA: ["ko", "en"],
    SPAIN: ["es", "en"],
    SWITZERLAND: ["de", "fr", "it", "rm", "en"],
    UK: ["en"],  # "cy", "sco", "gd", "ga"],
    USA: ["en"],
    WORLDWIDE: ["en"],
}

# LANGS for labels of fields
LANGS = ["ar", "en"]
