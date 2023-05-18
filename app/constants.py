import pycountry

from app.enums.campaigns import Campaigns

COUNTRY_ALPHA_2_TO_NAME = {
    country.alpha_2: country.name for country in pycountry.countries
}

CAMPAIGNS_LIST = [
    Campaigns.what_women_want.value,
    Campaigns.what_young_people_want.value,
    Campaigns.midwives_voices.value,
]
