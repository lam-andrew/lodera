# 0002. PostgreSQL 16 + pgvector (relational + vector store in one service)

- **Status:** Accepted
- **Date:** 2026-08-28

## Context

Orbit stores two kinds of data: **relational data** (users, portfolios, holdings, cached
market prices) and **vector embeddings** of SEC filing text for the secondary RAG layer.
A naive design would run a relational database plus a dedicated vector database as separate
services. For a solo developer on a 14-week timeline, every additional service is more
operational surface to configure, containerize, test, back up, and reason about.

We needed a storage approach that supports both relational queries and vector similarity
search while minimizing the number of moving parts.

## Decision

We will use **PostgreSQL 16 with the pgvector extension** as the single data service, storing
both relational data and filing embeddings in the same database.

- Portfolios, holdings, and the market-data cache use ordinary relational tables.
- Filing embeddings use pgvector columns with vector similarity indexes.

## Consequences

- **Positive:** One database service instead of two — simpler Docker Compose, fewer
  connection strings, one backup/restore path, one thing to learn deeply.
- **Positive:** Relational and vector data can be joined in a single query (e.g. "embeddings
  for filings belonging to holdings in this portfolio") without cross-service coordination.
- **Positive:** PostgreSQL is provider-agnostic and runs anywhere, consistent with the
  no-lock-in goal (see [0003](0003-docker-compose-provider-agnostic.md)).
- **Cost:** pgvector's performance ceiling is below that of a specialized vector database at
  very large scale. For a capstone-scale corpus this is a non-issue; if it ever mattered, a
  future ADR would introduce a dedicated vector store and supersede this one.
- **Cost:** The Postgres image must include the pgvector extension (use a `pgvector/pgvector`
  image or install the extension), and a migration must `CREATE EXTENSION vector`.

## Alternatives Considered

- **Postgres + a dedicated vector DB (Pinecone, Weaviate, Qdrant, Milvus):** better vector
  performance at scale, but adds a second service (and for hosted options, a paid dependency
  and vendor lock-in) that a capstone-scale corpus does not justify.
- **SQLite + a local vector index (FAISS/Chroma):** lighter for local dev, but SQLite is a
  poor fit for a containerized multi-service deployment and would diverge from the production
  target.
