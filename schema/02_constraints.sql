-- Additional integrity constraints that could not be expressed inline in
-- 01_create_tables.sql because they depend on cross-table state. Enforce
-- through triggers in 03_triggers.sql; this file simply documents them
-- as commented blueprints and provides any extra UNIQUE / CHECK that we
-- want to separate from table creation.
--
-- Owner: Alfred Chen (qxc225)

USE harmonyvault;

-- Enforce: a Projects row's owner must also exist in ProjectCollaborators
-- with role='owner'. This is handled by a trigger in 03_triggers.sql.

-- Enforce: a clip cannot be assigned to a project owned by a different
-- user unless that user is a collaborator on the project. Handled by a
-- trigger in 03_triggers.sql.

-- Enforce: ClipVersions.versionNumber for a given clipID must be the next
-- integer in sequence starting at 1. Handled by a BEFORE INSERT trigger.

-- Reserve a synthetic "system" username so admin queries have a stable
-- owner if needed. Safe to rerun.
INSERT IGNORE INTO Users (userID, username, email, dateCreated)
VALUES (1, 'system', 'system@harmonyvault.local', CURRENT_TIMESTAMP);
