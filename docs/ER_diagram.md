# ER Diagram

The editable source of the diagram lives at `ER_diagram.drawio` (to be produced with draw.io / diagrams.net). An exported `ER_diagram.png` is the authoritative copy for the report. This file documents the content of the diagram so that whoever redraws it does not reintroduce the mistakes flagged in the TA proposal feedback.

## Entities (boxes)

| Entity | Attributes shown inside the box | Notes |
| --- | --- | --- |
| User | userID (key), username, email, dateCreated | strong entity |
| Clip | clipID (key), title, duration, filepath, dateCreated | strong entity; **no** `userID` inside the box |
| MusicalAttributes | musicalKey, mode, tempo, timeSignature | weak entity of Clip (identifying relationship below) |
| Project | projectID (key), name, description, dateCreated | strong entity; **no** `ownerUserID` inside the box |
| Tag | tagID (key), tagName | strong entity; **no** `userID` inside the box |
| ClipVersion | versionNumber (partial key), notes, filepath, dateCreated | weak entity of Clip |

## Relationships (diamonds)

| Relationship | Between | Cardinality | Participation | Attributes |
| --- | --- | --- | --- | --- |
| Owns | User — Clip | 1 : N | Clip total, User partial | — |
| Has | Clip — MusicalAttributes | 1 : 1 | MusicalAttributes total (identifying) | — |
| Creates | User — Project | 1 : N | Project total, User partial | — |
| Defines | User — Tag | 1 : N | Tag total, User partial | — |
| TaggedWith | Clip — Tag | M : N | partial both sides | — |
| Contains | Project — Clip | M : N | partial both sides | — |
| Collaborates | User — Project | M : N | partial both sides | role, addedAt |
| HasVersion | Clip — ClipVersion | 1 : N | ClipVersion total (identifying) | — |

## TA feedback that this diagram must satisfy

- **No foreign-key attributes inside entity boxes.** Proposal had `userID` inside Clip, `userID` inside Tags, `userID` inside Projects, `clipID` inside MusicalAttributes. All removed; the diamonds express those links.
- **The `Collaborates` relationship carries `role` and `addedAt` as relationship attributes.** Do not draw them on the Project or User boxes.
- **MusicalAttributes and ClipVersion are weak entities.** Draw double-lined rectangles around them and double-lined diamonds for their identifying relationships (`Has`, `HasVersion`).

## Export checklist

1. Open `ER_diagram.drawio` in diagrams.net.
2. Verify every entity/relationship in the tables above appears and no FK attributes are in boxes.
3. File → Export as PNG, 300 DPI, transparent background off, save as `docs/ER_diagram.png`.
4. Also export a PDF copy at `report/assets/ER_diagram.pdf` for the final report.
