-- A clean, typed view of the raw discover endpoint data.
-- Staging models do NO joins and NO business logic — they just clean,
-- rename, and de-duplicate from a single source.
--
-- De-dupe note: TMDB's paginated discover endpoint occasionally returns the
-- same movie on multiple pages (observed on 8 of ~10,000 movies in our 2024
-- backfill, all with identical attributes). We pick one row per movie_id
-- using the lowest source-file path as a deterministic tiebreaker.
-- See ADR-0002 for details.

WITH source AS (
    SELECT * FROM {{ source('raw', 'raw_movies_discover') }}
),

renamed AS (
    SELECT
        -- Identifiers
        id AS movie_id,

        -- Descriptive fields
        title,
        original_title,
        overview,
        original_language,

        -- Metrics
        vote_average,
        vote_count,
        popularity,

        -- Dates
        release_date,

        -- Flags
        adult AS is_adult,
        video AS is_video,

        -- Arrays (kept as-is; we'll unnest in a downstream model)
        genre_ids,

        -- Lineage
        filename AS _source_file
    FROM source
),

deduplicated AS (
    SELECT
        *,
        ROW_NUMBER() OVER (
            PARTITION BY movie_id
            ORDER BY _source_file
        ) AS _row_num
    FROM renamed
)

SELECT
    movie_id,
    title,
    original_title,
    overview,
    original_language,
    vote_average,
    vote_count,
    popularity,
    release_date,
    is_adult,
    is_video,
    genre_ids,
    _source_file
FROM deduplicated
WHERE _row_num = 1