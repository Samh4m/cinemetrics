"""Load TMDB raw JSON data into DuckDB as queryable tables.

Reads all paginated JSON files from data/raw/tmdb/ and loads them into a
single `raw_movies` table in data/cinemetrics.duckdb. The source file path
is preserved as a column so we can trace any row back to its origin —
essential for debugging and for understanding ingestion lineage.
"""

import os
from pathlib import Path

import duckdb
from dotenv import load_dotenv


def load_discover_to_duckdb(db_path: Path, raw_dir: Path) -> int:
    """Load all discover/* JSON files into raw_movies. Returns row count.

    Uses DuckDB's read_json function with the union_by_name option to
    handle minor schema variations across files (e.g., missing optional
    fields on some movies).
    """
    discover_glob = str(raw_dir / "tmdb" / "discover" / "release_year=*" / "page=*.json")

    con = duckdb.connect(str(db_path))
    try:
        # Drop and recreate the table on each run. For V1, this is fine:
        # ingestion is small and idempotent. Later we'll do incremental loads.
        con.execute("DROP TABLE IF EXISTS raw_movies_discover;")
        con.execute(
            f"""
            CREATE TABLE raw_movies_discover AS
            SELECT
                filename,
                unnest(results, recursive := true)
            FROM read_json(
                '{discover_glob}',
                union_by_name := true,
                filename := true
            );
            """
        )
        row_count = con.execute("SELECT COUNT(*) FROM raw_movies_discover;").fetchone()[0]
    finally:
        con.close()

    return row_count


def load_popular_to_duckdb(db_path: Path, raw_dir: Path) -> int:
    """Load all popular/* JSON files into raw_movies_popular. Returns row count."""
    popular_glob = str(raw_dir / "tmdb" / "popular" / "date=*" / "response.json")

    con = duckdb.connect(str(db_path))
    try:
        con.execute("DROP TABLE IF EXISTS raw_movies_popular;")
        con.execute(
            f"""
            CREATE TABLE raw_movies_popular AS
            SELECT
                filename,
                unnest(results, recursive := true)
            FROM read_json(
                '{popular_glob}',
                union_by_name := true,
                filename := true
            );
            """
        )
        row_count = con.execute("SELECT COUNT(*) FROM raw_movies_popular;").fetchone()[0]
    finally:
        con.close()

    return row_count


def main() -> None:
    """Load all raw TMDB data into DuckDB and print summary stats."""
    load_dotenv()

    data_dir = Path(os.environ.get("DATA_DIR", "data/raw"))
    db_path = Path("data/cinemetrics.duckdb")

    # Ensure parent directory exists.
    db_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading raw data from {data_dir} into {db_path}...")

    discover_rows = load_discover_to_duckdb(db_path, data_dir)
    print(f"  raw_movies_discover: {discover_rows:,} rows")

    popular_rows = load_popular_to_duckdb(db_path, data_dir)
    print(f"  raw_movies_popular:  {popular_rows:,} rows")

    print("Done.")


if __name__ == "__main__":
    main()