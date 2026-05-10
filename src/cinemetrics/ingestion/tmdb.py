"""Ingest movie data from the TMDB API

This module fetches data from TMDB's REST API and saves the raw JSON
response to disk under data/raw/tmdb/, partitioned by endpoint and date.
The raw layer is intentnionally untransformed - downstream dbt models
handle cleaning, modeling, and analytics.
"""

import json
import os
from datetime import date
from pathlib import Path

import httpx
from dotenv import load_dotenv


TMDB_API_BASE = "https://api.themoviedb.org/3"


def fetch_popular_movies(token: str, page: int = 1) -> dict:
    """Fetch one page of popular movies from TMDB.
    
    Args:
        token: the TMDB v4 API Read Access Token.
        page: Which page of results to fetch (TMDB returns 20 per page).
        
    Returns: The parsed JSON response as a Python dict.
    """

    url = f"{TMDB_API_BASE}/movie/popular"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page": page}

    response = httpx.get(url, headers=headers, params=params, timeout=30.0)
    response.raise_for_status()

    return response.json()


def save_response(data: dict, endpoint: str, partition_date: date) -> Path:
    """Save the raw API response to disk, partitioned by endpoint and date.
    
    Args: 
        data: The parsed JSON response.
        endpoint: A short name for the endpoint (e.g., "popular").
        
    Returns:
        The path to the saved file.
    """
    data_dir = Path(os.environ.get("DATA_DIR", "data/raw"))
    output_dir = data_dir / "tmdb" / endpoint / f"date={partition_date.isoformat()}"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "response.json"
    with output_path.open("w") as f:
        json.dump(data, f, indent=2)

    return output_path


def main() -> None:
    """Entry point: load .env, fetch popular movies, save to disk."""
    load_dotenv()

    token = os.environ["TMDB_API_TOKEN"]
    today = date.today()

    print(f"Fetching popular movies for {today.isoformat()}...")
    data = fetch_popular_movies(token)

    print(f"Got {len(data['results'])} movies on page {data['page']} of {data['total_pages']}.")

    output_path = save_response(data, endpoint="popular", partition_date=today)
    print(f"Saved to {output_path}")



if __name__ == "__main__":
    main()
