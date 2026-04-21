# pgvector Setup Guide

To improve entity resolution (mapping varying company names or tickers) beyond simple string matching, we are introducing **pgvector** to the `nlp-risk-analyzer` backend. This document provides a step-by-step guide to installing and configuring `pgvector`.

## Prerequisites
- PostgreSQL 11+ installed.
- Python 3.9+ with `sqlalchemy` and `pgvector` python package installed (added to `backend/requirements.txt`).

---

## Step 1: Install pgvector Extension in PostgreSQL

### Option A: Local Installation (macOS / Linux)
If you run Postgres locally, you'll need to compile the extension or use a package manager.

**macOS (Homebrew):**
```bash
brew install pgvector
```

**Ubuntu/Debian:**
```bash
sudo apt install postgresql-15-pgvector  # replace 15 with your Postgres version
```

### Option B: Docker (Recommended for Local Dev)
Use the official `pgvector` Docker image which comes pre-packaged.
Modify your `docker-compose.yml` (if you have one) or run:
```bash
docker run --name pgvector-db -e POSTGRES_PASSWORD=mysecretpassword -p 5432:5432 -d pgvector/pgvector:pg16
```

### Option C: Cloud Database
Most managed PostgreSQL providers (AWS RDS, Supabase, Neon) support `pgvector` out of the box. You just need to enable it (Step 2).

---

## Step 2: Enable the Extension in the Database

Connect to your database using `psql` or a tool like DBeaver/pgAdmin. Run the following SQL command:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

*Note: You must have superuser privileges or be the database owner to enable extensions.*

## Step 3: Verify the Python Environment

Ensure the correct packages are installed in your backend environment.

```bash
cd backend
pip install -r requirements.txt
# This ensures 'pgvector' and 'sqlalchemy' are installed
```

## Step 4: Add Vector Columns using Alembic

To store embeddings (e.g., text representations of ticker names or descriptions), you need to update your SQLAlchemy models and generate a migration.

1. **Update `app/models/ticker.py`:** Add a `Vector` column.
```python
from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
# ...
class Ticker(Base):
    # ... your existing columns
    embedding = Column(Vector(384)) # 384 for small sentence-transformers (e.g., all-MiniLM-L6-v2)
    # Or 1536 if you use OpenAI text-embedding-3-small
```

2. **Generate Alembic Migration:**
```bash
alembic revision --autogenerate -m "add vector embedding to ticker"
alembic upgrade head
```

## Step 5: Querying with Vector Similarity

Once your tickers receive embeddings, replace the old `difflib.get_close_matches` in `processor.py` with an embedding similarity search.

```python
# Pseudo-code in processor.py mapping logic
from sqlalchemy import select
from pgvector.sqlalchemy import Vector

# Assuming you generate an embedding for the entity string
entity_embedding = generate_embedding(entity_text) 

# Find the closest ticker using L2 distance (<->)
closest_ticker = db.execute(
    select(Ticker).order_by(Ticker.embedding.l2_distance(entity_embedding)).limit(1)
).scalar()
```

You are now ready to scale your entity linkage with dense vector retrieval!
