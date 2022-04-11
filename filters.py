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
        ARAB_REGION: f"?{COUNTRY} wdt:P463 wd:Q7172 . # Make sure the country belongs to the Arab league",
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
    GEOGRAPHY: {
        "not_ancient": "MINUS # Discard the following\n"
        f"{{ {{?{CITY} wdt:P31 wd:Q15661340}} # an ancient city\n"
        "UNION\n"
        f"{{?{CITY} wdt:P31 wd:Q676050}} # an old town\n"
        "UNION\n"
        f"{{?{CITY} wdt:P31 wd:Q2974842}} }} . # a lost city",
        "sovereign_state": f"?{COUNTRY} wdt:P31 wd:Q3624078 . # The country is a sovereign country",
        "US_state": f"?{COUNTRY} wdt:P31 wd:Q35657 . # The country is a US state",
    },
}
