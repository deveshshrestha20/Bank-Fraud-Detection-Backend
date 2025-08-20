from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from backend.app.auth.utils import create_activation_token
from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.services.activate_email import send_activation_email
from backend.app.database.session import get_session
from backend.app.schema.otp_question import AccountStatusSchema
from backend.app.schema.user import UserReadSchema, EmailRequestSchema
from backend.app.api.services.auth_service import AuthService

logger = get_logger()
auth_service = AuthService()

activate_router = APIRouter(prefix="/auth", tags=["activate_account"])

@activate_router.post("/activate/{token}", response_model=UserReadSchema, status_code=status.HTTP_200_OK)
async def activate_user(token: str, session: AsyncSession = Depends(get_session)):
    try:
        user = await auth_service.activate_user_account(session, token)
        return {"message": "User activated successfully", "email": user.email}

    except ValueError as e:
        error_msg = str(e)

        if error_msg == "Activation token has expired. Please request a new activation email.":
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail={
                    "status": "error",
                    "message": "Activation token has expired.",
                    "action": "Please request a new activation email.",
                    "action_url": f"{settings.API_BASE_URL}/auth/resend_activation_link",
                    "email_required": True,
                }
            )
        elif error_msg == "Invalid activation token":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Activation token is invalid.",
                    "action": "Please confirm your activation token is valid.",
                }
            )
        elif error_msg == "User already active":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "User is already active.",
                    "action": "There is no need to activate your account.",
                }
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

    except HTTPException as http_exception:
        raise http_exception

    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate user: {e}"
        )

@activate_router.post("/resend_activation_email", response_model=UserReadSchema, status_code=status.HTTP_200_OK)
async def resend_activation_link(email_data: EmailRequestSchema, session: AsyncSession = Depends(get_session) ):
    try:
        user = await auth_service.get_user_by_email(email_data.email, session, include_inactive=True)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {email_data.email} not found",
            )
        if user.is_active or user.account_status == AccountStatusSchema.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "User is already active. No need to activate your account.",
                    "action": "Please login to your account.",
                },
            )

        activation_token = create_activation_token(user.id)
        await send_activation_email(user.email, activation_token)

        return {
            "message": "New activation link has been sent. Please check you email inbox.",
        }

    except HTTPException as http_exception:
        raise http_exception
    except Exception as e:
        logger.error(f"Failed to resend activation link: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": "error",
                "message":"Failed to resend activation link.",
                "action": "Please try again later.",
            },
        )
