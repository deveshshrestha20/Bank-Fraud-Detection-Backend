from enum import Enum
from pydantic import BaseModel

class SecurityQuestionsSchema(str, Enum):
    MOTHER_MAIDEN_NAME = "What is the name of your mother?"
    CHILDHOOD_FRIEND = "What is the name of your childhood friend?"
    FAVORITE_COLOR = "What is your favorite color?"
    BIRTH_CITY = "What is the name of the city you were born in?"

class UserSecurityQuestion(BaseModel):
    question: SecurityQuestionsSchema
    answer: str


class AccountStatusSchema(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    PENDING = "pending"


class RoleChoicesSchema(str, Enum):
    CUSTOMER = "customer"
    ACCOUNT_EXECUTIVE = "account_executive"
    BRANCH_MANAGER = "branch_manager"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    TELLER = "teller"