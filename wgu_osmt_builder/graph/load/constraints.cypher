// Primary key by internal ID you set during LOAD CSV (n.id = row[":ID"])
CREATE CONSTRAINT rsd_id            IF NOT EXISTS FOR (n:RSD)            REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT keyword_id        IF NOT EXISTS FOR (n:Keyword)        REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT category_id       IF NOT EXISTS FOR (n:Category)       REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT standard_id       IF NOT EXISTS FOR (n:Standard)       REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT occupation_id     IF NOT EXISTS FOR (n:Occupation)     REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT collection_id     IF NOT EXISTS FOR (n:Collection)     REQUIRE n.id IS UNIQUE;
CREATE CONSTRAINT alignment_id      IF NOT EXISTS FOR (n:Alignment)      REQUIRE n.id IS UNIQUE;

// Natural keys (helps prevent accidental dupes even if :ID mapping changes)
CREATE CONSTRAINT rsd_identifier    IF NOT EXISTS FOR (n:RSD)            REQUIRE n.identifier IS UNIQUE;
CREATE CONSTRAINT standard_notation IF NOT EXISTS FOR (n:Standard)       REQUIRE n.notation   IS UNIQUE;
CREATE CONSTRAINT occupation_code   IF NOT EXISTS FOR (n:Occupation)     REQUIRE n.code       IS UNIQUE;
CREATE CONSTRAINT collection_ident  IF NOT EXISTS FOR (n:Collection)     REQUIRE n.identifier IS UNIQUE;
CREATE CONSTRAINT alignment_ident   IF NOT EXISTS FOR (n:Alignment)      REQUIRE n.identifier IS UNIQUE;
