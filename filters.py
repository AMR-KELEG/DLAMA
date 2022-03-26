from constants import *

FILTERS_DICTIONARY = {
    # Subject should be a person
    "occupation": {
        "common": f"?{PERSON} wdt:P106 ?{OCCUPATION} . # Occupation",
        "politics": f"{{?{OCCUPATION} wdt:P31 wd:Q303618}} # The occupation is instance of diplomatic rank\n"
        "UNION\n"
        f"{{?{PERSON} wdt:P106 wd:Q82955}} . # The occupation is politician",
        "music": f"?{OCCUPATION} wdt:P31+ wd:Q66715801 . # The occupation is instance of musical profession",
        "sports": f"?{OCCUPATION} wdt:P279+ wd:Q2066131 . # The occupation is subclass of athlete",
        "cinema_and_theatre": f"{{?{OCCUPATION} wdt:P279+ wd:Q713200}} . # The occupation is a subclass of performing artist\n"
        "MINUS # The occupation is instance of musical profession\n"
        f"{{?{OCCUPATION} wdt:P31+ wd:Q66715801}} . ",
    },
    "sports": {"football": f"?{CLUB} wdt:P31 wd:Q476028 . # Club is a football club"},
    "region_country": {
        ARAB_REGION: f"?{COUNTRY} wdt:P463 wd:Q7172 . # Make sure the country belongs to the Arab league",
    },
    # TODO: Fix this
    "misc": {
        "a_language": f"?{LANGUAGE} wdt:P31 wd:Q34770 . # Make sure it's an instance of language",
        # TODO: Fix this (it's not working!)
        "not_ancient": f"MINUS {{ {{?{CITY} wdt:P31 wd:Q15661340}} UNION {{?{CITY} wdt:P31 wd:Q2974842}} }} . # Make sure it's not an instance of ancient cities",
    },
}
