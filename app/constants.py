from app.enums.campaign_code import CampaignCode

CAMPAIGNS_LIST = [
    CampaignCode.what_women_want.value,
    CampaignCode.what_young_people_want.value,
    CampaignCode.midwives_voices.value,
]

# Load stopwords from file
with open("stopwords.txt", "r") as file:
    STOPWORDS: set[str] = {line.rstrip() for line in file}
