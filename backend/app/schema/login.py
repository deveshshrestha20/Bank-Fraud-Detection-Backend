from pydantic import EmailStr
from sqlmodel import SQLModel, Field


class EmailRequestSchema(SQLModel):
    email: EmailStr


class OTPVerifyRequestSchema(SQLModel):
    email: EmailStr
    otp: str = Field(min_length=6, max_length=6)