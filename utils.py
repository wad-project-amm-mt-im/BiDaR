import re

import pycountry

COUNTRIES = [country.name for country in pycountry.countries]

INGREDIENTS = ['onion', 'chicken', 'garlic']

regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'


def check(email):
    if re.fullmatch(regex, email):
        return True
    return False
