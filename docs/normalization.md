# Normalization Proof

This document proves that every HarmonyVault relation is in Boyce-Codd Normal Form (BCNF), which is strictly stronger than 3NF. It satisfies report §5 (schema in 3NF) and §9 (normalization via functional dependencies).

A relation `R` is in BCNF iff, for every non-trivial FD `X -> Y` in its closure, `X` is a superkey of `R`. The candidate keys and minimal cover of each relation are taken from `functional_dependencies.md`.

## 1. Users(userID, username, email, dateCreated)

- Candidate keys: {userID}, {username}, {email}.
- FDs in minimal cover: `userID -> username`, `userID -> email`, `userID -> dateCreated`.
- Every LHS is `{userID}`, which is a candidate key and therefore a superkey. **BCNF.**

## 2. Clips(clipID, userID, title, duration, filepath, dateCreated)

- Candidate key: {clipID}.
- Only non-trivial FD: `clipID -> userID, title, duration, filepath, dateCreated`.
- LHS is the candidate key, so it is a superkey. **BCNF.**

## 3. MusicalAttributes(clipID, musicalKey, mode, tempo, timeSignature)

- Candidate key: {clipID}.
- Only non-trivial FD: `clipID -> musicalKey, mode, tempo, timeSignature`.
- LHS is the candidate key. **BCNF.**

## 4. Projects(projectID, ownerUserID, name, description, dateCreated)

- Candidate keys: {projectID}, {ownerUserID, name}.
- FDs: `projectID -> ...` (LHS is a candidate key) and `(ownerUserID, name) -> projectID, description, dateCreated` (LHS is a candidate key).
- Both LHSs are superkeys. **BCNF.**

## 5. Tags(tagID, userID, tagName)

- Candidate keys: {tagID}, {userID, tagName}.
- FDs: `tagID -> userID, tagName` and `(userID, tagName) -> tagID`. Both LHSs are candidate keys. **BCNF.**

## 6. ClipTags(clipID, tagID)

- Candidate key: {clipID, tagID} (the full attribute set).
- No non-trivial FDs exist; the only FDs are trivial. **BCNF** vacuously.

## 7. ProjectClips(projectID, clipID)

Same structure as ClipTags. **BCNF** vacuously.

## 8. ProjectCollaborators(projectID, userID, role, addedAt)

- Candidate key: {projectID, userID}.
- Only non-trivial FD: `(projectID, userID) -> role, addedAt`.
- LHS is the candidate key. **BCNF.**

## 9. ClipVersions(versionID, clipID, versionNumber, notes, filepath, dateCreated)

- Candidate keys: {versionID}, {clipID, versionNumber}.
- FDs: `versionID -> ...` and `(clipID, versionNumber) -> versionID, notes, filepath, dateCreated`. Both LHSs are candidate keys. **BCNF.**

---

## Decomposition losslessness and dependency preservation

Because the schema is already in BCNF and was *designed* (not obtained by decomposing a larger universal relation), there is no decomposition to justify. Each entity in the ER diagram maps to exactly one relation, and every many-to-many relationship becomes its own junction table. Lossless join is guaranteed because every pair of relations shares a foreign-key attribute set that is a superkey of at least one side.

Dependency preservation is trivially satisfied since every FD in `F_total` is enforced inside the relation that contains it; no FD was split across relations during design.

---

## Why the proposal's original relationship schemas were incorrect

The TA's proposal feedback (item 5) flagged three relationship schemas that were written with the wrong primary key. The error is structural: the PK of a relationship schema must be determined by the *cardinality* of the relationship, not by naively listing both entity keys. This section first shows the **corrected relationship schemas** in the form the TA asked for, then shows how each one collapses into the final nine-relation design.

### Step 1 — corrected relationship schemas (ER level)

| # | Original relationship | Cardinality | Incorrect proposal form | Corrected form (TA rule) |
| --- | --- | --- | --- | --- |
| 1 | `Has` (Users — Clips) | many-to-one (clips → user) | `Has(userID, clipID)` with PK `{userID, clipID}` | `Has(`**`clipID`**`, userID)` with PK `{clipID}` — the PK comes from the "many" side |
| 2 | `Create` (Users — Projects) | many-to-one (projects → user) | `Create(userID, projectID)` with PK `{userID, projectID}` | `Create(`**`projectID`**`, userID)` with PK `{projectID}` — PK from the "many" side |
| 3 | `To` (Clips — MusicalAttributes) | one-to-one | `To(clipID, attributeID)` with PK `{clipID, attributeID}` | `To(`**`clipID`**`, attributeID)` with PK `{clipID}` — for a 1-1, one side's key is chosen as PK |

In each case the original proposal used a *composite* primary key containing both entity keys. That is wrong for a many-to-one relationship (the PK is the "many" side alone) and redundant for a one-to-one relationship (either side's key is a candidate; only one is promoted to PK).

### Step 2 — collapse each corrected relationship into an entity table

Once the relationship schemas above are correct, each of them has exactly the same candidate key as one of the entities it connects, which means the relationship can be merged into that entity without information loss:

1. `Has(clipID, userID)` with `{clipID}` as PK has the same PK as `Clips`. Adding `userID` as a non-key attribute of `Clips` (renamed `Clips.userID`) preserves every FD and removes the relation entirely.
2. `Create(projectID, userID)` with `{projectID}` as PK has the same PK as `Projects`. Folding `userID` (renamed `Projects.ownerUserID`) into `Projects` preserves every FD and removes the relation.
3. `To(clipID, attributeID)` with `{clipID}` as PK: since the attribute side is entirely functionally dependent on `clipID`, its attributes (`musicalKey`, `mode`, `tempo`, `timeSignature`) become non-key attributes of a relation keyed on `clipID`. This is `MusicalAttributes(clipID, …)` with `clipID` as both PK and FK to `Clips`.

### Step 3 — add the two relations the proposal was missing

The TA also asked for a collaboration use case (item 3) and for the version-history feature mentioned in the proposal to have a backing relation. Two new relations were added:

- `ProjectCollaborators(projectID, userID, role, addedAt)` with PK `{projectID, userID}` — a standard M-N relation with a role attribute.
- `ClipVersions(versionID, clipID, versionNumber, notes, filepath, dateCreated)` — a weak entity of `Clips` with its own surrogate PK and a second candidate key `(clipID, versionNumber)`.

The three corrections plus the two additions together produce the nine-relation BCNF schema proved above.
