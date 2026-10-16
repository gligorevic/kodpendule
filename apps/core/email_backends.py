"""SendGrid's HTTPS API avoids SMTP ports blocked by some hosting plans."""
import base64
import json
from email.utils import parseaddr
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class SendGridAPIBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages or []:
            if not message.recipients():
                continue
            try:
                if not settings.SENDGRID_API_KEY:
                    raise ValueError("SENDGRID_API_KEY is not configured.")
                payload = self.payload(message)
                request = Request(
                    "https://api.sendgrid.com/v3/mail/send",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Authorization": "Bearer " + settings.SENDGRID_API_KEY, "Content-Type": "application/json"},
                    method="POST",
                )
                # Never retry a send after an uncertain response: it could duplicate mail.
                try:
                    with urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
                        if response.status != 202:
                            raise RuntimeError(f"Mail provider returned HTTP {response.status}.")
                except HTTPError as exc:
                    # Do not expose request credentials or message content in logs.
                    raise RuntimeError(f"Mail provider rejected the message (HTTP {exc.code}).") from None
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return sent

    @staticmethod
    def address(value):
        name, email = parseaddr(value)
        return {"email": email, **({"name": name} if name else {})}

    @classmethod
    def payload(cls, message):
        message.message()  # Django validates headers, including newline injection.
        envelope = {field: [cls.address(value) for value in getattr(message, field)] for field in ("to", "cc", "bcc") if getattr(message, field)}
        payload = {
            "personalizations": [envelope],
            "from": cls.address(message.from_email),
            "subject": str(message.subject),
            "content": [{"type": "text/" + message.content_subtype, "value": str(message.body)}],
            "tracking_settings": {"click_tracking": {"enable": False, "enable_text": False}, "open_tracking": {"enable": False}},
        }
        for content, mimetype in getattr(message, "alternatives", []):
            payload["content"].append({"type": mimetype, "value": content})
        if message.reply_to:
            payload["reply_to_list"] = [cls.address(value) for value in message.reply_to]
        if message.extra_headers:
            payload["headers"] = dict(message.extra_headers)
        if message.attachments:
            attachments = []
            for attachment in message.attachments:
                if not isinstance(attachment, tuple):
                    raise ValueError("MIME attachment objects are not supported by this backend.")
                filename, content, mimetype = attachment
                if isinstance(content, str):
                    content = content.encode("utf-8")
                attachments.append({"filename": filename, "type": mimetype, "content": base64.b64encode(content).decode("ascii"), "disposition": "attachment"})
            payload["attachments"] = attachments
        return payload
