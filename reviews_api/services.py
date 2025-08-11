# reviews_api/services.py
import requests
from django.conf import settings

def get_movie_details(title):
    api_key = settings.OMDB_API_KEY
    base_url = "http://www.omdbapi.com/"
    params = {
        't': title,
        'apikey': api_key
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        if data.get("Response") == "True":
            return data
        return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching movie data: {e}")
        return None