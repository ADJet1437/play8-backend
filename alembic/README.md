# Alembic Database Migrations

This directory contains Alembic database migration scripts.

## Usage

### Create a new migration
```bash
alembic revision --autogenerate -m "description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback one migration
```bash
alembic downgrade -1
```

### Rollback to a specific revision
```bash
alembic downgrade <revision_id>
```

### View current revision
```bash
alembic current
```

### View migration history
```bash
alembic history
```

## Configuration

- Database URL is read from `DATABASE_URL` environment variable
- Models are imported from `src/` directory
- Migration files are stored in `alembic/versions/`

## Initial Setup

After setting up Alembic, create your first migration:

```bash
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```


