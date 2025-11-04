# Graph CSV Schema (for `graphs/`)

Rapid reference to build the Neo4j schema and bulk-import mappings from the CSVs under `wgu_osmt_builder/data/out/graph/`.

---

## Node files

| File | Node label | Columns (name:type) |
|---|---|---|
| `nodes_rsd.csv` | `RichSkillDescriptor` | `:ID:string`, `:LABEL:string`, `prefLabel:string`, `identifier:string`, `status:string`, `created:datetime`, `issued:datetime`, `modified:datetime` |
| `nodes_keyword.csv` | `Keyword` | `:ID:string`, `:LABEL:string`, `prefLabel:string` |
| `nodes_category.csv` | `Category` | `:ID:string`, `:LABEL:string`, `prefLabel:string` |
| `nodes_standard.csv` | `Standard` | `:ID:string`, `:LABEL:string`, `prefLabel:string`, `notation:string` |
| `nodes_occupation.csv` | `Occupation` | `:ID:string`, `:LABEL:string`, `prefLabel:string`, `code:string` |
| `nodes_collection.csv` | `Collection` | `:ID:string`, `:LABEL:string`, `title:string`, `identifier:string` |
| `nodes_alignment.csv` | `Alignment` | `:ID:string`, `:LABEL:string`, `prefLabel:string`, `identifier:string` |

Notes:
- `:ID` values are localnames from TTL, e.g. `rsd-<uuid>`, `kw-<slug>`, `cat-<slug>`, `std-<slug>`, `bls-<code>`, `col-<uuid>`, `align-<slug>`.
- All non-`datetime` columns are strings. `created`, `issued`, `modified` are `datetime`.

---

## Relationship files

All relationship CSVs share the header: `:START_ID,:END_ID,:TYPE`

| File | Edge label (`:TYPE`) | Source node file → Target node file |
|---|---|---|
| `rels_rsd_hasKeyword.csv` | `HAS_KEYWORD` | `nodes_rsd.csv` → `nodes_keyword.csv` |
| `rels_rsd_hasCategory.csv` | `HAS_CATEGORY` | `nodes_rsd.csv` → `nodes_category.csv` |
| `rels_rsd_hasStandard.csv` | `HAS_STANDARD` | `nodes_rsd.csv` → `nodes_standard.csv` |
| `rels_rsd_hasOccupation.csv` | `HAS_OCCUPATION` | `nodes_rsd.csv` → `nodes_occupation.csv` |
| `rels_rsd_inCollection.csv` | `IN_COLLECTION` | `nodes_rsd.csv` → `nodes_collection.csv` |
| `rels_rsd_hasAlignment.csv` | `HAS_ALIGNMENT` | `nodes_rsd.csv` → `nodes_alignment.csv` |
| `rels_occupation_partOf.csv` | `PART_OF` | `nodes_occupation.csv` → `nodes_occupation.csv` (hierarchy) |

---

## Suggested Neo4j constraints

```cypher
// One constraint per label on :ID
CREATE CONSTRAINT rsd_id IF NOT EXISTS FOR (n:RichSkillDescriptor) REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT kw_id  IF NOT EXISTS FOR (n:Keyword)            REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT cat_id IF NOT EXISTS FOR (n:Category)           REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT std_id IF NOT EXISTS FOR (n:Standard)           REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT bls_id IF NOT EXISTS FOR (n:Occupation)         REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT col_id IF NOT EXISTS FOR (n:Collection)         REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT aln_id IF NOT EXISTS FOR (n:Alignment)          REQUIRE n.id IS UNIQUE;
```

When using `neo4j-admin database import` or `neo4j-admin import`, map `:ID` to `id` and `:LABEL` to labels automatically. If loading via Cypher `LOAD CSV`, set `n.id = row.\`:ID\`` explicitly.

---

## Minimal bulk-import mapping (neo4j-admin)

Place all CSVs under a single directory and run something like:

```bash
neo4j-admin database import full \
  --nodes=RichSkillDescriptor=nodes_rsd.csv \
  --nodes=Keyword=nodes_keyword.csv \
  --nodes=Category=nodes_category.csv \
  --nodes=Standard=nodes_standard.csv \
  --nodes=Occupation=nodes_occupation.csv \
  --nodes=Collection=nodes_collection.csv \
  --nodes=Alignment=nodes_alignment.csv \
  --relationships=HAS_KEYWORD=rels_rsd_hasKeyword.csv \
  --relationships=HAS_CATEGORY=rels_rsd_hasCategory.csv \
  --relationships=HAS_STANDARD=rels_rsd_hasStandard.csv \
  --relationships=HAS_OCCUPATION=rels_rsd_hasOccupation.csv \
  --relationships=IN_COLLECTION=rels_rsd_inCollection.csv \
  --relationships=HAS_ALIGNMENT=rels_rsd_hasAlignment.csv \
  --relationships=PART_OF=rels_occupation_partOf.csv
```

This importer respects the `:ID`, `:START_ID`, `:END_ID`, `:LABEL`, and `:TYPE` headers.

---
