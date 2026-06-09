# ADR-0003: Use a CSV seed for the TMDB genre lookup

## Status

Accepted — 2026-06-09

## Context

The stg_movies table contains a genre_ids column with arrays of TMDB genre IDs (e.g., [28, 12, 878]). While useful for source systems, these numeric IDs are not meaningful for analytics and reporting. To enable genre-based analysis, the IDs must be mapped to human-readable names such as "Action," "Adventure," and "Science Fiction."

TMDB provides the canonical genre mapping through its /genre/movie/list endpoint. The dataset is small (around 19 movie genres) and changes rarely, making it suitable as a reference lookup table for downstream marts.

## Options considered

### Option 1: CSV seed in dbt/seeds/

We write and read our own csv based off of what we need from the documentation in the website. We create a seeds/ to check for null and uniqueness.

**Pros:**
- Since it's a small API list, we do not need to call the API all the time and can maintain it ourselves
- Easy for new contributors to inspect and edit

**Cons:**
- If it updates and we don't know about it, it might mess with the data a little but this rarely happens
- Doesn't run unless we explicitly run dbt seed

### Option 2: Ingest via Python from /genre/movie/list

We do an API call and ingest the genres list, this takes more work and time

**Pros:**
- A more accurate list of genres and easy to update all the time
- consistent pattern

**Cons:**
- takes more time, more code to maintain and overkill for stable data
- Could fail mid pipeline if TMDB has an outage

### Option 3: Hardcoded CASE statement in the model

hardcoding a case statement

**Pros:**
- no new infrastructure
- No dependency

**Cons:**
- doesn't scale
- hard to read 

## Decision

We chose option 1 because the dataset is so small that ingesting it is not worth the effort. The cost of freshness automation outweighs the benefit for a list this stable. We can revisit this when TMDB updates the genre list consistently and more frequently.

## Consequences

**Positive:**
- We do not add a network dependency at build time
- Less code for us to maintain
- Easy to inspect because the genre list lives directly in the repository

**Negative or trade-offs accepted:**
- This does not always reflect TMDB's current state
- Updates require a manual change to the seed file
- The data may become stale if TMDB starts updating genres more frequently

**Future revisit triggers:**
- If TMDB begins adding or changing genres more frequently
- If we expand to TV show ingestion and need to support a separate genre endpoint
- If missing or NULL genre mappings appear because the seed has become outdated