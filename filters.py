from constants import *

FILTERS_DICTIONARY = {
    # Subject should be a person
    OCCUPATION: {
        POLITICS: f"{{?{OCCUPATION} wdt:P31 wd:Q303618}} # The occupation is instance of diplomatic rank\n"
        "UNION\n"
        f"{{?{PERSON} wdt:P106 wd:Q82955}} . # The occupation is politician",
        MUSIC: f"?{OCCUPATION} wdt:P31+ wd:Q66715801 . # The occupation is instance of musical profession",
        SPORTS: f"?{OCCUPATION} wdt:P279+ wd:Q2066131 . # The occupation is subclass of athlete",
        CINEMA_AND_THEATRE: f"{{?{OCCUPATION} wdt:P279+ wd:Q713200}} . # The occupation is a subclass of performing artist\n"
        "MINUS\n"
        f"{{?{OCCUPATION} wdt:P31+ wd:Q66715801}} . # The occupation is instance of musical profession",
    },
    "sports": {"football": f"?{CLUB} wdt:P31 wd:Q476028 . # Club is a football club"},
    "region_country": {
        ANDORRA: f"VALUES ?{COUNTRY} {{wd:Q228}} . # Country is Andorra",
        ARAB_REGION: f"?{COUNTRY} wdt:P463 wd:Q7172 . # Make sure the country belongs to the Arab league",
        AUSTRALIA: f"VALUES ?{COUNTRY} {{wd:Q408}} . # Country is Australia",
        AUSTRIA: f"VALUES ?{COUNTRY} {{wd:Q40}} . # Country is Austria",
        BELGIUM: f"VALUES ?{COUNTRY} {{wd:Q31}} . # Country is Belgium",
        CANADA: f"VALUES ?{COUNTRY} {{wd:Q16}} . # Country is Canada",
        CHINA: f"VALUES ?{COUNTRY} {{wd:Q148}} . # Country is China",
        FRANCE: f"VALUES ?{COUNTRY} {{wd:Q142}} . # Country is France",
        GERMANY: f"VALUES ?{COUNTRY} {{wd:Q183}} . # Country is Germany",
        IRELAND: f"VALUES ?{COUNTRY} {{wd:Q27}} . # Country is Ireland",
        ITALY: f"VALUES ?{COUNTRY} {{wd:Q38}} . # Country is Italy",
        JAPAN: f"VALUES ?{COUNTRY} {{wd:Q17}} . # Country is Japan",
        LIECHTENSTEIN: f"VALUES ?{COUNTRY} {{wd:Q347}} . # Country is Liechtenstein",
        LUXEMBOURG: f"VALUES ?{COUNTRY} {{wd:Q32}} . # Country is Luxembourg",
        MONACO: f"VALUES ?{COUNTRY} {{wd:Q235}} . # Country is Monaco",
        NETHERLANDS: f"VALUES ?{COUNTRY} {{wd:Q55}} . # Country is Netherlands",
        NEW_ZEALAND: f"VALUES ?{COUNTRY} {{wd:Q664}} . # Country is New Zealand",
        NORTH_KOREA: f"VALUES ?{COUNTRY} {{wd:Q423}} . # Country is North Korea",
        PORTUGAL: f"VALUES ?{COUNTRY} {{wd:Q45}} . # Country is Portugal",
        SAN_MARINO: f"VALUES ?{COUNTRY} {{wd:Q238}} . # Country is San Marino",
        SOUTH_KOREA: f"VALUES ?{COUNTRY} {{wd:Q884}} . # Country is South Korea",
        SPAIN: f"VALUES ?{COUNTRY} {{wd:Q29}} . # Country is Spain",
        SWITZERLAND: f"VALUES ?{COUNTRY} {{wd:Q39}} . # Country is Switzerland",
        UK: f"VALUES ?{COUNTRY} {{wd:Q145}} . # Country is UK",
        USA: f"VALUES ?{COUNTRY} {{wd:Q30}} . # Country is USA",
    },
    PERSON: {
        "country_of_citizenship": f"?{PERSON} wdt:P27 ?{COUNTRY} . # The person has a country of citizenship",
        OCCUPATION: f"?{PERSON} wdt:P106 ?{OCCUPATION} . # The person has an occupation",
    },
    PIECE_OF_WORK: {
        MUSIC: f"?{PIECE_OF_WORK} wdt:P31/wdt:P279* wd:Q2188189 . # The piece of work is instance of something that is a subclass of musical work",
        CINEMA_AND_THEATRE: f"{{?{PIECE_OF_WORK} wdt:P31/wdt:P279* wd:Q2431196 }} . # The piece of work is instance of something that is a subclass of audiovisual work\n"
        "MINUS\n"
        f"{{?{PIECE_OF_WORK} wdt:P31/wdt:P279* wd:Q2188189 }}. # The piece of work is instance of something that is a subclass of musical work\n",
        "country_of_origin": f"?{PIECE_OF_WORK} wdt:P495 ?{COUNTRY} . # The piece of work has a country of origin",
    },
    MUSIC: {
        "not_voice": f"MINUS {{VALUES ?{INSTRUMENT} {{wd:Q17172850}} }} . # Remove instrument 'voice'"
    },
    LANGUAGE: {
        "not_sign_language": f"MINUS {{ ?{LANGUAGE} wdt:P31 wd:Q34228 }} . # Remove sign languages"
    },
    GEOGRAPHY: {
        "not_lost_city": f"MINUS {{?{CITY} wdt:P31 wd:Q2974842}} . # A lost city",
        "not_historical_country": f"MINUS {{?{COUNTRY} wdt:P31 wd:Q3024240}} . # Discard historical countries",
        "sovereign_state": f"?{COUNTRY} wdt:P31 wd:Q3624078 . # The country is a sovereign country",
        "US_state": f"?{COUNTRY} wdt:P31 wd:Q35657 . # The country is a US state",
    },
}
