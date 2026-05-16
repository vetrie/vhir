"""SQLAlchemy table definitions — one table per resource type."""
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB

metadata = MetaData()

_RESOURCE_TYPES = [
    "animal",
    "owner",
    "practitioner",
    "practitioner_role",
    "organization",
    "encounter",
    "observation",
    "condition",
    "medication_request",
]


def _resource_table(name: str) -> Table:
    """Build a standard resource table with JSONB body and history support."""
    return Table(
        name,
        metadata,
        Column("id", Text, primary_key=True),
        Column("version", Integer, nullable=False, default=1),
        Column("last_updated", DateTime(timezone=True), nullable=False, server_default=func.now()),
        Column("body", JSONB, nullable=False),
        Column("deleted", Boolean, nullable=False, default=False),
    )


animal            = _resource_table("animal")
owner             = _resource_table("owner")
practitioner      = _resource_table("practitioner")
practitioner_role = _resource_table("practitioner_role")
organization      = _resource_table("organization")
encounter         = _resource_table("encounter")
observation       = _resource_table("observation")
condition_table   = _resource_table("condition")
medication_request = _resource_table("medication_request")

# History table for all resources (append-only)
resource_history = Table(
    "resource_history",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("resource_type", Text, nullable=False),
    Column("resource_id", Text, nullable=False),
    Column("version", Integer, nullable=False),
    Column("changed_at", DateTime(timezone=True), nullable=False, server_default=func.now()),
    Column("body", JSONB, nullable=False),
    Column("operation", Text, nullable=False),  # create / update / delete
)

# GIN indexes for fast JSONB search
Index("ix_animal_identifiers", animal.c.body["identifiers"], postgresql_using="gin")
Index("ix_animal_owners",      animal.c.body["owners"],      postgresql_using="gin")
Index("ix_observation_code",   observation.c.body["code"],   postgresql_using="gin")
Index("ix_condition_code",     condition_table.c.body["code"], postgresql_using="gin")
