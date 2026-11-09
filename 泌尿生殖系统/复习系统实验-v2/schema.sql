PRAGMA foreign_keys = ON;

CREATE TABLE source_documents (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  kind TEXT NOT NULL,
  path TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  raw_text TEXT NOT NULL
);

CREATE TABLE candidate_segments (
  id TEXT PRIMARY KEY,
  source_document_id TEXT NOT NULL REFERENCES source_documents(id),
  ordinal INTEGER NOT NULL,
  start_line INTEGER NOT NULL,
  end_line INTEGER NOT NULL,
  heading_level INTEGER,
  heading TEXT,
  heading_path TEXT,
  text TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  UNIQUE(source_document_id, ordinal)
);

CREATE TABLE knowledge_nodes (
  id TEXT PRIMARY KEY,
  parent_id TEXT REFERENCES knowledge_nodes(id),
  title TEXT NOT NULL,
  canonical_path TEXT NOT NULL UNIQUE,
  origin TEXT NOT NULL,
  syllabus_level TEXT,
  status TEXT NOT NULL DEFAULT 'active'
);

CREATE TABLE node_relations (
  from_node_id TEXT NOT NULL REFERENCES knowledge_nodes(id),
  to_node_id TEXT NOT NULL REFERENCES knowledge_nodes(id),
  relation_type TEXT NOT NULL,
  strength REAL NOT NULL DEFAULT 1.0,
  note TEXT,
  PRIMARY KEY(from_node_id, to_node_id, relation_type)
);

CREATE TABLE fragments (
  id TEXT PRIMARY KEY,
  source_document_id TEXT NOT NULL REFERENCES source_documents(id),
  knowledge_node_id TEXT REFERENCES knowledge_nodes(id),
  start_line INTEGER NOT NULL,
  end_line INTEGER NOT NULL,
  text TEXT NOT NULL,
  sha256 TEXT NOT NULL,
  split_method TEXT NOT NULL,
  review_status TEXT NOT NULL,
  mapping_status TEXT NOT NULL
);

CREATE TABLE fragment_members (
  fragment_id TEXT NOT NULL REFERENCES fragments(id),
  candidate_segment_id TEXT NOT NULL REFERENCES candidate_segments(id),
  member_order INTEGER NOT NULL,
  PRIMARY KEY(fragment_id, candidate_segment_id)
);

CREATE TABLE evidence (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  knowledge_node_id TEXT NOT NULL REFERENCES knowledge_nodes(id),
  fragment_id TEXT REFERENCES fragments(id),
  source_kind TEXT NOT NULL,
  source_locator TEXT,
  directness TEXT NOT NULL,
  signal TEXT NOT NULL,
  raw_excerpt TEXT,
  value REAL
);

CREATE TABLE score_schemes (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  config_json TEXT NOT NULL
);

CREATE TABLE node_scores (
  scheme_id TEXT NOT NULL REFERENCES score_schemes(id),
  knowledge_node_id TEXT NOT NULL REFERENCES knowledge_nodes(id),
  total_score REAL NOT NULL,
  components_json TEXT NOT NULL,
  PRIMARY KEY(scheme_id, knowledge_node_id)
);

CREATE TABLE exercise_items (
  id TEXT PRIMARY KEY,
  knowledge_node_id TEXT NOT NULL REFERENCES knowledge_nodes(id),
  source TEXT,
  question TEXT NOT NULL,
  answer TEXT,
  metadata_json TEXT
);
