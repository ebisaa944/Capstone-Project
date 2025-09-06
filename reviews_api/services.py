# reviews_api/services.py
import logging
from typing import Optional, Dict, Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def get_movie_details(title: str) -> Optional[Dict[str, Any]]:
    """
    Fetch movie details from the OMDB API.

    Args:
        title (str): The title of the movie to search.

    Returns:
        dict: Movie details if found.
        None: If the movie is not found or an error occurs.
    """
    api_key = getattr(settings, "OMDB_API_KEY", None)
    if not api_key:
        logger.error("OMDB_API_KEY is not set in Django settings.")
        return None

    base_url = "http://www.omdbapi.com/"
    params = {"t": title, "apikey": api_key}

    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("Response") == "True":
            return data

        logger.warning("OMDB API returned no results for title: %s", title)
        return None

    except requests.exceptions.Timeout:
        logger.error("OMDB API request timed out for title: %s", title)
    except requests.exceptions.RequestException as e:
        logger.error("Error fetching movie data for title %s: %s", title, e)

    return None
