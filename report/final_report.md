# HarmonyVault — Final Report

**Course**: CSDS 341 Introduction to Database Systems, Spring 2026
**Team**: Jacob Liebson (jel212), Sky Zhou (sxz903), Alfred Chen (qxc225)
**Report length target**: ≤ 15 pages (per spec).
**Submission**: single zip to Canvas, 2026-05-01 23:59.

> Writing guidance: every section below corresponds to a rubric item in the project specification. Keep each section tight; do not exceed the 15-page cap. Screenshots, query outputs, and the ER diagram go in `report/assets/` and are embedded here by reference.

---

## 1. Application Background

*Rubric §a.* Motivation, problem statement, existing solutions, and comparison to HarmonyVault.

- The problem: musicians accumulate short audio clips whose metadata (key, tempo, mode, time signature) cannot be searched through ordinary filesystems.
- Existing solutions to cover for the TA's feedback:
  - **Splice** (<https://splice.com>) — cloud loop marketplace + DAW plugin; search by key and tempo but not a user-owned relational store.
  - **Loopcloud** (<https://www.loopcloud.com>) — similar, with a local caching client.
  - **Ableton Live's Browser** and **Native Instruments Maschine** — in-DAW organization limited to one workstation, not queryable from outside.
  - **iTunes / Apple Music libraries** — keyed on finished songs, not raw clips; no project/tag model.
- HarmonyVault differs in that it is (a) user-owned, (b) fully relational, (c) query-first (not playback-first), and (d) shareable across collaborators without a DAW license.

## 2. Data Description and Constraints

*Rubric §b.* Pull from `docs/integrity_constraints.md`: primary keys, foreign keys, CHECKs, UNIQUEs, the four trigger-enforced rules, and the application-layer validations.

## 3. ER Diagram

*Rubric §c.* Embed `docs/ER_diagram.png`. Caption should note the three fixes from TA feedback: no FKs inside entity boxes, `role`/`addedAt` on the `Collaborates` relationship, and `MusicalAttributes` and `ClipVersion` as weak entities with double borders.

## 4. Functional Dependencies

*Rubric §d.* Reproduce the FD listing from `docs/functional_dependencies.md`; point out which relations have more than one candidate key.

## 5. Schema in 3NF / BCNF

*Rubric §e.* Copy the nine `CREATE TABLE` statements from `schema/01_create_tables.sql`; reproduce the per-relation BCNF proof from `docs/normalization.md`; explicitly note that every relation is in BCNF (strictly stronger than 3NF).

## 6. Example Queries

*Rubric §f.* Table of nine queries (E1-E3, M1-M3, H1-H3) with English description (`queries/explanations.md`). Then show E3 in SQL **and** RA **and** TRC from `queries/ra_trc.md`. Include screenshots of representative query outputs from the running CLI.

## 7. Implementation

*Rubric §g.* OS (macOS, Linux), DBMS (MySQL 8.x), language (Python 3.11, click, Flask, pandas, Faker). Note row counts after `setup_db.py`: expected ≥ 10,000 clips + 10,000 attribute rows from Spotify, plus synthetic users/tags/projects/collaborators.

## 8. Integrity Constraints in Practice

*Rubric §8 of the extended outline.* Reproduce §5 of `docs/integrity_constraints.md`: trigger-enforced rules and the rationale for splitting enforcement between CHECKs, triggers, and the application layer.

## 9. Per-Member Contributions

*Rubric §h.* Copy the three "Standalone: yes" sections from `docs/work_division.md`. Then each member writes a one-paragraph "what I learned" block (see §10 below).

## 10. What We Learned

*Rubric §i.* One paragraph per team member covering a concept not on the lecture slides:

- **Alfred**: trigger-driven semantic constraints (e.g. access control via `ProjectCollaborators`) and how they interact with cascade deletes.
- **Jacob**: real-world data ingestion — dealing with messy CSV column encodings, key-integer ↔ name translation, and balancing synthetic data with Faker's uniqueness quirks.
- **Sky**: expressing the same information need in SQL vs RA vs TRC, and the formal reason some SQL queries cannot be written in classical RA.

## 11. Conclusions

Short section summarizing what works, the scale achieved, and what we would do differently with more time (e.g. full-text search on titles, audio similarity indexing, cloud deployment).

---

## Appendix 1 — Installation Manual

Mirror of `README.md` with slightly more hand-holding for a TA who has never used Docker.

## Appendix 2 — User Manual

Walk-through screenshots of:

1. `python -m cli clips search --key C --mode minor --tempo-min 90 --tempo-max 120`
2. `python -m cli projects create ...`
3. Browsing `/clips`, `/projects`, `/search` in the web UI.

## Appendix 3 — Programmer Manual

- Module map: `cli/`, `scripts/`, `web/`, `schema/`, `queries/`.
- Public function signatures from `cli/db.py` (`connect`, `load_query`, `run_query`, `run_named`, `run_mutation`).
- Convention: every new SQL file lives in `queries/`, every schema change goes in `schema/` plus `docs/`.
- Testing: `pytest` runs schema presence check, SQL smoke tests, and CLI `--help` smoke test.
