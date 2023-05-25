import json


def get_countries_data_list() -> dict:
    with open("countries_data.json", "r") as countries_data:
        countries = json.loads(countries_data.read())

    return countries
