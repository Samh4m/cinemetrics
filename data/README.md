# data/

This folder holds local data artifacts: raw JSON files from ingestion, intermediate Parquet caches, and the local DuckDB database file (`cinemetrics.duckdb`).

**Nothing in this folder is committed to Git.** Each developer's machine has its own local copy.

To rebuild the contents of this folder from scratch:

```bash
# Re-ingest the raw data
uv run python -m cinemetrics.ingestion.tmdb popular
uv run python -m cinemetrics.ingestion.tmdb discover --year 2024

# Re-load into DuckDB
uv run python -m cinemetrics.loading.duckdb_loader
```

Generated subfolders:

- `raw/` — JSON files from API ingestion, partitioned by source and date
- `staging/` — intermediate transformations (reserved for future use)
- `cinemetrics.duckdb` — the local analytics database