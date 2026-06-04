-- A clean, typed view of the raw discover endpoint data.
-- Staging models do NO joins and NO business logic — they just clean
-- and rename columns from a single source.

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
)

SELECT * FROM renamed