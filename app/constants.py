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
COUNTRY_COORDINATE = {
    "MW": [-13.9626, 33.7741],
    "CA": [45.421106, -75.690308],
    "EC": [-0.220164, -78.512327],
    "BI": [-3.363812, 29.367503],
    "ZW": [-17.831773, 31.045686],
    "IN": [26.7041, 79.1025],
    "FI": [60.16741, 24.942577],
    "MA": [34.022405, -6.834543],
    "FR": [48.856697, 2.351462],
    "US": [38.894986, -77.036571],
    "GR": [37.983941, 23.728305],
    "FJ": [-18.141588, 178.442166],
    "BR": [-10.333333, -53.2],
    "GY": [6.802577, -58.162861],
    "HT": [18.547327, -72.339593],
    "AG": [47.561701, -52.715149],
    "ZA": [-25.745937, 28.187944],
    "NP": [27.708317, 85.320582],
    "ET": [9.010793, 38.761252],
    "PG": [-9.47433, 147.15995],
    "GH": [5.560014, -0.205744],
    "AR": [-34.607568, -58.437089],
    "SE": [59.325117, 18.071094],
    "MT": [35.898982, 14.513676],
    "LS": [-29.310054, 27.478222],
    "NL": [52.37276, 4.893604],
    "LR": [6.328034, -10.797788],
    "BB": [13.097783, -59.618418],
    "NZ": [-41.288795, 174.777211],
    "BJ": [6.499072, 2.625336],
    "LT": [54.687046, 25.282911],
    "VG": [18.4207, -64.64],
    "KH": [11.568271, 104.922443],
    "BH": [26.223504, 50.582244],
    "DK": [55.686724, 12.570072],
    "AF": [34.526011, 69.177684],
    "IL": [31.778345, 35.225079],
    "SA": [24.631969, 46.715065],
    "BW": [-24.658136, 25.908847],
    "SY": [33.51307, 36.309581],
    "ID": [-6.175394, 106.827183],
    "PL": [52.233717, 21.071411],
    "PH": [14.590622, 120.97997],
    "ML": [12.605033, -7.986514],
    "RW": [-1.88596, 30.129675],
    "BT": [27.472762, 89.629548],
    "UY": [-34.905904, -56.191357],
    "TG": [6.130419, 1.215829],
    "AT": [48.208354, 16.372504],
    "ER": [15.338967, 38.932676],
    "GT": [14.622233, -90.518519],
    "PF": [-17.537384, -149.565996],
    "TL": [-8.8742, 125.7275],
    "LC": [13.952589, -60.987824],
    "CH": [46.948271, 7.451451],
    "AU": [-35.297591, 149.101268],
    "NO": [59.91333, 10.73897],
    "TZ": [-6.163, 35.7516],
    "CM": [2.848, 12.5021],
    "CL": [9.869479, -83.798075],
    "TR": [39.920777, 32.854067],
    "SN": [14.693425, -17.447938],
    "GM": [13.4432, -15.3101],
    "BD": [23.759357, 90.378814],
    "DZ": [36.775361, 3.060188],
    "CR": [9.932543, -84.079578],
    "KE": [-1.2921, 39.8219],
    "RO": [44.436141, 26.10272],
    "MX": [19.4326, -99.1332],
    "IE": [53.349764, -6.260273],
    "CI": [7.54, -5.5471],
    "UG": [2.3476, 31.582500000000003],
    "IT": [41.89332, 12.482932],
    "BF": [12.368187, -1.527094],
    "TT": [10.657268, -61.518017],
    "DM": [48.771037, -95.769788],
    "JM": [17.971215, -76.792813],
    "SR": [5.821609, -55.177043],
    "KN": [17.296092, -62.722301],
    "IS": [64.145981, -21.942237],
    "PY": [-25.280046, -57.634381],
    "PK": [34.6844, 72.0479],
    "ZM": [-15.416449, 28.282154],
    "BG": [-15.25384, 48.256216],
    "PE": [-12.062106, -77.036526],
    "BS": [25.0343, -77.3963],
    "SD": [15.593325, 32.53565],
    "GB": [51.507322, -0.127647],
    "SL": [8.479004, -13.26795],
    "AE": [24.474796, 54.370576],
    "DE": [52.517036, 13.38886],
    "IR": [35.6892, 51.389],
    "NA": [-22.574392, 17.079069],
    "ES": [40.416705, -3.703582],
    "VU": [-17.741497, 168.315016],
    "GA": [0.390002, 9.454001],
    "CD": [-4.4419, 15.2663],
    "SS": [4.847202, 31.595166],
    "SO": [2.042778, 45.338564],
    "NG": [10.0765, 6.3986],
    "PT": [38.707751, -9.136592],
    "AL": [41.0, 20.0],
    "AS": [-14.3333, -170.0],
    "AD": [42.5, 1.6],
    "AO": [-12.5, 18.5],
    "AI": [18.25, -63.1667],
    "AQ": [-90.0, 0.0],
    "AM": [40.0, 45.0],
    "AW": [12.5, -69.9667],
    "AZ": [40.5, 47.5],
    "BY": [53.0, 28.0],
    "BE": [50.8333, 4.0],
    "BZ": [17.25, -88.75],
    "BM": [32.3333, -64.75],
    "BO": [-17.0, -65.0],
    "BA": [44.0, 18.0],
    "BV": [-54.4333, 3.4],
    "IO": [-6.0, 71.5],
    "BN": [4.5, 114.6667],
    "CV": [16.0, -24.0],
    "KY": [19.5, -80.5],
    "CF": [7.0, 21.0],
    "TD": [15.0, 19.0],
    "CN": [35.0, 105.0],
    "CX": [-10.5, 105.6667],
    "CC": [-12.5, 96.8333],
    "CO": [4.0, -72.0],
    "KM": [-12.1667, 44.25],
    "CG": [-1.0, 15.0],
    "CK": [-21.2333, -159.7667],
    "HR": [45.1667, 15.5],
    "CU": [21.5, -80.0],
    "CY": [35.0, 33.0],
    "CZ": [49.75, 15.5],
    "DJ": [11.5, 43.0],
    "DO": [19.0, -70.6667],
    "EG": [27.0, 30.0],
    "SV": [13.8333, -88.9167],
    "GQ": [2.0, 10.0],
    "EE": [59.0, 26.0],
    "FK": [-51.75, -59.0],
    "FO": [62.0, -7.0],
    "GF": [4.0, -53.0],
    "TF": [-43.0, 67.0],
    "GE": [42.0, 43.5],
    "GI": [36.1833, -5.3667],
    "GL": [72.0, -40.0],
    "GD": [12.1167, -61.6667],
    "GP": [16.25, -61.5833],
    "GU": [13.4667, 144.7833],
    "GG": [49.5, -2.56],
    "GN": [11.0, -10.0],
    "GW": [12.0, -15.0],
    "HM": [-53.1, 72.5167],
    "VA": [41.9, 12.45],
    "HN": [15.0, -86.5],
    "HK": [22.25, 114.1667],
    "HU": [47.0, 20.0],
    "IQ": [33.0, 44.0],
    "IM": [54.23, -4.55],
    "JP": [36.0, 138.0],
    "JE": [49.21, -2.13],
    "JO": [31.0, 36.0],
    "KZ": [48.0, 68.0],
    "KI": [1.4167, 173.0],
    "KP": [40.0, 127.0],
    "KR": [37.0, 127.5],
    "KW": [29.3375, 47.6581],
    "KG": [41.0, 75.0],
    "LA": [18.0, 105.0],
    "LV": [57.0, 25.0],
    "LB": [33.8333, 35.8333],
    "LY": [25.0, 17.0],
    "LI": [47.1667, 9.5333],
    "LU": [49.75, 6.1667],
    "MO": [22.1667, 113.55],
    "MK": [41.8333, 22.0],
    "MG": [-20.0, 47.0],
    "MY": [2.5, 112.5],
    "MV": [3.25, 73.0],
    "MH": [9.0, 168.0],
    "MQ": [14.6667, -61.0],
    "MR": [20.0, -12.0],
    "MU": [-20.2833, 57.55],
    "YT": [-12.8333, 45.1667],
    "FM": [6.9167, 158.25],
    "MD": [47.0, 29.0],
    "MC": [43.7333, 7.4],
    "MN": [46.0, 105.0],
    "ME": [42.0, 19.0],
    "MS": [16.75, -62.2],
    "MZ": [-18.25, 35.0],
    "MM": [22.0, 98.0],
    "NR": [-0.5333, 166.9167],
    "AN": [12.25, -68.75],
    "NC": [-21.5, 165.5],
    "NI": [13.0, -85.0],
    "NE": [16.0, 8.0],
    "NU": [-19.0333, -169.8667],
    "NF": [-29.0333, 167.95],
    "MP": [15.2, 145.75],
    "OM": [21.0, 57.0],
    "PW": [7.5, 134.5],
    "PS": [32.0, 35.25],
    "PA": [9.0, -80.0],
    "PN": [-24.7, -127.4],
    "PR": [18.25, -66.5],
    "QA": [25.5, 51.25],
    "RE": [-21.1, 55.6],
    "RU": [60.0, 100.0],
    "SH": [-15.9333, -5.7],
    "PM": [46.8333, -56.3333],
    "VC": [13.25, -61.2],
    "WS": [-13.5833, -172.3333],
    "SM": [43.7667, 12.4167],
    "ST": [1.0, 7.0],
    "RS": [44.0, 21.0],
    "SC": [-4.5833, 55.6667],
    "SG": [1.3667, 103.8],
    "SK": [48.6667, 19.5],
    "SI": [46.0, 15.0],
    "SB": [-8.0, 159.0],
    "GS": [-54.5, -37.0],
    "LK": [7.0, 81.0],
    "SJ": [78.0, 20.0],
    "SZ": [-26.5, 31.5],
    "TW": [23.5, 121.0],
    "TJ": [39.0, 71.0],
    "TH": [15.0, 100.0],
    "TK": [-9.0, -172.0],
    "TO": [-20.0, -175.0],
    "TN": [34.0, 9.0],
    "TM": [40.0, 60.0],
    "TC": [21.75, -71.5833],
    "TV": [-8.0, 178.0],
    "UA": [49.0, 32.0],
    "UM": [19.2833, 166.6],
    "UZ": [41.0, 64.0],
    "VE": [8.0, -66.0],
    "VN": [16.0, 106.0],
    "VI": [18.3333, -64.8333],
    "WF": [-13.3, -176.2],
    "EH": [24.5, -13.0],
    "YE": [15.0, 48.0],
}

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
