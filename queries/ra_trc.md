# Queries in Relational Algebra and Tuple Relational Calculus

The CSDS 341 spec (§7) requires examples in SQL, Relational Algebra (RA), and Tuple Relational Calculus (TRC), and specifically at least **one** query that can be expressed in all three formalisms. Query E3 (easy) is that query; we also render several others to show mastery of the formalisms.

Notation:
- `σ_P(R)` — selection with predicate `P` on relation `R`
- `π_A(R)` — projection onto attribute set `A`
- `R ⋈_P S` — theta-join on predicate `P`
- `R ⋈ S` — natural join
- TRC: `{ t | F(t) }` where `F` is a first-order formula over tuple variables
- `∃`, `∀`, `∧`, `∨`, `¬`, `→` have the usual meaning

---

## E3: Every clip whose tempo is in [90, 120] BPM (SQL + RA + TRC)

**SQL**
```sql
SELECT c.clipID, c.title, ma.musicalKey, ma.mode, ma.tempo
FROM Clips c
JOIN MusicalAttributes ma ON ma.clipID = c.clipID
WHERE ma.tempo BETWEEN 90 AND 120;
```

**Relational algebra**
```
π_{clipID, title, musicalKey, mode, tempo} (
    σ_{tempo ≥ 90 ∧ tempo ≤ 120} (
        Clips ⋈ MusicalAttributes
    )
)
```

**TRC**
```
{ t.clipID, t.title, a.musicalKey, a.mode, a.tempo |
    ∃ c ∈ Clips ( c.clipID = t.clipID ∧ c.title = t.title ) ∧
    ∃ a ∈ MusicalAttributes ( a.clipID = t.clipID ∧
                              a.tempo ≥ 90 ∧ a.tempo ≤ 120 )
}
```

This single query satisfies the spec requirement of "at least one query expressible in all three formalisms".

---

## E2: Clips per user (RA only — aggregation is not in basic RA, so this is illustrative)

RA does not have a native aggregation operator in the textbook definition; most textbooks introduce a `γ` operator as a convenience extension. With that extension:

```
γ_{u.username ; count(c.clipID) → clip_count} (
    Users u ⟕ Clips c on u.userID = c.userID
)
```
The `⟕` is a left outer join so users with zero clips still appear. Without `γ`, the query cannot be written in pure RA, which is why the spec warns that not every SQL query has a RA/TRC form.

---

## H1: Orphaned clips (RA and TRC)

A clip that is not in any project.

**RA**
```
π_{clipID, title} ( Clips ) − π_{clipID, title} ( Clips ⋈ ProjectClips )
```

**TRC**
```
{ t.clipID, t.title |
    ∃ c ∈ Clips ( c.clipID = t.clipID ∧ c.title = t.title ) ∧
    ¬ ∃ pc ∈ ProjectClips ( pc.clipID = t.clipID )
}
```

---

## H2: Users who have tagged every one of their own clips (TRC only)

This is a universal-quantifier query. Pure RA cannot express it with only the basic operators; TRC handles it directly with `∀`.

**TRC**
```
{ t.username |
    ∃ u ∈ Users ( u.username = t.username ∧
        ∀ c ∈ Clips (
            c.userID = u.userID →
            ∃ ct ∈ ClipTags ( ct.clipID = c.clipID )
        )
    )
}
```

In RA one would write it as division:
```
π_{username} (Users)
    − π_{username} (
        (Clips ⋈ Users) − π_{clipID, userID, username} (
            ClipTags ⋈ Clips ⋈ Users
        )
    )
```
which is equivalent but much less readable — exactly the tradeoff the spec wants us to illustrate.

---

## M2: Projects whose clips come from multiple owners (RA)

```
π_{projectID, name} (
    γ_{projectID, name ; count(distinct userID) → owners} (
        Projects ⋈ ProjectClips ⋈ Clips
    )
) ⋈ σ_{owners > 1}
```

The same caveat about `γ` applies.

---

## Queries that can **not** be expressed in basic RA or TRC

- **M3** (compare per-user average tempo to overall average) requires aggregation and therefore needs the extended RA `γ` operator and extended TRC with aggregate functions. The spec notes that such queries motivate the extensions.
- **H3** (most recent version of each clip) requires `MAX` per group, again aggregation.
- Any query that uses ORDER BY + LIMIT (e.g. top-10 tags) is not expressible because neither formalism has an ordering notion.

We flag these three in report §6 as examples of SQL features that live outside classical RA/TRC.
