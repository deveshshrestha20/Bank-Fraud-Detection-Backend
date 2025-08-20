from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from backend.app.core.logging import get_logger
from backend.app.database.session import get_session
from backend.app.models import User
from backend.app.schema.user import UserReadSchema, UserCreateSchema
from backend.app.api.services.auth_service import AuthService


logger = get_logger()
auth_service = AuthService()

register_router = APIRouter(prefix="/auth", tags=["auth"])

@register_router.post("/register", response_model=UserReadSchema, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreateSchema, session: AsyncSession = Depends(get_session)):
    try:
        if await auth_service.check_user_email_exists(session, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )

        if await auth_service.check_user_id_no_exists(session, user_data.id_no):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User ID No. already registered"
            )

        new_user = await auth_service.create_user(user_data, session)
        logger.info(f"Created new user: {new_user.email}")
        return new_user

    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to register user: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create user")

    except HTTPException as http_exception:
        await session.rollback()
        raise http_exception



@register_router.post("/login", response_model=UserReadSchema)
async def login(user_data: UserReadSchema, session: AsyncSession):

