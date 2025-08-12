from typing import Optional

from fastapi import HTTPException
from sqlmodel import SQLModel, Field
from pydantic import EmailStr, field_validator
from sqlalchemy import String, Column
from starlette import status

from backend.app.schema.otp_question import SecurityQuestionsSchema, AccountStatusSchema, RoleChoicesSchema


class BaseUserSchema(SQLModel):
    username: Optional[str] = Field(
        default=None,
        sa_column=Column(String(12), unique=True)
    )
    email: EmailStr = Field(
        sa_column=Column(String(255), unique=True, index=True)
    )
    first_name: str = Field(sa_column=Column(String(30)))
    middle_name: Optional[str] = Field(default=None, sa_column=Column(String(30)))
    last_name: str = Field(sa_column=Column(String(30)))
    id_no: int = Field(sa_column=Column(unique=True))
    is_active: bool = Field(default=False)
    is_superuser: bool = Field(default=False)
    security_question: SecurityQuestionsSchema
    security_answer: str = Field(sa_column=Column(String(30)))
    account_status: AccountStatusSchema = Field(default=AccountStatusSchema.INACTIVE)
    role: RoleChoicesSchema = Field(default=RoleChoicesSchema.CUSTOMER)


class UserCreateSchema(BaseUserSchema):
    password: str = Field(min_length=8, max_length=40)
    confirm_password: str = Field(min_length=8, max_length=40)

    @field_validator("confirm_password")
    def validate_confirm_password(cls, confirm_password, values):
        password = values.data.get("password")  # Get the 'password' field
        if password and confirm_password != password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Passwords do not match",
                    "action": "Please ensure that the passwords you entered match",
                },
            )
        return confirm_password