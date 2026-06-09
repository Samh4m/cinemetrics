-- One row per (movie, genre) pair. Explodes the genre_ids array from
-- stg_movies and joins to the genre lookup seed.
--
-- This is an "intermediate" model — used by marts, not consumed directly
-- by stakeholders. Lives under models/intermediate/ by dbt convention.

WITH movies AS (
    SELECT
        movie_id,
        title,
        release_date,
        vote_average,
        vote_count,
        popularity,
        original_language,
        is_adult,
        genre_ids
    FROM {{ ref('stg_movies') }}
),

exploded AS (
    SELECT
        movie_id,
        title,
        release_date,
        vote_average,
        vote_count,
        popularity,
        original_language,
        is_adult,
        UNNEST(genre_ids) AS genre_id
    FROM movies
),

joined AS (
    SELECT
        e.movie_id,
        e.title,
        e.release_date,
        e.vote_average,
        e.vote_count,
        e.popularity,
        e.original_language,
        e.is_adult,
        e.genre_id,
        g.genre_name
    FROM exploded e
    LEFT JOIN {{ ref('tmdb_genres') }} g
        ON e.genre_id = g.genre_id
)

SELECT * FROM joined