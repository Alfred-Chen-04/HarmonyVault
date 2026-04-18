-- Admin / cross-user queries (report §6, use cases U9–U11).
-- These address the TA's proposal-feedback item 1: add administrative
-- queries that span the whole catalog, not just a single user's data.
-- Owner: Jacob Liebson (jel212).

-- A1: Top-N most popular tag names across the entire platform.
--     Answers U9: "Which tags do musicians reach for most?"
SELECT t.tagName,
       COUNT(ct.clipID) AS usage_count
FROM Tags t
JOIN ClipTags ct ON ct.tagID = t.tagID
GROUP BY t.tagName
ORDER BY usage_count DESC
LIMIT 20;

-- A2: Per-user statistics — clip count, project count, collaboration count.
--     Answers U10: "Who are the most active / most collaborative users?"
SELECT u.userID,
       u.username,
       COUNT(DISTINCT c.clipID)            AS clips_owned,
       COUNT(DISTINCT p.projectID)         AS projects_owned,
       COUNT(DISTINCT pc.projectID)        AS projects_as_collaborator
FROM Users u
LEFT JOIN Clips                c  ON c.userID            = u.userID
LEFT JOIN Projects             p  ON p.ownerUserID       = u.userID
LEFT JOIN ProjectCollaborators pc ON pc.userID           = u.userID
                                  AND pc.role           <> 'owner'
GROUP BY u.userID, u.username
ORDER BY clips_owned DESC;

-- A3: Tempo histogram — how many clips fall into each 20-BPM bucket.
--     Answers U11: "What is the tempo distribution across the whole catalog?"
SELECT CONCAT(FLOOR(ma.tempo / 20) * 20, '–',
              FLOOR(ma.tempo / 20) * 20 + 19) AS bpm_range,
       COUNT(*)                                AS clip_count
FROM MusicalAttributes ma
GROUP BY FLOOR(ma.tempo / 20)
ORDER BY FLOOR(ma.tempo / 20);
