-- Top genres of 2024 by user engagement.
--
-- "Engagement" here = total vote_count across all movies in the genre.
-- Filter: vote_count >= 50 per movie to exclude near-zero-data entries
-- whose ratings would be unreliable.
--
-- One row per genre, ordered by total engagement.

WITH credible_movies AS (
    SELECT *
    FROM {{ ref('int_movies_genres') }}
    WHERE vote_count >= 50
        AND genre_name IS NOT NULL
        AND NOT is_adult
),

genre_stats AS (
    SELECT
        genre_name,
        COUNT(DISTINCT movie_id) AS movies_in_genre,
        SUM(vote_count) AS total_votes,
        ROUND(AVG(vote_average), 2) AS avg_rating,
        ROUND(AVG(popularity), 2) AS avg_popularity
    FROM credible_movies
    GROUP BY genre_name
)

SELECT
    genre_name,
    movies_in_genre,
    total_votes,
    avg_rating,
    avg_popularity
FROM genre_stats
ORDER BY total_votes DESC