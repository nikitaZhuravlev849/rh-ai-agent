import logging
from typing import Optional
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
from app.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None and settings.SENDGRID_API_KEY:
            self._client = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
        return self._client

    async def send_email(
        self,
        to_email: str,
        to_name: Optional[str],
        subject: str,
        body: str,
    ) -> bool:
        if not settings.SENDGRID_API_KEY:
            logger.warning(f"[MOCK EMAIL] To: {to_email} | Subject: {subject}")
            logger.info(f"[MOCK EMAIL BODY]\n{body[:200]}...")
            return True

        try:
            message = Mail(
                from_email=Email(settings.EMAIL_FROM, settings.EMAIL_FROM_NAME),
                to_emails=To(to_email, to_name or ""),
                subject=subject,
                plain_text_content=Content("text/plain", body),
            )
            response = self.client.client.mail.send.post(request_body=message.get())
            success = response.status_code in (200, 202)
            if success:
                logger.info(f"Email sent to {to_email}: {response.status_code}")
            else:
                logger.error(f"Email failed to {to_email}: {response.status_code} {response.body}")
            return success
        except Exception as e:
            logger.error(f"SendGrid error for {to_email}: {e}")
            return False

    async def check_delivery_status(self, message_id: str) -> Optional[str]:
        if not settings.SENDGRID_API_KEY:
            return "delivered"
        try:
            response = self.client.client.messages._(message_id).get()
            data = response.to_dict()
            events = data.get("messages", [{}])[0].get("events", [])
            if events:
                return events[-1].get("event_name", "unknown")
        except Exception as e:
            logger.error(f"Status check error for {message_id}: {e}")
        return None
