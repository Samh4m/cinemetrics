# ADR-0001: Use date range filter (not primary_release_year) for TMDB discover ingestion

## Status

Accepted — 2026-05-11

## Context

The initial implementation of the discover backfill used TMDB's `primary_release_year`
query parameter, expecting it to return movies with that primary release year. Auditing
the resulting 2024 dataset (10,000 movies sampled across 500 pages, sorted by popularity)
revealed that **95.7% of returned movies had a `release_date` outside of 2024**, including:

- Movies from prior decades (e.g., *The Devil Wears Prada* (2006), *Malena* (2000))
- Movies with future release dates (e.g., *The Super Mario Galaxy Movie* (2026),
  *Project Hail Mary* (2026))

The filter parameter does not behave as its name implies. Per TMDB community discussions,
`primary_release_year` reflects the "primary release" field, which is influenced by the
earliest known release date across all countries and re-release events, and appears to
weakly constrain results at scale. In practice, the filter is so permissive that the
result set is dominated by the `sort_by=popularity.desc` ordering, returning the most
popular movies globally rather than the most popular movies released in the requested year.

## Decision

Replace `primary_release_year=YEAR` with an explicit date range:

This filters by an explicit, unambiguous date range against the primary release date,
which is the canonical "this is when the movie came out" field.

## Consequences

**Positive:**

- After the fix, an audit of 10,000 sampled 2024 movies showed **0 records with a
  `release_date` outside 2024** — the filter now behaves as intended.
- Date ranges allow for finer-grained filtering in the future (e.g., specific months
  or quarters within a year).
- The filter semantics are now explicit in the query string. A future engineer reading
  the params dict can see exactly what's being filtered without relying on TMDB's
  interpretation of a year alias.

**Negative:**

- The discover endpoint still returns at most 500 pages × 20 results = 10,000 movies
  per query, due to TMDB's hard pagination cap. For 2024, TMDB reports 2,653 total
  pages (~53,000 movies released in 2024); we sample only the most popular 10,000.
  This is acceptable for analytics use cases but means the dataset is not exhaustive.

**Process learnings:**

- **Always audit a fresh dataset before assuming a filter behaves as its name suggests.**
  API documentation, parameter names, and actual behavior are not always aligned.
- The bronze layer's purpose includes catching exactly this class of bug: had we
  loaded directly into a `movies_2024` warehouse table, the bad data would have been
  permanent and the bug invisible. By saving raw JSON to disk and auditing before
  transforming, we preserved the option to fix the upstream query without losing work.
- A simple Python audit script (`audit_discover.py`) — checking the proportion of
  records matching the expected filter — is a cheap, high-value tool. Future ingestion
  changes will include a similar verification step.