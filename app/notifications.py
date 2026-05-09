import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import aiosmtplib

from app.config import settings

logger = logging.getLogger(__name__)


def build_price_drop_email(
    origin: str,
    destination: str,
    departure_date: str,
    old_price: float,
    new_price: float,
    savings: float,
    total_savings: float,
    confirmation_number: str | None,
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Price Drop Alert: {origin} → {destination} (-${savings:.0f}!)"
    msg["From"] = settings.from_email or settings.smtp_username
    msg["To"] = settings.notification_email

    html = f"""
    <html>
    <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background: linear-gradient(135deg, #003366 0%, #0055a5 100%); color: white; padding: 30px; border-radius: 12px 12px 0 0;">
            <h1 style="margin: 0; font-size: 24px;">Price Drop Alert</h1>
            <p style="margin: 8px 0 0; opacity: 0.9; font-size: 16px;">{origin} → {destination}</p>
        </div>

        <div style="background: #f8f9fa; padding: 30px; border: 1px solid #e9ecef; border-top: none;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                <div>
                    <p style="color: #6c757d; margin: 0; font-size: 12px; text-transform: uppercase;">Previous Price</p>
                    <p style="color: #dc3545; margin: 4px 0 0; font-size: 24px; text-decoration: line-through;">${old_price:.2f}</p>
                </div>
                <div>
                    <p style="color: #6c757d; margin: 0; font-size: 12px; text-transform: uppercase;">New Price</p>
                    <p style="color: #28a745; margin: 4px 0 0; font-size: 24px; font-weight: bold;">${new_price:.2f}</p>
                </div>
            </div>

            <div style="background: #d4edda; border: 1px solid #c3e6cb; border-radius: 8px; padding: 16px; text-align: center; margin-bottom: 20px;">
                <p style="color: #155724; margin: 0; font-size: 14px;">You save</p>
                <p style="color: #155724; margin: 4px 0 0; font-size: 32px; font-weight: bold;">${savings:.2f}</p>
                <p style="color: #155724; margin: 4px 0 0; font-size: 13px;">Total savings so far: ${total_savings:.2f}</p>
            </div>

            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; color: #6c757d; font-size: 14px;">Departure</td>
                    <td style="padding: 8px 0; text-align: right; font-size: 14px;">{departure_date}</td>
                </tr>
                {"<tr><td style='padding: 8px 0; color: #6c757d; font-size: 14px;'>Confirmation</td><td style='padding: 8px 0; text-align: right; font-size: 14px;'>" + confirmation_number + "</td></tr>" if confirmation_number else ""}
            </table>

            <div style="margin-top: 24px; text-align: center;">
                <a href="https://www.delta.com/mytrips/"
                   style="background: #003366; color: white; padding: 12px 32px; border-radius: 6px; text-decoration: none; font-weight: 600; display: inline-block;">
                    Rebook on Delta →
                </a>
            </div>
        </div>

        <div style="padding: 16px; text-align: center; color: #6c757d; font-size: 12px; border: 1px solid #e9ecef; border-top: none; border-radius: 0 0 12px 12px;">
            Delta Flight Tracker · Automatic price monitoring
        </div>
    </body>
    </html>
    """

    text = f"""
Price Drop Alert: {origin} → {destination}

Previous Price: ${old_price:.2f}
New Price: ${new_price:.2f}
You Save: ${savings:.2f}
Total Savings: ${total_savings:.2f}

Departure: {departure_date}
{"Confirmation: " + confirmation_number if confirmation_number else ""}

Rebook at: https://www.delta.com/mytrips/
    """

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))
    return msg


async def send_price_drop_notification(
    origin: str,
    destination: str,
    departure_date: str,
    old_price: float,
    new_price: float,
    savings: float,
    total_savings: float,
    confirmation_number: str | None = None,
) -> bool:
    if not settings.smtp_username or not settings.smtp_password:
        logger.warning(
            "SMTP not configured. Would have sent price drop alert: "
            "%s→%s dropped $%.2f→$%.2f (save $%.2f)",
            origin,
            destination,
            old_price,
            new_price,
            savings,
        )
        return False

    msg = build_price_drop_email(
        origin=origin,
        destination=destination,
        departure_date=departure_date,
        old_price=old_price,
        new_price=new_price,
        savings=savings,
        total_savings=total_savings,
        confirmation_number=confirmation_number,
    )

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            start_tls=True,
            username=settings.smtp_username,
            password=settings.smtp_password,
        )
        logger.info("Price drop email sent for %s→%s", origin, destination)
        return True
    except Exception:
        logger.exception("Failed to send price drop email")
        return False


def send_price_drop_notification_sync(
    origin: str,
    destination: str,
    departure_date: str,
    old_price: float,
    new_price: float,
    savings: float,
    total_savings: float,
    confirmation_number: str | None = None,
) -> bool:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    send_price_drop_notification(
                        origin,
                        destination,
                        departure_date,
                        old_price,
                        new_price,
                        savings,
                        total_savings,
                        confirmation_number,
                    ),
                )
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(
                send_price_drop_notification(
                    origin,
                    destination,
                    departure_date,
                    old_price,
                    new_price,
                    savings,
                    total_savings,
                    confirmation_number,
                )
            )
    except Exception:
        logger.exception("Failed to send notification synchronously")
        return False
