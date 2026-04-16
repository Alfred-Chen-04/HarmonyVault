-- Parameterized search used by `python -m cli clips search`.
-- The CLI binds NULL to any filter it did not receive so this single
-- query covers the full combinatorial space.

SELECT c.clipID, c.title, u.username AS owner,
       ma.musicalKey, ma.mode, ma.tempo
FROM Clips c
JOIN Users u ON u.userID = c.userID
JOIN MusicalAttributes ma ON ma.clipID = c.clipID
WHERE (%(key)s  IS NULL OR ma.musicalKey = %(key)s)
  AND (%(mode)s IS NULL OR ma.mode       = %(mode)s)
  AND ma.tempo BETWEEN %(tempo_min)s AND %(tempo_max)s
ORDER BY ma.tempo
LIMIT %(limit)s
