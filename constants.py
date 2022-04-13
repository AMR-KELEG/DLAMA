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
ARAB_REGION = "Arab"
WORLDWIDE = "Worldwide"
BELGIUM = "Belgium"
CHINA = "China"
JAPAN = "Japan"
NORTH_KOREA = "North Korea"
SOUTH_KOREA = "South Korea"
USA = "USA"
CANADA = "Canada"
AUSTRALIA = "Australia"
NEW_ZEALAND = "New Zealand"
GERMANY = "Germany"
FRANCE = "France"
ITALY = "Italy"
UK = "UK"
SPAIN = "Spain"
PORTUGAL = "Portugal"
LUXEMBOURG = "Luxembourg"
NETHERLANDS = "Netherlands"
AUSTRIA = "Austria"
IRELAND = "Ireland"
SWITZERLAND = "Switzerland"

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

SOUTH_WESTERN_EUROPE = [ITALY, SPAIN, PORTUGAL]
NORTH_AMERICA_AND_AUSTRALIA = [AUSTRALIA, CANADA, NEW_ZEALAND, USA]
EASTERN_ASIA = [CHINA, JAPAN, NORTH_KOREA, SOUTH_KOREA]

#  LANGS for links of wikipedia
REGIONS_LANGS = {
    WORLDWIDE: ["en"],
    ARAB_REGION: ["ar", "en", "fr"],
    AUSTRIA: ["de", "en"],
    BELGIUM: ["de", "fr", "nl", "en"],
    FRANCE: ["fr", "en"],
    GERMANY: ["de", "en"],
    IRELAND: ["ga", "en"],
    LUXEMBOURG: ["lb", "fr", "de", "en"],
    NETHERLANDS: ["nl", "en"],
    SWITZERLAND: ["de", "fr", "it", "rm", "en"],
    UK: ["en", "cy", "sco", "gd"],  # , "ga"],
    CHINA: ["zh", "en"],  # "zh-yue", "zh-classical", "en"],
    JAPAN: ["ja", "en"],
    SOUTH_KOREA: ["ko", "en"],
    NORTH_KOREA: ["ko", "en"],
    USA: ["en"],
    CANADA: ["en", "fr"],
    AUSTRALIA: ["en"],
    NEW_ZEALAND: ["en", "mi"],
    ITALY: ["it", "en"],
    SPAIN: ["es", "ca", "eu", "en"],
    PORTUGAL: ["pt", "en"],
}

# LANGS for labels of fields
LANGS = ["ar", "en"]
