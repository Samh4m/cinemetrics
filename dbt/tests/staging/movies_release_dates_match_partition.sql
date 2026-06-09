-- ADR-0001 protection: the TMDB primary_release_date filter is unreliable.
-- This test confirms that the rows landing in stg_movies actually have
-- release dates in 2024 (the partition we're targeting in V1).
--
-- A row showing up here is a row TMDB returned for our 2024 query that's
-- NOT actually from 2024. If this test fails, our filter has regressed
-- or TMDB's behavior has changed again.

SELECT
    movie_id,
    title,
    release_date
FROM {{ ref('stg_movies') }}
WHERE release_date IS NOT NULL
    AND NOT (release_date >= '2024-01-01' AND release_date <= '2024-12-31')