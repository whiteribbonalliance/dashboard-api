from enum import Enum


class CampaignCode(str, Enum):
    what_women_want: str = "wra03a"
    what_young_people_want: str = "pmn01a"
    midwives_voices: str = "midwife"
    # mexico: str = "giz"
    # pakistan: str = "wwwpakistan"
    healthwellbeing: str = "healthwellbeing"
