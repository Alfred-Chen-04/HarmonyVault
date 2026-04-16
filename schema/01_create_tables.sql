-- HarmonyVault schema (MySQL 8.x)
-- Owner: Alfred Chen (qxc225)
--
-- Nine relations implementing the corrected design after TA proposal feedback:
--   * The many-to-one "Has" relationship between Users and Clips is folded into
--     Clips via Clips.userID (the feedback said a separate Has(clipID, userID)
--     must have clipID as sole PK, which is equivalent to merging).
--   * The many-to-one "Create" relationship between Users and Projects is
--     folded into Projects via Projects.ownerUserID for the same reason.
--   * The one-to-one "To" relationship between Clips and MusicalAttributes is
--     collapsed: MusicalAttributes keeps clipID as its primary key and foreign
--     key, so there is no separate join relation.
--   * ProjectCollaborators is added to support the "collaboration" use case
--     that the TA asked us to cover.
--   * ClipVersions is added to fulfill the "version history" feature from the
--     proposal that was missing a relation.
--
-- Character set / engine choices
--   InnoDB is required for foreign-key enforcement and is the MySQL 8 default.
--   utf8mb4 covers emoji and non-Latin characters in titles and tag names.

CREATE DATABASE IF NOT EXISTS harmonyvault
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE harmonyvault;

-- Drop in reverse dependency order so re-runs work.
DROP TABLE IF EXISTS ClipVersions;
DROP TABLE IF EXISTS ProjectCollaborators;
DROP TABLE IF EXISTS ProjectClips;
DROP TABLE IF EXISTS ClipTags;
DROP TABLE IF EXISTS Tags;
DROP TABLE IF EXISTS Projects;
DROP TABLE IF EXISTS MusicalAttributes;
DROP TABLE IF EXISTS Clips;
DROP TABLE IF EXISTS Users;

-- -------------------------------------------------------------------
-- Users: application accounts.
-- -------------------------------------------------------------------
CREATE TABLE Users (
    userID        INT            NOT NULL AUTO_INCREMENT,
    username      VARCHAR(64)    NOT NULL,
    email         VARCHAR(255)   NOT NULL,
    dateCreated   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (userID),
    UNIQUE KEY uk_users_username (username),
    UNIQUE KEY uk_users_email    (email),
    CONSTRAINT ck_users_email_format CHECK (email LIKE '%_@_%._%')
) ENGINE=InnoDB;

-- -------------------------------------------------------------------
-- Clips: one row per audio idea owned by exactly one user.
-- The userID FK replaces the old Has(userID, clipID) relation.
-- -------------------------------------------------------------------
CREATE TABLE Clips (
    clipID        INT            NOT NULL AUTO_INCREMENT,
    userID        INT            NOT NULL,
    title         VARCHAR(255)   NOT NULL,
    duration      DECIMAL(8,2)   NOT NULL COMMENT 'seconds',
    filepath      VARCHAR(512)   NOT NULL,
    dateCreated   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (clipID),
    CONSTRAINT fk_clips_user
        FOREIGN KEY (userID) REFERENCES Users(userID)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT ck_clips_duration_positive CHECK (duration > 0)
) ENGINE=InnoDB;

-- -------------------------------------------------------------------
-- MusicalAttributes: one row per clip (1-1). PK = clipID, so the
-- former "To" relation collapses into this table entirely.
-- -------------------------------------------------------------------
CREATE TABLE MusicalAttributes (
    clipID         INT          NOT NULL,
    musicalKey     VARCHAR(3)   NOT NULL COMMENT 'Pitch class: C, C#, Db, ...',
    mode           VARCHAR(8)   NOT NULL COMMENT 'major or minor',
    tempo          DECIMAL(6,2) NOT NULL COMMENT 'BPM',
    timeSignature  VARCHAR(8)   NOT NULL DEFAULT '4/4',
    PRIMARY KEY (clipID),
    CONSTRAINT fk_ma_clip
        FOREIGN KEY (clipID) REFERENCES Clips(clipID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT ck_ma_mode  CHECK (mode IN ('major', 'minor')),
    CONSTRAINT ck_ma_tempo CHECK (tempo > 0 AND tempo < 400),
    CONSTRAINT ck_ma_key   CHECK (musicalKey IN
        ('C','C#','Db','D','D#','Eb','E','F','F#','Gb',
         'G','G#','Ab','A','A#','Bb','B'))
) ENGINE=InnoDB;

-- -------------------------------------------------------------------
-- Projects: a named collection of clips owned by one user.
-- ownerUserID FK replaces the old Create(userID, projectID) relation.
-- -------------------------------------------------------------------
CREATE TABLE Projects (
    projectID     INT            NOT NULL AUTO_INCREMENT,
    ownerUserID   INT            NOT NULL,
    name          VARCHAR(255)   NOT NULL,
    description   TEXT           NULL,
    dateCreated   DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (projectID),
    CONSTRAINT fk_projects_owner
        FOREIGN KEY (ownerUserID) REFERENCES Users(userID)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY uk_projects_owner_name (ownerUserID, name)
) ENGINE=InnoDB;

-- -------------------------------------------------------------------
-- Tags: each user maintains their own tag vocabulary.
-- -------------------------------------------------------------------
CREATE TABLE Tags (
    tagID      INT         NOT NULL AUTO_INCREMENT,
    userID     INT         NOT NULL,
    tagName    VARCHAR(64) NOT NULL,
    PRIMARY KEY (tagID),
    CONSTRAINT fk_tags_user
        FOREIGN KEY (userID) REFERENCES Users(userID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY uk_tags_owner_name (userID, tagName)
) ENGINE=InnoDB;

-- -------------------------------------------------------------------
-- ClipTags: M-N between Clips and Tags.
-- -------------------------------------------------------------------
CREATE TABLE ClipTags (
    clipID  INT NOT NULL,
    tagID   INT NOT NULL,
    PRIMARY KEY (clipID, tagID),
    CONSTRAINT fk_ct_clip
        FOREIGN KEY (clipID) REFERENCES Clips(clipID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ct_tag
        FOREIGN KEY (tagID) REFERENCES Tags(tagID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -------------------------------------------------------------------
-- ProjectClips: M-N between Projects and Clips.
-- -------------------------------------------------------------------
CREATE TABLE ProjectClips (
    projectID INT NOT NULL,
    clipID    INT NOT NULL,
    PRIMARY KEY (projectID, clipID),
    CONSTRAINT fk_pc_project
        FOREIGN KEY (projectID) REFERENCES Projects(projectID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_pc_clip
        FOREIGN KEY (clipID)    REFERENCES Clips(clipID)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB;

-- -------------------------------------------------------------------
-- ProjectCollaborators: adds the collaboration use case requested in
-- the TA's proposal feedback. A user can hold one role per project.
-- -------------------------------------------------------------------
CREATE TABLE ProjectCollaborators (
    projectID INT          NOT NULL,
    userID    INT          NOT NULL,
    role      VARCHAR(16)  NOT NULL,
    addedAt   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (projectID, userID),
    CONSTRAINT fk_col_project
        FOREIGN KEY (projectID) REFERENCES Projects(projectID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_col_user
        FOREIGN KEY (userID) REFERENCES Users(userID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT ck_col_role CHECK (role IN ('owner', 'editor', 'viewer'))
) ENGINE=InnoDB;

-- -------------------------------------------------------------------
-- ClipVersions: the "version history" feature the proposal mentions.
-- Each clip can have multiple versions, each with its own audio file.
-- -------------------------------------------------------------------
CREATE TABLE ClipVersions (
    versionID     INT          NOT NULL AUTO_INCREMENT,
    clipID        INT          NOT NULL,
    versionNumber INT          NOT NULL,
    notes         TEXT         NULL,
    filepath      VARCHAR(512) NOT NULL,
    dateCreated   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (versionID),
    CONSTRAINT fk_ver_clip
        FOREIGN KEY (clipID) REFERENCES Clips(clipID)
        ON DELETE CASCADE ON UPDATE CASCADE,
    UNIQUE KEY uk_ver_clip_number (clipID, versionNumber),
    CONSTRAINT ck_ver_number_positive CHECK (versionNumber >= 1)
) ENGINE=InnoDB;
