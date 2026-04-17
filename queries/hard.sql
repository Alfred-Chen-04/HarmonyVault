-- Hard queries (report §6): NOT EXISTS, correlated subqueries, multi-join.
-- Owner: Jacob Liebson (jel212).

-- H1: "orphaned clips" - clips a user owns that are not in any project
--     (the use case from the proposal)
SELECT c.clipID, c.title, u.username
FROM Clips c
JOIN Users u ON u.userID = c.userID
WHERE NOT EXISTS (
    SELECT 1
    FROM ProjectClips pc
    WHERE pc.clipID = c.clipID
);

-- H2: users who have tagged every one of their own clips at least once
SELECT u.username
FROM Users u
WHERE NOT EXISTS (
    SELECT 1
    FROM Clips c
    WHERE c.userID = u.userID
      AND NOT EXISTS (
          SELECT 1
          FROM ClipTags ct
          WHERE ct.clipID = c.clipID
      )
);

-- H3: most recent version of every clip, joined with its musical attributes
--     and owner. Classic "argmax per group" pattern.
SELECT c.clipID, c.title, u.username,
       cv.versionNumber AS latest_version, cv.dateCreated AS version_date,
       ma.musicalKey, ma.mode, ma.tempo
FROM Clips c
JOIN Users u ON u.userID = c.userID
JOIN MusicalAttributes ma ON ma.clipID = c.clipID
JOIN ClipVersions cv ON cv.clipID = c.clipID
WHERE cv.versionNumber = (
    SELECT MAX(v2.versionNumber)
    FROM ClipVersions v2
    WHERE v2.clipID = c.clipID
);
