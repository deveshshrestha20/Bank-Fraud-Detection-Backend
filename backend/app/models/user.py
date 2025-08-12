
import uuid
from datetime import datetime, timezone

from sqlalchemy import func, text
from sqlalchemy.dialects import postgresql as pg
from sqlmodel import Column, Field, Relationship

from backend.app.schema.otp_question import RoleChoicesSchema
from backend.app.schema.user import BaseUserSchema


class User(BaseUserSchema, table=True):
    id: uuid.UUID = Field(
        sa_column=Column(
            pg.UUID(as_uuid=True),
            primary_key=True,
        ),
        default_factory=uuid.uuid4,
    )
    hashed_password: str
    failed_login_attempts: int = Field(default=0, sa_type=pg.SMALLINT)
    last_failed_login: datetime | None = Field(
        default=None, sa_column=Column(pg.TIMESTAMP(timezone=True))
    )
    otp: str = Field(max_length=6, default="")
    otp_expiry_time: datetime | None = Field(
        default=None, sa_column=Column(pg.TIMESTAMP(timezone=True))
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=text("CURRENT_TIMESTAMP"),
        ),
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(
            pg.TIMESTAMP(timezone=True),
            nullable=False,
            onupdate=func.current_timestamp(),
        ),
    )

    # profile: "Profile" = Relationship(
    #     back_populates="user",
    #     sa_relationship_kwargs={
    #         "uselist": False,
    #         "lazy": "selectin",
    #     },
    # )
    # next_of_kins: list["NextOfKin"] = Relationship(back_populates="user")
    #
    # bank_accounts: list["BankAccount"] = Relationship(back_populates="user")
    #
    # sent_transactions: list["Transaction"] = Relationship(
    #     back_populates="sender",
    #     sa_relationship_kwargs={"foreign_keys": "Transaction.sender_id"},
    # )
    #
    # received_transactions: list["Transaction"] = Relationship(
    #     back_populates="receiver",
    #     sa_relationship_kwargs={"foreign_keys": "Transaction.receiver_id"},
    # )
    #
    # processed_transactions: list["Transaction"] = Relationship(
    #     back_populates="processor",
    #     sa_relationship_kwargs={"foreign_keys": "Transaction.processed_by"},
    # )

    @property
    def full_name(self) -> str:
        # If middle_name exists, include it with spaces, otherwise skip it
        if self.middle_name:
            full_name = f"{self.first_name} {self.middle_name} {self.last_name}"
        else:
            full_name = f"{self.first_name} {self.last_name}"
        # Capitalize first letter of each word and remove extra spaces
        return full_name.title().strip()

    def has_role(self, role: RoleChoicesSchema) -> bool:
        # Check if the user's role matches the given role
        return self.role == role
