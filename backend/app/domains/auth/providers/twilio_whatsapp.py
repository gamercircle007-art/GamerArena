"""Twilio WhatsApp OTP provider — primary signup channel."""

from twilio.rest import Client as TwilioClient

from app.core.config import Settings
from app.core.logging import get_logger
from app.domains.auth.providers.base import OTPChannel, OTPProvider
from app.domains.common.exceptions import DomainError

logger = get_logger(__name__)


class TwilioWhatsAppProvider(OTPProvider):
    """Send OTP via Twilio WhatsApp API (sandbox or production)."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._client: TwilioClient | None = None

    @property
    def channel(self) -> OTPChannel:
        return OTPChannel.WHATSAPP

    def _get_client(self) -> TwilioClient:
        if self._client is None:
            if not self.settings.twilio_account_sid or not self.settings.twilio_auth_token:
                raise DomainError("WhatsApp OTP service is not configured")
            self._client = TwilioClient(
                self.settings.twilio_account_sid,
                self.settings.twilio_auth_token,
            )
        return self._client

    @staticmethod
    def _format_number(phone: str) -> str:
        cleaned = phone.strip()
        if not cleaned.startswith("+"):
            cleaned = f"+{cleaned.lstrip('0')}"
        if not cleaned.startswith("whatsapp:"):
            cleaned = f"whatsapp:{cleaned}"
        return cleaned

    async def send_otp(self, phone_number: str, otp: str, expiry_minutes: int) -> None:
        if not self.settings.twilio_configured:
            if self.settings.is_local or self.settings.use_otp_dev_bypass:
                logger.info(
                    "whatsapp_otp_dev_mode",
                    phone=phone_number,
                    otp=otp,
                    expiry_minutes=expiry_minutes,
                )
                return
            raise DomainError(
                "WhatsApp OTP is not configured. "
                "Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_FROM on the server."
            )

        to_number = self._format_number(phone_number)
        from_number = (self.settings.twilio_whatsapp_from or "").strip()
        if not from_number:
            raise DomainError("TWILIO_WHATSAPP_FROM is not set")
        if not from_number.startswith("whatsapp:"):
            from_number = f"whatsapp:{from_number}"

        brand = (self.settings.app_name or "GamerCircle").replace("-", " ").title()
        body = (
            f"*{brand} Verification*\n\n"
            f"Your one-time password is: *{otp}*\n\n"
            f"This code expires in {expiry_minutes} minutes. "
            f"Do not share it with anyone.\n\n"
            f"If you did not request this, please ignore this message."
        )

        try:
            client = self._get_client()
            client.messages.create(
                body=body,
                from_=from_number,
                to=to_number,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("whatsapp_otp_send_failed", phone=to_number)
            raise DomainError(
                "Failed to send WhatsApp OTP. Check Twilio credentials and sandbox join."
            ) from exc
        logger.info("whatsapp_otp_sent", phone=to_number)