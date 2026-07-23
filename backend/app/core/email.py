import smtplib
from email.message import EmailMessage

from app.core.config import settings


def is_email_configured() -> bool:
    return all(
        [
            settings.SMTP_HOST,
            settings.SMTP_USERNAME,
            settings.SMTP_PASSWORD,
            settings.EMAIL_FROM,
        ]
    )


def send_email(
    *,
    to_email: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
) -> bool:
    if not is_email_configured():
        print(
            "Email is not configured. "
            "Set SMTP_HOST, SMTP_USERNAME, SMTP_PASSWORD, and EMAIL_FROM."
        )
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{settings.EMAIL_FROM_NAME} <{settings.EMAIL_FROM}>"
    message["To"] = to_email

    message.set_content(text_body)

    if html_body:
        message.add_alternative(html_body, subtype="html")

    smtp_password = settings.SMTP_PASSWORD.get_secret_value()

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_USE_TLS:
            server.starttls()

        server.login(settings.SMTP_USERNAME, smtp_password)
        server.send_message(message)

    return True


def send_verification_email(*, to_email: str, verification_url: str) -> bool:
    subject = "Verify your DocuMind AI account"

    text_body = f"""
Welcome to DocuMind AI.

Please verify your email address by opening this link:

{verification_url}

This link will expire soon.

If you did not create a DocuMind AI account, you can ignore this email.
""".strip()

    html_body = f"""
<!doctype html>
<html>
  <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #1f2933;">
    <h2>Verify your DocuMind AI account</h2>

    <p>Welcome to DocuMind AI.</p>

    <p>Please verify your email address by clicking the button below.</p>

    <p>
      <a href="{verification_url}"
         style="display:inline-block;padding:10px 16px;background:#1f2933;color:#ffffff;text-decoration:none;border-radius:6px;">
        Verify email
      </a>
    </p>

    <p style="font-size: 13px; color: #6b7280;">
      If the button does not work, copy and paste this link into your browser:
      <br />
      {verification_url}
    </p>

    <p style="font-size: 13px; color: #6b7280;">
      If you did not create a DocuMind AI account, you can ignore this email.
    </p>
  </body>
</html>
""".strip()

    return send_email(
        to_email=to_email,
        subject=subject,
        text_body=text_body,
        html_body=html_body,
    )