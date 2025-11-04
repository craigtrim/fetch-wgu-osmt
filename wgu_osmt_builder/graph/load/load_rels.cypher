// load_rels.cypher
// One-time param. Replace owner/repo/branch if needed.
:param base => 'https://raw.githubusercontent.com/craigtrim/wgu-osmt-skills-builder/master/wgu_osmt_builder/data/out/graph';

// ---------- RSD → Keyword ----------
LOAD CSV WITH HEADERS FROM $base + '/rels_rsd_hasKeyword.csv' AS row
MATCH (s:RSD {id: row[":START_ID"]})
MATCH (t:Keyword {id: row[":END_ID"]})
MERGE (s)-[:HAS_KEYWORD]->(t);

// ---------- RSD → Category ----------
LOAD CSV WITH HEADERS FROM $base + '/rels_rsd_hasCategory.csv' AS row
MATCH (s:RSD {id: row[":START_ID"]})
MATCH (t:Category {id: row[":END_ID"]})
MERGE (s)-[:HAS_CATEGORY]->(t);

// ---------- RSD → Standard ----------
LOAD CSV WITH HEADERS FROM $base + '/rels_rsd_hasStandard.csv' AS row
MATCH (s:RSD {id: row[":START_ID"]})
MATCH (t:Standard {id: row[":END_ID"]})
MERGE (s)-[:HAS_STANDARD]->(t);

// ---------- RSD → Occupation ----------
LOAD CSV WITH HEADERS FROM $base + '/rels_rsd_hasOccupation.csv' AS row
MATCH (s:RSD {id: row[":START_ID"]})
MATCH (t:Occupation {id: row[":END_ID"]})
MERGE (s)-[:HAS_OCCUPATION]->(t);

// ---------- RSD → Collection ----------
LOAD CSV WITH HEADERS FROM $base + '/rels_rsd_inCollection.csv' AS row
MATCH (s:RSD {id: row[":START_ID"]})
MATCH (t:Collection {id: row[":END_ID"]})
MERGE (s)-[:IN_COLLECTION]->(t);

// ---------- RSD → Alignment ----------
LOAD CSV WITH HEADERS FROM $base + '/rels_rsd_hasAlignment.csv' AS row
MATCH (s:RSD {id: row[":START_ID"]})
MATCH (t:Alignment {id: row[":END_ID"]})
MERGE (s)-[:HAS_ALIGNMENT]->(t);

// ---------- Occupation → Occupation (hierarchy) ----------
LOAD CSV WITH HEADERS FROM $base + '/rels_occupation_partOf.csv' AS row
MATCH (s:Occupation {id: row[":START_ID"]})
MATCH (t:Occupation {id: row[":END_ID"]})
MERGE (s)-[:PART_OF]->(t);
