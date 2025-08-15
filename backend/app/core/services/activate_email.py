
from backend.app.core.config import settings
from backend.app.core.emails.base import EmailTemplate



class AccountActivationEmail(EmailTemplate):
    template_name = "account_activation.html"
    template_name_plain = "account_activation.txt"
    subject = "Activate Your Account"


async def send_activation_email(email: str, token: str) -> None:
    activation_url = (
        f"{settings.API_BASE_URL}/auth/activate/{token}"
    )

    context = {
        "activation_url": activation_url,
        "expiry_time": settings.ACTIVATION_TOKEN_EXPIRATION_MINUTES,
        "support_email": settings.SUPPORT_EMAIL,
    }
    await AccountActivationEmail.send_email(email_to=email, context=context)