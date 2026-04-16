-- Triggers that enforce cross-table integrity constraints that cannot be
-- written as simple CHECK expressions. Report §8 cites each one.
-- Owner: Alfred Chen (qxc225)

USE harmonyvault;

DROP TRIGGER IF EXISTS trg_projects_after_insert_owner_collab;
DROP TRIGGER IF EXISTS trg_project_clips_before_insert_access;
DROP TRIGGER IF EXISTS trg_clip_versions_before_insert_seq;
DROP TRIGGER IF EXISTS trg_clip_versions_before_update_immutable_number;

DELIMITER //

-- When a Project is created, automatically record its owner as a
-- collaborator with role='owner'. Keeps the collaborator roster complete
-- so "list everyone who can edit this project" is a single query.
CREATE TRIGGER trg_projects_after_insert_owner_collab
AFTER INSERT ON Projects
FOR EACH ROW
BEGIN
    INSERT IGNORE INTO ProjectCollaborators (projectID, userID, role, addedAt)
    VALUES (NEW.projectID, NEW.ownerUserID, 'owner', CURRENT_TIMESTAMP);
END //

-- A clip may only be added to a project if the clip's owner is either
-- the project's owner or a collaborator on that project. This prevents
-- a user from attaching someone else's clip to their project unless
-- they have been granted access.
CREATE TRIGGER trg_project_clips_before_insert_access
BEFORE INSERT ON ProjectClips
FOR EACH ROW
BEGIN
    DECLARE v_clip_owner INT;
    DECLARE v_project_owner INT;
    DECLARE v_is_collab INT;

    SELECT userID INTO v_clip_owner FROM Clips WHERE clipID = NEW.clipID;
    SELECT ownerUserID INTO v_project_owner FROM Projects
        WHERE projectID = NEW.projectID;

    IF v_clip_owner <> v_project_owner THEN
        SELECT COUNT(*) INTO v_is_collab
        FROM ProjectCollaborators
        WHERE projectID = NEW.projectID
          AND userID    = v_clip_owner;

        IF v_is_collab = 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT =
                'Clip owner is not a collaborator on the target project.';
        END IF;
    END IF;
END //

-- ClipVersions.versionNumber must be the next integer in sequence for
-- each clipID starting at 1. We compute it automatically if the caller
-- passes 0 or NULL; otherwise we validate.
CREATE TRIGGER trg_clip_versions_before_insert_seq
BEFORE INSERT ON ClipVersions
FOR EACH ROW
BEGIN
    DECLARE v_next INT;
    SELECT COALESCE(MAX(versionNumber), 0) + 1 INTO v_next
    FROM ClipVersions WHERE clipID = NEW.clipID;

    IF NEW.versionNumber IS NULL OR NEW.versionNumber = 0 THEN
        SET NEW.versionNumber = v_next;
    ELSEIF NEW.versionNumber <> v_next THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT =
            'ClipVersions.versionNumber must be the next sequential value.';
    END IF;
END //

-- Prevent renumbering an existing version; versionNumber is immutable
-- once assigned so history stays consistent.
CREATE TRIGGER trg_clip_versions_before_update_immutable_number
BEFORE UPDATE ON ClipVersions
FOR EACH ROW
BEGIN
    IF NEW.versionNumber <> OLD.versionNumber THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'ClipVersions.versionNumber is immutable.';
    END IF;
END //

DELIMITER ;
