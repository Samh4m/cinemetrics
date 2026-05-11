"""Ingest movie data from the TMDB API.

This module fetches data from TMDB's REST API and saves the raw JSON
responses to disk under data/raw/tmdb/. The raw layer is intentionally
untransformed — downstream dbt models handle cleaning, modeling, and analytics.

Two ingestion modes:
- popular: snapshot of currently-popular movies (incremental, daily).
  Partitioned by ingestion date.
- discover: bulk historical load of all movies for a given year.
  Partitioned by release year.

Usage:
    python -m cinemetrics.ingestion.tmdb popular
    python -m cinemetrics.ingestion.tmdb discover --year 2024
"""

import argparse
import json
import os
import time
from datetime import date
from pathlib import Path

import httpx
from dotenv import load_dotenv


TMDB_API_BASE = "https://api.themoviedb.org/3"


def fetch_popular_movies(token: str, page: int = 1) -> dict:
    """Fetch one page of popular movies from TMDB.

    Args:
        token: The TMDB v4 API Read Access Token.
        page: Which page of results to fetch (TMDB returns 20 per page).

    Returns:
        The parsed JSON response as a Python dict.
    """
    url = f"{TMDB_API_BASE}/movie/popular"
    headers = {"Authorization": f"Bearer {token}"}
    params = {"page": page}

    response = httpx.get(url, headers=headers, params=params, timeout=30.0)
    response.raise_for_status()

    return response.json()


def fetch_discover_movies(token: str, year: int, page: int = 1) -> dict:
    """Fetch one page of movies released in a given year.

    Args:
        token: The TMDB v4 API Read Access Token.
        year: The release year to filter by (uses primary_release_date range).
        page: Which page of results to fetch (TMDB returns 20 per page).

    Returns:
        The parsed JSON response as a Python dict.
    """
    url = f"{TMDB_API_BASE}/discover/movie"
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "primary_release_date.gte": f"{year}-01-01",
        "primary_release_date.lte": f"{year}-12-31",
        "page": page,
        "sort_by": "popularity.desc",
    }

    response = httpx.get(url, headers=headers, params=params, timeout=30.0)
    response.raise_for_status()

    return response.json()


def save_response(data: dict, endpoint: str, partition_date: date) -> Path:
    """Save the raw API response to disk, partitioned by endpoint and date.

    Args:
        data: The parsed JSON response.
        endpoint: A short name for the endpoint (e.g., "popular").
        partition_date: The date to partition under.

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


def save_discover_page(data: dict, year: int, page: int) -> Path:
    """Save one page of discover results, partitioned by release year."""
    data_dir = Path(os.environ.get("DATA_DIR", "data/raw"))
    output_dir = data_dir / "tmdb" / "discover" / f"release_year={year}"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"page={page:03d}.json"
    with output_path.open("w") as f:
        json.dump(data, f, indent=2)

    return output_path


def run_popular(token: str) -> None:
    """Fetch one page of popular movies and save it."""
    today = date.today()

    print(f"Fetching popular movies for {today.isoformat()}...")
    data = fetch_popular_movies(token)

    print(f"Got {len(data['results'])} movies on page {data['page']} of {data['total_pages']}.")

    output_path = save_response(data, endpoint="popular", partition_date=today)
    print(f"Saved to {output_path}")


def run_discover_backfill(token: str, year: int) -> None:
    """Fetch ALL pages of discover results for a given year, saving each separately."""
    print(f"Starting discover backfill for {year}...")

    # Fetch page 1 first to learn how many pages exist.
    first_page = fetch_discover_movies(token, year, page=1)
    total_pages = first_page["total_pages"]
    total_results = first_page["total_results"]

    # TMDB caps pagination at 500 pages.
    pages_to_fetch = min(total_pages, 500)
    if total_pages > 500:
        print(f"Year {year} has {total_pages} pages but TMDB caps at 500. Fetching first 500.")

    print(f"Found {total_results} movies across {total_pages} pages. Fetching {pages_to_fetch}.")

    # Save the first page (we already have it).
    save_discover_page(first_page, year, page=1)

    # Fetch and save the rest.
    for page in range(2, pages_to_fetch + 1):
        try:
            data = fetch_discover_movies(token, year, page=page)
            save_discover_page(data, year, page=page)

            if page % 50 == 0:
                print(f"  ...fetched page {page}/{pages_to_fetch}")

            time.sleep(0.25)  # Be polite: ~4 req/sec, well under TMDB's limit.
        except httpx.HTTPStatusError as e:
            print(f"  Error on page {page}: {e}. Continuing.")
            continue

    print(f"Backfill for {year} complete.")


def main() -> None:
    """CLI entry point: dispatch to the right ingestion function based on args."""
    parser = argparse.ArgumentParser(
        description="Ingest movie data from the TMDB API."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # `popular` subcommand: takes no extra arguments.
    subparsers.add_parser("popular", help="Fetch one page of currently popular movies.")

    # `discover` subcommand: takes a required --year flag.
    discover_parser = subparsers.add_parser(
        "discover", help="Bulk fetch all movies released in a given year."
    )
    discover_parser.add_argument(
        "--year", type=int, required=True, help="The release year to fetch."
    )

    args = parser.parse_args()

    load_dotenv()
    token = os.environ["TMDB_API_TOKEN"]

    if args.command == "popular":
        run_popular(token)
    elif args.command == "discover":
        run_discover_backfill(token, year=args.year)


if __name__ == "__main__":
    main()