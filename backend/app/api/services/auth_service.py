import asyncio
import uuid
from datetime import datetime, timezone, timedelta

import jwt
from fastapi import status
from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select


from backend.app.auth.utils import verify_password, generate_otp, generate_username, hash_password, \
    create_activation_token
from backend.app.core.config import settings
from backend.app.core.logging import get_logger
from backend.app.core.services.activate_email import send_activation_email
from backend.app.core.services.otp_login import send_login_otp_email
from backend.app.models import User
from backend.app.schema.otp_question import AccountStatusSchema
from backend.app.schema.user import UserCreateSchema

logger = get_logger()


class AuthService:

    def __init__(self,db):
              self.db = db

    async def get_user_by_email(self,email: EmailStr, session: AsyncSession, include_inactive:bool = False) -> User | None:
        stmt = select(User).where(User.email == email)
        if include_inactive:
            stmt = stmt.where(User.is_active == False)
        result = await session.execute(stmt)
        return result.scalars().first()

    # For looking up Bank account / external ID (id_number) || Fraud check, transaction validation, external references
    async def get_user_by_id_no(self,id_no: int, session: AsyncSession, include_inactive:bool = False) -> User | None:
        stmt = select(User).where(User.id_no == id_no)
        if include_inactive:
            stmt = stmt.where(User.is_active == False)
        result = await session.execute(stmt)
        return result.scalars().first()

# For looking up DB primary key (id) || JWT token lookup, profile view, internal operations
    async def get_user_by_id(self,id: uuid.UUID, session: AsyncSession, include_inactive:bool = False) -> User | None:
        stmt = select(User).where(User.id == id)
        if include_inactive:
            stmt = stmt.where(User.is_active == False)
        result = await session.execute(stmt)
        return result.scalars().first()

    # Simple helper methods / functions for checking if user email , id number and id exists or not
    async def check_user_email_exists(self, email: EmailStr, session: AsyncSession) -> bool:
        user = await self.get_user_by_email(email, session, include_inactive=False)
        return bool(user)

    async def check_user_id_no_exists(self, id_no: int, session: AsyncSession) -> bool:
        id_no = await self.get_user_by_id_no(id_no, session, include_inactive=False)
        return bool(id_no)

    async def check_user_id_exists(self, id: uuid.UUID, session: AsyncSession) -> bool:
        id = await self.get_user_by_id(id, session, include_inactive=False)
        return bool(id)

    async def verify_user_password(self,plain_password: str, hashed_password: str) -> bool:
        return verify_password(plain_password, hashed_password)

    async def reset_user_state(
            self,
            user: User,
            session: AsyncSession,
            *,
            clear_otp: bool = True,
            log_action: bool = True,
    ) -> None:
        previous_status = user.account_status

        user.failed_login_attempts = 0
        user.last_failed_login = None

        if clear_otp:
            user.otp = ""
            user.otp_expiry_time = None

        if user.account_status == AccountStatusSchema.LOCKED:
            user.account_status = AccountStatusSchema.ACTIVE

        await session.commit()

        await session.refresh(user)

        if log_action and previous_status != user.account_status:
            logger.info(
                f"User {user.email} state reset: {previous_status} -> {user.account_status}"
            )

    async def validate_user_status(self, user: User) -> None:
        if not user.is_active:
            return HTTPException(status_code=404, detail={
                "status": "error",
                "message":"User is not active",
                "action": "Please activate your account first",
            })

        if user.account_status == AccountStatusSchema.LOCKED:
            return HTTPException(status_code=404, detail={
                "status": "error",
                "message": "Your account is locked",
                "action": "Contact support team",
            })

        if user.account_status == AccountStatusSchema.INACTIVE:
            return HTTPException(status_code=404, detail={
                "status": "error",
                "message": "Your account is inactive",
                "action": "Please activate your account",
            })

    async def generate_and_save_otp(
        self,
        user: User,
        session: AsyncSession,
    ) -> tuple[bool, str]:
        try:
            otp = generate_otp()
            user.otp = otp

            user.otp_expiry_time = datetime.now(timezone.utc) + timedelta(
                minutes=settings.OTP_EXPIRATION_MINUTES
            )

            await session.commit()
            await session.refresh(user)
        #
            for attempt in range(3):
                try:
                    await send_login_otp_email(user.email, otp)
                    logger.info(f"OTP sent to {user.email} successfully")
                    return True, otp
                except Exception as e:
                    logger.error(
                        f"Failed to send OTP email (attempt {attempt + 1}): {e}"
                    )
                    if attempt == 2:
                        user.otp = ""
                        user.otp_expiry_time = None
                        await session.commit()
                        await session.refresh(user)
                        return False, ""

                    await asyncio.sleep(2**attempt)
            return False, ""


        # If anything fails:
        # Log the error.
        except Exception as e:
            logger.error(f"Failed to generate and save OTP: {e}")


            # Clear the OTP and expiry time. Commit changes again to keep data clean. Return failure
            user.otp = ""
            user.otp_expiry_time = None
            await session.commit()
            await session.refresh(user)
            return False, ""

    async def create_user(
            self,
            user_data: UserCreateSchema,
            session: AsyncSession,
    ) -> User:
        user_data_dict = user_data.model_dump(
            exclude={"confirm_password", "username", "is_active", "account_status"}
        )

        password = user_data_dict.pop("password")

        new_user = User(
            username=generate_username(),
            hashed_password=hash_password(password),
            is_active=False,
            account_status=AccountStatusSchema.PENDING,
            **user_data_dict,
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        activation_token = create_activation_token(new_user.id)
        try:
            await send_activation_email(new_user.email, activation_token)
            logger.info(f"Activation email sent to {new_user.email}")

        except Exception as e:
            logger.error(f"Failed to send activation email to {new_user.email}: {e}")
            raise

        return new_user

    async def activate_user_account(
            self,
            token: str,
            session: AsyncSession,
    ) -> User:
        try:
            payload = jwt.decode(
                token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
            )

            if payload.get("type") != "activation":
                raise ValueError("Invalid token type")

            user_id = uuid.UUID(payload["id"])

            user = await self.get_user_by_id(user_id, session, include_inactive=True)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "status": "error",
                        "message": "User not found",
                    },
                )
            if user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "User already activated",
                    },
                )
            await self.reset_user_state(user, session, clear_otp=True, log_action=True)

            user.is_active = True
            user.account_status = AccountStatusSchema.ACTIVE

            await session.commit()
            await session.refresh(user)

            return user

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Activation token expired",
                },
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "status": "error",
                    "message": "Invalid activation token",
                },
            )
        except HTTPException as http_ex:
            raise http_ex
        except Exception as e:
            logger.error(f"Failed to activate user account: {e}")
            raise

    async def verify_login_otp(
            self,
            email: str,
            otp: str,
            session: AsyncSession,
    ) -> User:
        try:
            user = await self.get_user_by_email(email, session)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={"status": "error", "message": "Invalid credentials"},
                )

            await self.validate_user_status(user)
            await self.check_user_lockout(user, session)

            # OTP check
            if user.otp != otp:
                await self.increment_failed_login_attempts(user, session)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "Invalid OTP",
                        "action": "Please check your OTP and try again",
                    },
                )

            # Expiry check
            if not user.otp_expiry_time or user.otp_expiry_time < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "status": "error",
                        "message": "OTP has expired",
                        "action": "Please request a new OTP",
                    },
                )

            await self.reset_user_state(user, session, clear_otp=False)
            return user

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error during OTP verification: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "status": "error",
                    "message": "Failed to verify OTP",
                    "action": "Please try again later",
                },
            )

    async def check_user_lockout(
            self,
            user: User,
            session: AsyncSession,
    ) -> None:
        if user.account_status != AccountStatusSchema.LOCKED or not user.last_failed_login:
            return

        lockout_time = user.last_failed_login + timedelta(
            minutes=settings.LOCKOUT_DURATION_MINUTES
        )
        now = datetime.now(timezone.utc)

        if now >= lockout_time:
            await self.reset_user_state(user, session, clear_otp=False)
            logger.info(f"Lockout period ended for user {user.email}")
            return

        remaining_minutes = int((lockout_time - now).total_seconds() / 60)
        logger.warning(f"Attempted login to locked account: {user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": "error",
                "message": "Your account is temporarily locked",
                "action": f"Please try again after {remaining_minutes} minutes",
                "lockout_remaining_minutes": remaining_minutes,
            },
        )

    async def increment_failed_login_attempts(
            self,
            user: User,
            session: AsyncSession,
    ) -> None:
        """Increase failed attempts and lock account if limit is reached."""

        # Increase failed attempts and update last failed time
        user.failed_login_attempts += 1
        user.last_failed_login = datetime.now(timezone.utc)

        # Lock account if too many attempts
        if user.failed_login_attempts >= settings.LOGIN_ATTEMPTS:
            user.account_status = AccountStatusSchema.LOCKED

            # # Try sending lockout email
            # try:
            #     await send_account_lockout_email(user.email, user.last_failed_login)
            #     logger.info(f"Lockout email sent to {user.email}")
            # except Exception as e:
            #     logger.error(f"Email sending failed for {user.email}: {e}")
            #
            # logger.warning(f"User {user.email} locked due to failed logins")

        # Save changes
        await session.commit()
        await session.refresh(user)

auth_service = AuthService()
