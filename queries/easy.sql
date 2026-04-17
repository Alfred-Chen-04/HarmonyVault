-- Easy queries (report §6). Each block = one query the CLI/Web UI can run.
-- Owner: Jacob Liebson (jel212).

-- E1: list every registered user ordered by signup date
SELECT userID, username, email, dateCreated
FROM Users
ORDER BY dateCreated ASC;

-- E2: count how many clips each user owns
SELECT u.username, COUNT(c.clipID) AS clip_count
FROM Users u
LEFT JOIN Clips c ON c.userID = u.userID
GROUP BY u.username
ORDER BY clip_count DESC;

-- E3: find every clip whose tempo lies in [90, 120] BPM
SELECT c.clipID, c.title, ma.musicalKey, ma.mode, ma.tempo
FROM Clips c
JOIN MusicalAttributes ma ON ma.clipID = c.clipID
WHERE ma.tempo BETWEEN 90 AND 120
ORDER BY ma.tempo;
