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

## Why the proposal's original schema was not yet in 3NF

The proposal (before TA feedback) included three relationship relations that violated the 3NF definition of relationship-schema primary keys:

1. `Has(clipID, userID)` with composite PK. Because `clipID -> userID` holds (a clip has exactly one owner), `{userID}` is not a candidate key of Has but appears as a non-prime determinant of itself — trivial — while the composite PK was larger than necessary. Folding `userID` into `Clips` removes the relation entirely and satisfies BCNF.
2. `Create(userID, projectID)` had the same structural problem and was folded into `Projects.ownerUserID` for the same reason.
3. `To(clipID, attributeID)` held `clipID -> attributeID` and `attributeID -> clipID` because the relationship is 1-1, making each of `{clipID}` and `{attributeID}` a candidate key. Keeping both as the PK inflated the key unnecessarily. Collapsing `MusicalAttributes` to use `clipID` as both PK and FK yields BCNF with a single candidate key.

These three corrections — together with adding `ProjectCollaborators` and `ClipVersions` — are exactly the changes that produce the nine-relation schema above.
