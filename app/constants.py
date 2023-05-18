import pycountry

COUNTRY_ALPHA_2_TO_NAME = {}
for country in pycountry.countries:
    COUNTRY_ALPHA_2_TO_NAME[country.alpha_2] = country.name
