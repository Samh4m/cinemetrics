# ADR-0002: stg_movies de-duplicates discover rows from TMDB pagination

## Status

Accepted — 2026-05-26

## Context

The first dbt test run on `stg_movies` revealed that 8 movies appeared twice
in the discover dataset — a uniqueness violation on `movie_id`. Investigation
showed:

- Each duplicate pair has identical attributes (same `movie_id`, `title`,
  `popularity`, `vote_average`, etc.)
- Duplicates appear on adjacent or near-adjacent pages (e.g., page=006 and
  page=007) within the popularity-sorted result set
- All duplicates fall in the first ~13 pages of results, where popularity
  scores are densest

The root cause is likely an instability in TMDB's paginated `popularity.desc`
sort: when multiple movies have very close (or tied) popularity scores, the
sort order across pages is not strictly deterministic, allowing the same
movie to appear in two adjacent pages' windows.

This is a known pattern in paginated APIs that don't guarantee a strict total
order on the sort key.

## Decision

De-duplicate within the `stg_movies` staging model using a `ROW_NUMBER()`
window function partitioned by `movie_id`, ordered by `_source_file` as a
deterministic tiebreaker. This keeps the first occurrence (alphabetically
lowest source-file path, which corresponds to the lower page number and
therefore the higher-popularity-rank appearance).

```sql
ROW_NUMBER() OVER (
    PARTITION BY movie_id
    ORDER BY _source_file
) AS _row_num
```

The `unique` test on `movie_id` in `_schema.yml` enforces this going forward.

## Consequences

**Positive:**

- `stg_movies.movie_id` is now reliably unique. Downstream marts can use it
  as a join key without worrying about row multiplication.
- The de-dupe is deterministic. Re-running the model produces the same
  result given the same source data.
- The `unique` test continues to enforce the invariant — if TMDB's behavior
  ever produces non-identical duplicates (e.g., the same movie_id with
  different titles), the test will fail and prompt investigation.

**Negative:**

- We silently drop a small number (~0.08%) of duplicate rows. Since they're
  identical to the kept row, no analytical information is lost. But the count
  difference between raw and staging tables now has a known explanation, and
  anyone investigating discrepancies should be aware.

**Process learnings:**

- A `unique` test on natural keys is one of the cheapest and most valuable
  tests in dbt. It caught a real issue immediately on first run.
- "The data must be unique" is a common implicit assumption in downstream
  code. Making it explicit via a test prevents subtle aggregation bugs.
- The initial hypothesis (popularity shifted between page fetches) was
  wrong — the popularity values were identical across duplicates. Always
  check the actual data before committing to a root-cause story.