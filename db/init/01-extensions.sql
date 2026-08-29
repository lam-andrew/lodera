-- Database initialization for Lodera.
-- Runs once, automatically, the first time the PostgreSQL data volume is created
-- (scripts in /docker-entrypoint-initdb.d are executed by the official Postgres image).

-- pgvector: enables vector columns + similarity search for the RAG layer's filing
-- embeddings, kept in the same database as relational data (see ADR 0002).
CREATE EXTENSION IF NOT EXISTS vector;
