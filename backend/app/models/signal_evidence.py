"""
SignalEvidence — Join table linking Signals to Evidence records.
Needed so SQLModel's create_all() creates this table automatically.
"""
import uuid
from sqlmodel import Field, SQLModel


class SignalEvidence(SQLModel, table=True):
    __tablename__ = "signal_evidence"

    signal_id: uuid.UUID = Field(
        foreign_key="signals.id",
        primary_key=True,
    )
    evidence_id: uuid.UUID = Field(
        foreign_key="evidence.id",
        primary_key=True,
    )
