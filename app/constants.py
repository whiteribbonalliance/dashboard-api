import json

from app.enums.campaign_code import CampaignCode
from app.enums.question_code import QuestionCode

CAMPAIGN_CODES = [campaign.value for campaign in CampaignCode]

QUESTION_CODES = [q.value for q in QuestionCode]

# Load stopwords from file
with open("stopwords.json", "r", encoding="utf8") as file:
    STOPWORDS: dict = json.loads(file.read())

# Load countries data from file
with open("countries_data.json", "r") as file:
    COUNTRIES_DATA: dict = json.loads(file.read())


# This is nominally the coordinates of the capital of each country
# but where they appear too close together on the map I have shifted them slightly.
# All lat/longs are definitely inside the country that they are supposed to be in,
# but they are sometimes not the capital if that capital is very close to the capital of another country.
COUNTRY_COORDINATE = {}
for key, value in COUNTRIES_DATA.items():
    COUNTRY_COORDINATE[key] = value["coordinates"]

# Languages supported by Cloud Translation API
TRANSLATION_LANGUAGES = {
    "af": {"name": "Afrikaans"},
    "ak": {"name": "Akan"},
    "am": {"name": "አማርኛ"},
    "ar": {"name": "العربية"},
    "as": {"name": "অসমীয়া"},
    "ay": {"name": "Aymar aru"},
    "az": {"name": "azərbaycan"},
    "be": {"name": "беларуская"},
    "bg": {"name": "български"},
    "bho": {"name": "भोजपुरी"},
    "bm": {"name": "bamanakan"},
    "bn": {"name": "বাংলা"},
    "bs": {"name": "bosanski"},
    "ca": {"name": "català"},
    "ceb": {"name": "Binisaya"},
    "ckb": {"name": "کوردیی ناوەندی"},
    "co": {"name": "corsu"},
    "cs": {"name": "čeština"},
    "cy": {"name": "Cymraeg"},
    "da": {"name": "dansk"},
    "de": {"name": "Deutsch"},
    "doi": {"name": "डोगरी"},
    "dv": {"name": "ދިވެހި"},
    "ee": {"name": "Eʋegbe"},
    "el": {"name": "Ελληνικά"},
    "en": {"name": "English"},
    "eo": {"name": "esperanto"},
    "es": {"name": "español"},
    "et": {"name": "eesti"},
    "eu": {"name": "euskara"},
    "fa": {"name": "فارسی"},
    "fi": {"name": "suomi"},
    "fil": {"name": "Filipino"},
    "fr": {"name": "français"},
    "fy": {"name": "Frysk"},
    "ga": {"name": "Gaeilge"},
    "gd": {"name": "Gàidhlig"},
    "gl": {"name": "galego"},
    "gn": {"name": "Avañeʼẽ"},
    "gom": {"name": "कोंकणी"},
    "gu": {"name": "ગુજરાતી"},
    "ha": {"name": "Hausa"},
    "haw": {"name": "ʻŌlelo Hawaiʻi"},
    "he": {"name": "עברית"},
    "hi": {"name": "हिन्दी"},
    "hmn": {"name": "lus Hmoob"},
    "hr": {"name": "hrvatski"},
    "ht": {"name": "kreyòl ayisyen"},
    "hu": {"name": "magyar"},
    "hy": {"name": "հայերեն"},
    "id": {"name": "Indonesia"},
    "ig": {"name": "Asụsụ Igbo"},
    "ilo": {"name": "Ilokano"},
    "is": {"name": "íslenska"},
    "it": {"name": "italiano"},
    "ja": {"name": "日本語"},
    "jv": {"name": "Jawa"},
    "ka": {"name": "ქართული"},
    "kk": {"name": "қазақ тілі"},
    "km": {"name": "ខ្មែរ"},
    "kn": {"name": "ಕನ್ನಡ"},
    "ko": {"name": "한국어"},
    "kri": {"name": "Krio"},
    "ku": {"name": "kurdî"},
    "ky": {"name": "кыргызча"},
    "la": {"name": "Lingua Latīna"},
    "lb": {"name": "Lëtzebuergesch"},
    "lg": {"name": "Luganda"},
    "ln": {"name": "lingála"},
    "lo": {"name": "ລາວ"},
    "lt": {"name": "lietuvių"},
    "lus": {"name": "Mizo ṭawng"},
    "lv": {"name": "latviešu"},
    "mai": {"name": "मैथिली"},
    "mg": {"name": "Malagasy"},
    "mi": {"name": "Māori"},
    "mk": {"name": "македонски"},
    "ml": {"name": "മലയാളം"},
    "mn": {"name": "монгол"},
    "mni_mtei": {"name": "ꯃꯩꯇꯩꯂꯣꯟ"},
    "mr": {"name": "मराठी"},
    "ms": {"name": "Melayu"},
    "mt": {"name": "Malti"},
    "my": {"name": "မြန်မာ"},
    "ne": {"name": "नेपाली"},
    "nl": {"name": "Nederlands"},
    "no": {"name": "norsk"},
    "nso": {"name": "Sepedi"},
    "ny": {"name": "Chichewa"},
    "om": {"name": "Oromoo"},
    "or": {"name": "ଓଡ଼ିଆ"},
    "pa": {"name": "ਪੰਜਾਬੀ"},
    "pl": {"name": "polski"},
    "ps": {"name": "پښتو"},
    "pt": {"name": "português"},
    "qu": {"name": "Runasimi"},
    "ro": {"name": "română"},
    "ru": {"name": "русский"},
    "rw": {"name": "Kinyarwanda"},
    "sa": {"name": "संस्कृत"},
    "sd": {"name": "سنڌي"},
    "si": {"name": "සිංහල"},
    "sk": {"name": "slovenčina"},
    "sl": {"name": "slovenščina"},
    "sm": {"name": "Gagana faʻa Sāmoa"},
    "sn": {"name": "chiShona"},
    "so": {"name": "Soomaali"},
    "sq": {"name": "shqip"},
    "sr": {"name": "српски"},
    "st": {"name": "Sesotho"},
    "su": {"name": "Basa Sunda"},
    "sv": {"name": "svenska"},
    "sw": {"name": "Kiswahili"},
    "ta": {"name": "தமிழ்"},
    "te": {"name": "తెలుగు"},
    "tg": {"name": "тоҷикӣ"},
    "th": {"name": "ไทย"},
    "ti": {"name": "ትግርኛ"},
    "tk": {"name": "türkmen dili"},
    "tl": {"name": "Tagalog"},
    "tr": {"name": "Türkçe"},
    "ts": {"name": "Xitsonga"},
    "tt": {"name": "татар"},
    "ug": {"name": "ئۇيغۇرچە"},
    "uk": {"name": "українська"},
    "ur": {"name": "اردو"},
    "uz": {"name": "o‘zbek"},
    "vi": {"name": "Tiếng Việt"},
    "xh": {"name": "isiXhosa"},
    "yi": {"name": "ייִדיש"},
    "yo": {"name": "Èdè Yorùbá"},
    "zh": {"name": "中国人"},
    "zh_tw": {"name": "中國人"},
    "zu": {"name": "isiZulu"},
}

TRANSLATIONS_JSON = "translations.json"

ACCESS_TOKEN_EXPIRE_DAYS = 30

n_wordcloud_words = 100
n_top_words = 20

n_responses_sample = 1000
