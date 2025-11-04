// load_nodes.cypher
// One-time param. Replace owner/repo/branch if needed.
:param base => 'https://raw.githubusercontent.com/craigtrim/wgu-osmt-skills-builder/master/wgu_osmt_builder/data/out/graph';

// ---------- RSD ----------
LOAD CSV WITH HEADERS FROM $base + '/nodes_rsd.csv' AS row
MERGE (n:RSD {id: row[":ID"]})
FOREACH (v IN CASE WHEN row.prefLabel <> '' THEN [row.prefLabel] ELSE [] END | SET n.prefLabel = v)
FOREACH (v IN CASE WHEN row.identifier <> '' THEN [row.identifier] ELSE [] END | SET n.identifier = v)
FOREACH (v IN CASE WHEN row.status <> '' THEN [row.status] ELSE [] END | SET n.status = v)
FOREACH (v IN CASE WHEN row.`created:datetime` <> '' THEN [datetime(row.`created:datetime`)] ELSE [] END | SET n.created = v)
FOREACH (v IN CASE WHEN row.`issued:datetime` <> '' THEN [datetime(row.`issued:datetime`)] ELSE [] END | SET n.issued = v)
FOREACH (v IN CASE WHEN row.`modified:datetime` <> '' THEN [datetime(row.`modified:datetime`)] ELSE [] END | SET n.modified = v);

// ---------- Keyword ----------
LOAD CSV WITH HEADERS FROM $base + '/nodes_keyword.csv' AS row
MERGE (n:Keyword {id: row[":ID"]})
FOREACH (v IN CASE WHEN row.prefLabel <> '' THEN [row.prefLabel] ELSE [] END | SET n.prefLabel = v);

// ---------- Category ----------
LOAD CSV WITH HEADERS FROM $base + '/nodes_category.csv' AS row
MERGE (n:Category {id: row[":ID"]})
FOREACH (v IN CASE WHEN row.prefLabel <> '' THEN [row.prefLabel] ELSE [] END | SET n.prefLabel = v);

// ---------- Standard ----------
LOAD CSV WITH HEADERS FROM $base + '/nodes_standard.csv' AS row
MERGE (n:Standard {id: row[":ID"]})
FOREACH (v IN CASE WHEN row.prefLabel <> '' THEN [row.prefLabel] ELSE [] END | SET n.prefLabel = v)
FOREACH (v IN CASE WHEN row.notation  <> '' THEN [row.notation]  ELSE [] END | SET n.notation  = v);

// ---------- Occupation ----------
LOAD CSV WITH HEADERS FROM $base + '/nodes_occupation.csv' AS row
MERGE (n:Occupation {id: row[":ID"]})
FOREACH (v IN CASE WHEN row.prefLabel <> '' THEN [row.prefLabel] ELSE [] END | SET n.prefLabel = v)
FOREACH (v IN CASE WHEN row.code      <> '' THEN [row.code]      ELSE [] END | SET n.code      = v);

// ---------- Collection ----------
LOAD CSV WITH HEADERS FROM $base + '/nodes_collection.csv' AS row
MERGE (n:Collection {id: row[":ID"]})
FOREACH (v IN CASE WHEN row.title      <> '' THEN [row.title]      ELSE [] END | SET n.title      = v)
FOREACH (v IN CASE WHEN row.identifier <> '' THEN [row.identifier] ELSE [] END | SET n.identifier = v);

// ---------- Alignment ----------
LOAD CSV WITH HEADERS FROM $base + '/nodes_alignment.csv' AS row
MERGE (n:Alignment {id: row[":ID"]})
FOREACH (v IN CASE WHEN row.prefLabel  <> '' THEN [row.prefLabel]  ELSE [] END | SET n.prefLabel  = v)
FOREACH (v IN CASE WHEN row.identifier <> '' THEN [row.identifier] ELSE [] END | SET n.identifier = v);
