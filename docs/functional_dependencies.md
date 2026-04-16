# Functional Dependencies

This document enumerates the functional dependencies (FDs) that hold over the HarmonyVault relations and derives a minimal cover for each relation. It supports report §4 (functional dependencies) and §9 (normalization).

## Notation

Relations are written with their full attribute list followed by the FD set `F`. Primary keys are underlined in text as `[attr]`. All FDs are semantic: they follow from the meaning of the application, not from a particular instance.

---

## 1. Users(userID, username, email, dateCreated)

```
F_Users = {
    userID     -> username, email, dateCreated,
    username   -> userID, email, dateCreated,
    email      -> userID, username, dateCreated
}
```

All three of `userID`, `username`, and `email` are candidate keys because `UNIQUE` constraints guarantee each identifies a single row. The minimal cover collapses to the single generator `userID` since the `UNIQUE` constraints on `username` and `email` are enforced by indices, not additional FDs for normalization purposes. For the BCNF proof we keep all three candidate keys.

Minimal cover: `{ userID -> username, userID -> email, userID -> dateCreated }`.

---

## 2. Clips(clipID, userID, title, duration, filepath, dateCreated)

```
F_Clips = {
    clipID -> userID, title, duration, filepath, dateCreated
}
```

`clipID` is the only candidate key. `userID` is a foreign key, not a determinant of any other Clips attribute (different users can give their clips the same title). `filepath` is not guaranteed unique in practice because two versions can point at different files with the same name in different folders; we therefore do not record `filepath -> clipID`.

Minimal cover is already in minimal form: one FD, LHS singleton, each RHS attribute non-redundant.

---

## 3. MusicalAttributes(clipID, musicalKey, mode, tempo, timeSignature)

```
F_MA = {
    clipID -> musicalKey, mode, tempo, timeSignature
}
```

Because a clip has exactly one set of musical attributes and the table is keyed on `clipID`, this is the only FD. Minimal cover is the FD itself.

---

## 4. Projects(projectID, ownerUserID, name, description, dateCreated)

```
F_Projects = {
    projectID            -> ownerUserID, name, description, dateCreated,
    ownerUserID, name    -> projectID, description, dateCreated
}
```

The second FD follows from the `UNIQUE(ownerUserID, name)` constraint: a given owner cannot reuse the same project name, so `(ownerUserID, name)` is a second candidate key.

Minimal cover:
```
projectID           -> ownerUserID, name, description, dateCreated
ownerUserID, name   -> projectID
```

---

## 5. Tags(tagID, userID, tagName)

```
F_Tags = {
    tagID            -> userID, tagName,
    userID, tagName  -> tagID
}
```

Two candidate keys: `tagID` (surrogate) and `(userID, tagName)` (business key enforced by `UNIQUE`). Minimal cover keeps both since neither is derivable from the other.

---

## 6. ClipTags(clipID, tagID)

```
F_CT = { }   -- no non-trivial FDs; the full attribute set is the key
```

ClipTags is all-key. Every FD that holds is trivial.

---

## 7. ProjectClips(projectID, clipID)

```
F_PC = { }   -- all-key relation
```

Same reasoning as ClipTags.

---

## 8. ProjectCollaborators(projectID, userID, role, addedAt)

```
F_PCol = {
    projectID, userID -> role, addedAt
}
```

Role and addedAt are per-membership attributes. `(projectID, userID)` is the only candidate key. Different collaborators on the same project can hold the same role, and the same user can be a collaborator on many projects with different roles, so there is no simpler determinant.

---

## 9. ClipVersions(versionID, clipID, versionNumber, notes, filepath, dateCreated)

```
F_CV = {
    versionID             -> clipID, versionNumber, notes, filepath, dateCreated,
    clipID, versionNumber -> versionID, notes, filepath, dateCreated
}
```

Two candidate keys: `versionID` (surrogate) and `(clipID, versionNumber)` (enforced by `UNIQUE`).

Minimal cover:
```
versionID              -> clipID, versionNumber, notes, filepath, dateCreated
clipID, versionNumber  -> versionID
```

---

## Summary of candidate keys

| Relation | Candidate keys |
| --- | --- |
| Users | {userID}, {username}, {email} |
| Clips | {clipID} |
| MusicalAttributes | {clipID} |
| Projects | {projectID}, {ownerUserID, name} |
| Tags | {tagID}, {userID, tagName} |
| ClipTags | {clipID, tagID} |
| ProjectClips | {projectID, clipID} |
| ProjectCollaborators | {projectID, userID} |
| ClipVersions | {versionID}, {clipID, versionNumber} |

Because every FD above has a candidate key on the left-hand side, every relation is in BCNF; the proof is given in `normalization.md`.
