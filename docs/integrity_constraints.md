# Integrity Constraints

Every constraint enforced by HarmonyVault, grouped by how it is enforced. Serves report §2 (data description) and §8 (integrity constraints).

## 1. Entity integrity (primary keys)

Every relation declares a PRIMARY KEY; no primary-key attribute is NULL. Enforced by the column definitions in `schema/01_create_tables.sql`.

| Relation | Primary key |
| --- | --- |
| Users | userID |
| Clips | clipID |
| MusicalAttributes | clipID |
| Projects | projectID |
| Tags | tagID |
| ClipTags | (clipID, tagID) |
| ProjectClips | (projectID, clipID) |
| ProjectCollaborators | (projectID, userID) |
| ClipVersions | versionID |

## 2. Referential integrity (foreign keys)

All foreign keys are declared with explicit `ON DELETE` / `ON UPDATE` actions:

| Relation.column | References | On delete | On update |
| --- | --- | --- | --- |
| Clips.userID | Users.userID | RESTRICT | CASCADE |
| MusicalAttributes.clipID | Clips.clipID | CASCADE | CASCADE |
| Projects.ownerUserID | Users.userID | RESTRICT | CASCADE |
| Tags.userID | Users.userID | CASCADE | CASCADE |
| ClipTags.clipID | Clips.clipID | CASCADE | CASCADE |
| ClipTags.tagID | Tags.tagID | CASCADE | CASCADE |
| ProjectClips.projectID | Projects.projectID | CASCADE | CASCADE |
| ProjectClips.clipID | Clips.clipID | CASCADE | CASCADE |
| ProjectCollaborators.projectID | Projects.projectID | CASCADE | CASCADE |
| ProjectCollaborators.userID | Users.userID | CASCADE | CASCADE |
| ClipVersions.clipID | Clips.clipID | CASCADE | CASCADE |

`RESTRICT` on `Clips.userID` and `Projects.ownerUserID` prevents deleting a user who still owns data. Every other relationship cascades because the dependent rows are meaningless without the parent.

## 3. Domain constraints (CHECKs)

Enforced inline in `schema/01_create_tables.sql`:

- `Users.email LIKE '%_@_%._%'` — loose sanity check for an `@` and a dot.
- `Clips.duration > 0`.
- `MusicalAttributes.mode IN ('major', 'minor')`.
- `MusicalAttributes.tempo > 0 AND tempo < 400`.
- `MusicalAttributes.musicalKey IN (17 pitch-class values)`.
- `ProjectCollaborators.role IN ('owner', 'editor', 'viewer')`.
- `ClipVersions.versionNumber >= 1`.

## 4. Uniqueness (UNIQUE)

- `Users.username`, `Users.email` — independent uniqueness.
- `Projects(ownerUserID, name)` — a user cannot reuse a project name.
- `Tags(userID, tagName)` — a user cannot create duplicate tags.
- `ClipVersions(clipID, versionNumber)` — version numbers are sequential within a clip.

## 5. Trigger-enforced constraints (semantic, cross-table)

Implemented in `schema/03_triggers.sql`:

1. **Owner is a collaborator.** When a row is inserted into `Projects`, a matching row is inserted into `ProjectCollaborators` with role `owner`. This guarantees that a "list all collaborators" query always returns the owner.
2. **Project-clip access control.** A clip can only be added to a project if the clip's owner is either the project's owner or already a collaborator on that project. Raises `SQLSTATE 45000` otherwise.
3. **Sequential version numbers.** `ClipVersions.versionNumber` is auto-assigned to `MAX(existing) + 1` when the caller leaves it `NULL` or `0`. A caller-supplied value that skips the next-integer is rejected.
4. **Immutable version numbers.** Updating `ClipVersions.versionNumber` is rejected so historical references remain valid.

## 6. Application-layer constraints (enforced in Python)

These are easier (and cheaper) to validate in the CLI and web layers than in SQL, so `cli/` and `web/routes/` perform the check before submitting a query:

- Email format beyond the loose `CHECK` (validated with a real regex in Python).
- File path sanitization for `Clips.filepath` and `ClipVersions.filepath` (absolute vs relative, no `..` traversal).
- Role of the authenticated user is sufficient to perform the requested action on `Projects` and `Clips` (e.g. a `viewer` collaborator cannot add clips).
- Tag names are lowercased and trimmed before insertion so `"Jazz "` and `"jazz"` become the same tag.

## 7. How each constraint maps to the report

Report §2 uses §§1-4 above. Report §8 focuses on §§5-6 and explains the tradeoff: CHECKs are declarative and cheap; triggers are necessary when the rule crosses tables; application-layer validation is used when the rule needs context (e.g. the current user) that the DBMS does not have.
