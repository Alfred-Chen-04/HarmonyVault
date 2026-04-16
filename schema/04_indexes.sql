-- Non-PK indexes to speed up the queries in queries/*.sql.
-- Owner: Alfred Chen (qxc225)

USE harmonyvault;

-- Search clips by musical key + tempo range: the canonical workload.
CREATE INDEX idx_ma_key_tempo ON MusicalAttributes (musicalKey, tempo);

-- Search clips by mode alone (e.g. "all minor clips").
CREATE INDEX idx_ma_mode ON MusicalAttributes (mode);

-- List a user's clips quickly (the CLI's most common SELECT).
CREATE INDEX idx_clips_user_date ON Clips (userID, dateCreated);

-- Tag lookups by name (tag autocomplete, cross-user tag popularity).
CREATE INDEX idx_tags_name ON Tags (tagName);

-- Reverse lookup: "which projects contain this clip?"
CREATE INDEX idx_project_clips_clip ON ProjectClips (clipID);

-- Reverse lookup: "which clips carry this tag?"
CREATE INDEX idx_clip_tags_tag ON ClipTags (tagID);

-- Collaborator lookups for access checks in triggers / queries.
CREATE INDEX idx_collab_user ON ProjectCollaborators (userID);

-- Latest-version-of-clip queries.
CREATE INDEX idx_versions_clip_num ON ClipVersions (clipID, versionNumber DESC);
