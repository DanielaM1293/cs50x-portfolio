-- 12. Titles of all of movies in which both Jennifer Lawrence and Bradley Cooper starred
SELECT title FROM movies
JOIN stars ON movies.id = stars.movie_id
JOIN people ON stars.person_id = people.id
WHERE people.name = 'Johnny Depp'
AND movies.id IN (
    SELECT movie_id FROM stars
    JOIN people ON stars.person_id = people.id
    WHERE people.name = 'Helena Bonham Carter'
);
