-- Stored procedures for HarmonyVault (MySQL 8.x)
-- Owner: Jacob Liebson (jel212)
--
-- Three procedures covering the three most common multi-step operations:
--
--   1. add_clip_with_tags   — atomically insert a clip, its musical
--                             attributes, and zero or more tags.
--   2. add_clip_version     — append the next version of an existing clip;
--                             versionNumber is assigned automatically by the
--                             trg_clip_versions_before_insert_seq trigger.
--   3. add_collaborator     — grant a user access to a project, or update
--                             their role if they are already a collaborator.
--
-- All three wrap their writes in an explicit transaction so that a failure
-- at any step leaves the database unchanged. The Java CLI calls them via
-- CallableStatement with the OUT parameters registered before execution.
--
-- Usage (MySQL CLI):
--   SOURCE queries/stored_procedures.sql;
--   CALL add_clip_with_tags(1, 'Bridge idea', 32.5, '/audio/bridge.wav',
--                           'G', 'major', 120.0, '4/4', 'guitar,ambient',
--                           @id);
--   SELECT @id;

USE harmonyvault;

DROP PROCEDURE IF EXISTS add_clip_with_tags;
DROP PROCEDURE IF EXISTS add_clip_version;
DROP PROCEDURE IF EXISTS add_collaborator;

DELIMITER //

-- -----------------------------------------------------------------------
-- add_clip_with_tags
--
-- Inserts one Clip row, one MusicalAttributes row, and ClipTags rows for
-- every comma-separated tag name in p_tag_csv. Tags that do not yet exist
-- in the caller's tag vocabulary are created automatically. Empty p_tag_csv
-- (or NULL) skips tag insertion entirely.
--
-- Parameters
--   p_userID        — owner of the new clip (must exist in Users)
--   p_title         — clip title
--   p_duration      — duration in seconds (must be > 0)
--   p_filepath      — path to the audio file
--   p_musicalKey    — pitch class, e.g. 'C', 'F#', 'Bb'
--   p_mode          — 'major' or 'minor'
--   p_tempo         — BPM (0 < tempo < 400)
--   p_timeSignature — e.g. '4/4', '3/4'  (default '4/4' if NULL)
--   p_tag_csv       — comma-separated tag names, e.g. 'guitar,ambient,loop'
--   p_clipID  OUT   — the AUTO_INCREMENT ID assigned to the new clip
-- -----------------------------------------------------------------------
CREATE PROCEDURE add_clip_with_tags(
    IN  p_userID        INT,
    IN  p_title         VARCHAR(255),
    IN  p_duration      DECIMAL(8,2),
    IN  p_filepath      VARCHAR(512),
    IN  p_musicalKey    VARCHAR(3),
    IN  p_mode          VARCHAR(8),
    IN  p_tempo         DECIMAL(6,2),
    IN  p_timeSignature VARCHAR(8),
    IN  p_tag_csv       TEXT,
    OUT p_clipID        INT
)
BEGIN
    DECLARE v_tagID    INT;
    DECLARE v_tagName  VARCHAR(64);
    DECLARE v_rest     TEXT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- Default time signature when caller omits it
    IF p_timeSignature IS NULL OR CHAR_LENGTH(TRIM(p_timeSignature)) = 0 THEN
        SET p_timeSignature = '4/4';
    END IF;

    INSERT INTO Clips (userID, title, duration, filepath)
    VALUES (p_userID, p_title, p_duration, p_filepath);

    SET p_clipID = LAST_INSERT_ID();

    INSERT INTO MusicalAttributes (clipID, musicalKey, mode, tempo, timeSignature)
    VALUES (p_clipID, p_musicalKey, p_mode, p_tempo, p_timeSignature);

    -- Walk the comma-separated tag list
    IF p_tag_csv IS NOT NULL AND CHAR_LENGTH(TRIM(p_tag_csv)) > 0 THEN
        SET v_rest = TRIM(p_tag_csv);

        WHILE CHAR_LENGTH(v_rest) > 0 DO
            IF LOCATE(',', v_rest) > 0 THEN
                SET v_tagName = TRIM(SUBSTRING_INDEX(v_rest, ',', 1));
                SET v_rest    = TRIM(SUBSTRING(v_rest, LOCATE(',', v_rest) + 1));
            ELSE
                SET v_tagName = TRIM(v_rest);
                SET v_rest    = '';
            END IF;

            IF CHAR_LENGTH(v_tagName) > 0 THEN
                -- Create the tag if it does not exist for this user
                INSERT IGNORE INTO Tags (userID, tagName)
                VALUES (p_userID, v_tagName);

                SELECT tagID INTO v_tagID
                FROM Tags
                WHERE userID = p_userID AND tagName = v_tagName;

                INSERT IGNORE INTO ClipTags (clipID, tagID)
                VALUES (p_clipID, v_tagID);
            END IF;
        END WHILE;
    END IF;

    COMMIT;
END //

-- -----------------------------------------------------------------------
-- add_clip_version
--
-- Appends a new ClipVersions row for an existing clip. The version number
-- is determined automatically by the trg_clip_versions_before_insert_seq
-- trigger (caller passes 0 and the trigger assigns MAX + 1). This procedure
-- exists so the Java CLI can call a single stored procedure instead of
-- manually computing the next version number.
--
-- Parameters
--   p_clipID      — the clip being versioned (must exist in Clips)
--   p_filepath    — path to the new audio file for this version
--   p_notes       — optional change notes (NULL is fine)
--   p_versionID OUT — the AUTO_INCREMENT ID of the new ClipVersions row
-- -----------------------------------------------------------------------
CREATE PROCEDURE add_clip_version(
    IN  p_clipID     INT,
    IN  p_filepath   VARCHAR(512),
    IN  p_notes      TEXT,
    OUT p_versionID  INT
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    -- versionNumber = 0 tells the trigger to auto-assign the next value
    INSERT INTO ClipVersions (clipID, versionNumber, notes, filepath)
    VALUES (p_clipID, 0, p_notes, p_filepath);

    SET p_versionID = LAST_INSERT_ID();

    COMMIT;
END //

-- -----------------------------------------------------------------------
-- add_collaborator
--
-- Grants p_userID access to p_projectID with the given role, or updates
-- their existing role if they are already listed as a collaborator. The
-- project owner's role (inserted automatically by the
-- trg_projects_after_insert_owner_collab trigger) can be updated here too
-- if the caller explicitly passes role='owner', but the typical use case
-- is granting 'editor' or 'viewer' access to a non-owner.
--
-- Parameters
--   p_projectID — target project (must exist in Projects)
--   p_userID    — user to add or update (must exist in Users)
--   p_role      — 'owner', 'editor', or 'viewer'
-- -----------------------------------------------------------------------
CREATE PROCEDURE add_collaborator(
    IN p_projectID INT,
    IN p_userID    INT,
    IN p_role      VARCHAR(16)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;

    START TRANSACTION;

    INSERT INTO ProjectCollaborators (projectID, userID, role)
    VALUES (p_projectID, p_userID, p_role)
    ON DUPLICATE KEY UPDATE role = VALUES(role);

    COMMIT;
END //

DELIMITER ;
