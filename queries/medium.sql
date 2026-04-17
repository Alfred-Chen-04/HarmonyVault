-- Medium queries (report §6): joins, aggregation, subqueries.
-- Owner: Jacob Liebson (jel212).

-- M1: clips in C minor with tempo between 90 and 120 BPM owned by a named user
SELECT c.clipID, c.title, ma.tempo
FROM Clips c
JOIN Users u ON u.userID = c.userID
JOIN MusicalAttributes ma ON ma.clipID = c.clipID
WHERE u.username  = 'alfred'
  AND ma.musicalKey = 'C'
  AND ma.mode       = 'minor'
  AND ma.tempo BETWEEN 90 AND 120;

-- M2: per project, count distinct owners of the clips inside it
--     (shows collaboration health)
SELECT p.projectID, p.name,
       COUNT(DISTINCT c.userID) AS distinct_clip_owners
FROM Projects p
JOIN ProjectClips pc ON pc.projectID = p.projectID
JOIN Clips        c  ON c.clipID   = pc.clipID
GROUP BY p.projectID, p.name
HAVING distinct_clip_owners > 1;

-- M3: users whose average clip tempo exceeds the overall average
SELECT u.username, AVG(ma.tempo) AS avg_tempo
FROM Users u
JOIN Clips c ON c.userID = u.userID
JOIN MusicalAttributes ma ON ma.clipID = c.clipID
GROUP BY u.username
HAVING AVG(ma.tempo) > (SELECT AVG(tempo) FROM MusicalAttributes)
ORDER BY avg_tempo DESC;
