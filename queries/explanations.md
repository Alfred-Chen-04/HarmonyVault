# Query catalog — plain-English descriptions

Every query in `easy.sql`, `medium.sql`, `hard.sql`, paired with the real-world question it answers. Mirrored into report §6.

## Easy

| ID | English | SQL file |
| --- | --- | --- |
| E1 | "List every registered user in signup order." | easy.sql |
| E2 | "How many clips does each user own?" | easy.sql |
| E3 | "Which clips have a tempo between 90 and 120 BPM?" | easy.sql |

## Medium

| ID | English | SQL file |
| --- | --- | --- |
| M1 | "Show me Alfred's C-minor clips in the 90-120 BPM range." | medium.sql |
| M2 | "Which projects have clips from multiple owners (i.e. real collaboration)?" | medium.sql |
| M3 | "Which users have an average tempo above the overall average?" | medium.sql |

## Hard

| ID | English | SQL file |
| --- | --- | --- |
| H1 | "Which clips are not in any project?" (the orphaned-ideas use case) | hard.sql |
| H2 | "Which users have tagged every clip they own?" (universal quantifier) | hard.sql |
| H3 | "For every clip, give me its most recent version together with its musical attributes and owner." | hard.sql |

## Admin (cross-user, added for TA feedback item 1)

| ID | English | Invoked via |
| --- | --- | --- |
| A1 | "Top-N most popular tag names across the platform." | `python -m cli admin top-tags` |
| A2 | "Per-user stats: clip count, project count, memberships." | `python -m cli admin user-stats` |
| A3 | "Tempo histogram across all stored clips." | `python -m cli admin tempo-histogram` |
