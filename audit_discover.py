"""Quick audit script: how many movies in our 2024 backfill aren't actually from 2024?

Run with: uv run python audit_discover.py
"""

import json
from pathlib import Path


def main() -> None:
    count_total = 0
    count_not_2024 = 0
    bad_examples = []

    discover_dir = Path("data/raw/tmdb/discover/release_year=2024")
    for f in sorted(discover_dir.glob("page=*.json")):
        data = json.loads(f.read_text())
        for movie in data["results"]:
            count_total += 1
            release_date = movie.get("release_date", "")
            if not release_date.startswith("2024"):
                count_not_2024 += 1
                if len(bad_examples) < 10:
                    bad_examples.append((movie["title"], release_date))

    pct = 100 * count_not_2024 / count_total if count_total > 0 else 0
    print(f"Total movies: {count_total}")
    print(f"Not released in 2024: {count_not_2024} ({pct:.1f}%)")
    print("\nFirst 10 examples:")
    for title, rd in bad_examples:
        print(f"  - {title!r}: release_date={rd!r}")


if __name__ == "__main__":
    main()