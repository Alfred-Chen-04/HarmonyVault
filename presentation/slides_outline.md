# HarmonyVault — Presentation Slides Outline
# CSDS 341 Spring 2026 | 5-minute slot

---

## Slide 1 — Title

**HarmonyVault**
A Relational Database for Musicians

CSDS 341 · Spring 2026
Jacob Liebson · Sky Zhou · Alfred Chen

*[Speaker note: Introduce the team and the project name. ~15 sec.]*

---

## Slide 2 — The Problem

**Musicians lose ideas.**

- Dozens of short clips per week: melodies, chord progressions, loops
- Files land on disk as `Voice Memo 2024-03-08.m4a` — metadata gone
- Six months later: "that minor-key 72 BPM idea" is unfindable

**A filesystem cannot answer:**
> "All minor-key clips between 90–120 BPM tagged *cinematic* in shared projects"

*[Speaker note: One relatable sentence to hook the audience, then show the query as motivation. ~20 sec.]*

---

## Slide 3 — Our Solution

**HarmonyVault** — a MySQL 8 relational backend for audio-clip metadata

- **9 tables** — clips, users, projects, tags, versions, collaborators
- **Java CLI** — search, create, load data (Jacob)
- **Python data pipeline** — Spotify ingest + Faker synthetic data (Sky)
- **Schema design** — ER, BCNF normalization, triggers, indexes (Alfred)

*[Image: ER diagram — docs/ER_diagram.png]*

*[Speaker note: Show the ER diagram image. Briefly walk the 4 entity clusters: Users/Clips/MusicalAttributes, Projects/ProjectCollaborators, Tags/ClipTags, ClipVersions. ~30 sec.]*

---

## Slide 4 — Schema Design (Alfred)

**9 relations, all in BCNF**

| Entity cluster | Tables |
|---|---|
| Core | Users, Clips, MusicalAttributes |
| Projects | Projects, ProjectCollaborators, ProjectClips |
| Tags | Tags, ClipTags |
| Versions | ClipVersions |

**Key design decisions:**
- Relationship schemas corrected: `Has(clipID, userID)` PK = {clipID} (many-to-one rule)
- M-N with attributes: `ProjectCollaborators` carries `role` and `addedAt`
- Weak entity: `ClipVersions` — partial key `versionNumber` within a clip

*[Speaker note: Mention TA feedback was addressed — no FK attributes in entity boxes. ~30 sec.]*

---

## Slide 5 — Integrity Constraints (Alfred)

**4 enforcement layers**

| Layer | Example |
|---|---|
| PRIMARY KEY | Every table has a surrogate or composite PK |
| CHECK | `mode IN ('major','minor')`, `0 < tempo < 400` |
| Trigger | Project-clip access control; sequential version numbers |
| Application | Role-based write permission; path sanitization |

**Trigger highlight:**
```sql
-- A clip can only be added to a project if the clip's owner
-- is the project owner OR an existing collaborator
BEFORE INSERT ON ProjectClips → SIGNAL SQLSTATE '45000'
```

*[Speaker note: Emphasize that triggers fire even on LOAD DATA INFILE — this is why we chose triggers over application-layer checks for the access control rule. ~35 sec.]*

---

## Slide 6 — Normalization (Alfred)

**BCNF proof in one table**

| Relation | Candidate keys | BCNF? |
|---|---|---|
| Users | {userID}, {username}, {email} | ✓ |
| Projects | {projectID}, {ownerUserID, name} | ✓ |
| ClipVersions | {versionID}, {clipID, versionNumber} | ✓ |
| ClipTags | {clipID, tagID} | ✓ (all-key, vacuous) |
| … | … | All 9 ✓ |

**Why BCNF holds:** every FD's LHS is a candidate key — no partial or transitive dependencies possible.

*[Speaker note: Quick point — the schema was designed rather than decomposed, so lossless join and dependency preservation are trivially satisfied. ~25 sec.]*

---

## Slide 7 — Data Pipeline (Sky)

**Two-stage CSV generation**

```
load_spotify.py      → clips.csv, musical_attributes.csv
                         (Kaggle "Ultimate Spotify Tracks", ~232k rows)

generate_synthetic.py → users.csv, tags.csv, projects.csv,
                         clip_tags.csv, project_clips.csv,
                         project_collaborators.csv, clip_versions.csv
                         (Faker, fixed seed — reproducible)

setup_db.py          → orchestrator, emits all 9 CSVs to data/csv/
```

**Target scale:** ≥ 500 users · ≥ 10,000 clips · ≥ 80 projects

**FK-safe load order** defined in `docs/csv_format.md` — critical because project_collaborators must precede project_clips (trigger dependency).

*[Speaker note: Mention that the golden-sample CSVs in data/csv_sample/ let Jacob test his Java loader early without waiting for the full dataset. ~30 sec.]*

---

## Slide 8 — Queries (Jacob)

**12 queries across 4 difficulty tiers**

| Tier | IDs | Example |
|---|---|---|
| Easy | E1–E3 | Count clips per user; list by signup date |
| Medium | M1–M3 | C-minor 90–120 BPM for a specific user |
| Hard | H1–H3 | Orphaned clips (NOT EXISTS); universal tag check (∀) |
| Admin | A1–A3 | Top-20 tags cross-catalog; tempo histogram |

**E3 in all 3 formalisms:**
```
SQL:  WHERE ma.tempo BETWEEN 90 AND 120
RA:   π_{…} ( σ_{tempo≥90 ∧ tempo≤120} ( Clips ⋈ MusicalAttributes ) )
TRC:  { t | ∃c∈Clips ∃a∈MusicalAttributes ( … ∧ a.tempo≥90 ∧ a.tempo≤120 ) }
```

*[Speaker note: Note that M3 and H3 require the extended RA γ operator — they can't be written in classical RA, which the spec acknowledges. ~30 sec.]*

---

## Slide 9 — Demo

**[Live demo / screenshots here]**

```bash
# Load all 9 CSVs (FK-safe order)
java -jar hv.jar load data/csv/

# Search: C-minor clips at 90–120 BPM
java -jar hv.jar clips search --key C --mode minor \
     --tempo-min 90 --tempo-max 120

# Admin: top 20 tags across catalog
java -jar hv.jar admin top-tags --limit 20
```

*[Speaker note: Walk through at least one search and one admin query live. If demo is not live, show screenshots. ~45 sec.]*

---

## Slide 10 — What We Learned

**Alfred:** Semantic cross-table constraints require triggers — `CHECK` can't access other tables. Tracing cascade-delete order through trigger firing clarified the boundary between schema (domain), trigger (cross-table invariant), and application (session context).

**Sky:** Real-world ingestion is messy. Kaggle Spotify CSV mixes integer key codes with string mode values; normalizing both into our `CHECK` domains needed more translation than expected. Faker's `unique` decorator depletes fast at 500-user scale.

**Jacob:** Not every SQL query has a RA/TRC equivalent. Finding one query that stays within σ/π/⋈ — no aggregation — was a real design constraint, not a textbook exercise.

*[Speaker note: Each member speaks their own bullet (~15 sec each). ~45 sec total.]*

---

## Slide 11 — Summary

- **HarmonyVault** — 9-table BCNF schema, 4 triggers, 12 queries, Java CLI
- Every rubric section addressed: ER, FDs, BCNF, constraints, data, queries (SQL + RA + TRC), per-member technical tracks
- TA proposal feedback fully incorporated: corrected relationship schemas, collaboration use case, admin queries, existing-tool comparison

**GitHub:** [repo URL]

*[Speaker note: End with repo URL or QR code. ~15 sec.]*
