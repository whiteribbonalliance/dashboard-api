"""Google Maps interactions"""

import googlemaps

from app import env


def get_googlemaps_client() -> googlemaps.Client:
    """Get Google Maps client"""

    return googlemaps.Client(key=env.GOOGLE_MAPS_API_KEY)


def get_coordinate(location: str) -> dict:
    """Get coordinate"""

    client = get_googlemaps_client()
    geocode_result = client.geocode(location)
    if len(geocode_result) > 0:
        geometry = geocode_result[0].get("geometry")
        if geometry:
            location = geometry.get("location")

            return {"lat": location.get("lat"), "lon": location.get("lng")}

    return {}
