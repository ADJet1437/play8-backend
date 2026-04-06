import logging
from urllib.parse import urlparse

import resend

from src.core.config import FROM_EMAIL, GOOGLE_REDIRECT_URI, RESEND_API_KEY

logger = logging.getLogger(__name__)

# Derive frontend origin from GOOGLE_REDIRECT_URI (e.g. "http://localhost:5173/auth/google/callback" → "http://localhost:5173")
_parsed = urlparse(GOOGLE_REDIRECT_URI or "http://localhost:5173")
FRONTEND_ORIGIN = f"{_parsed.scheme}://{_parsed.netloc}"


def _get_client() -> resend.Emails:
    resend.api_key = RESEND_API_KEY
    return resend.Emails


def send_verification_email(to_email: str, name: str, token: str) -> None:
    verify_url = f"{FRONTEND_ORIGIN}/auth/verify-email?token={token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto">
      <h2 style="color:#4f46e5">Verify your email</h2>
      <p>Hi {name or 'there'},</p>
      <p>Click the button below to verify your email address and activate your Play8 account.</p>
      <a href="{verify_url}"
         style="display:inline-block;background:#4f46e5;color:#fff;padding:12px 24px;
                border-radius:6px;text-decoration:none;font-weight:600;margin:16px 0">
        Verify Email
      </a>
      <p style="color:#6b7280;font-size:13px">
        This link expires in 24 hours. If you didn't create a Play8 account, ignore this email.
      </p>
    </div>
    """
    try:
        _get_client().send({
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Verify your Play8 email",
            "html": html,
        })
    except Exception:
        logger.exception("Failed to send verification email to %s", to_email)
        raise


def send_welcome_email(to_email: str, name: str) -> None:
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto">
      <h2 style="color:#4f46e5">Welcome to Play8, {name or 'there'}!</h2>
      <p>Your account is ready. Start booking a ball machine or chat with your AI training assistant.</p>
      <a href="{FRONTEND_ORIGIN}"
         style="display:inline-block;background:#4f46e5;color:#fff;padding:12px 24px;
                border-radius:6px;text-decoration:none;font-weight:600;margin:16px 0">
        Get Started
      </a>
      <p style="color:#6b7280;font-size:13px">See you on the court!</p>
    </div>
    """
    try:
        _get_client().send({
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Welcome to Play8!",
            "html": html,
        })
    except Exception:
        logger.exception("Failed to send welcome email to %s", to_email)
        # Don't re-raise — welcome email failure should not block login


def send_booking_confirmation_email(
    to_email: str,
    name: str,
    machine_name: str,
    machine_location: str,
    start_time: str,
    end_time: str,
    duration_minutes: int,
    amount_sek: float,
) -> None:
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto">
      <h2 style="color:#4f46e5">Booking Confirmed!</h2>
      <p>Hi {name or 'there'}, your session is booked. See you on the court!</p>

      <div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:20px;margin:20px 0">
        <table style="width:100%;border-collapse:collapse;font-size:14px">
          <tr>
            <td style="color:#6b7280;padding:6px 0;width:40%">Machine</td>
            <td style="color:#111827;font-weight:600">{machine_name}</td>
          </tr>
          <tr>
            <td style="color:#6b7280;padding:6px 0">Location</td>
            <td style="color:#111827;font-weight:600">{machine_location}</td>
          </tr>
          <tr>
            <td style="color:#6b7280;padding:6px 0">Date</td>
            <td style="color:#111827;font-weight:600">{start_time}</td>
          </tr>
          <tr>
            <td style="color:#6b7280;padding:6px 0">End time</td>
            <td style="color:#111827;font-weight:600">{end_time}</td>
          </tr>
          <tr>
            <td style="color:#6b7280;padding:6px 0">Duration</td>
            <td style="color:#111827;font-weight:600">{duration_minutes} min</td>
          </tr>
          <tr>
            <td style="color:#6b7280;padding:6px 0">Amount paid</td>
            <td style="color:#111827;font-weight:600">{amount_sek:.0f} SEK</td>
          </tr>
        </table>
      </div>

    </div>
    """
    try:
        _get_client().send({
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": f"Booking confirmed — {machine_name}, {start_time}",
            "html": html,
        })
    except Exception:
        logger.exception("Failed to send booking confirmation email to %s", to_email)


def send_password_reset_email(to_email: str, name: str, token: str) -> None:
    reset_url = f"{FRONTEND_ORIGIN}/auth/reset-password?token={token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:480px;margin:0 auto">
      <h2 style="color:#4f46e5">Reset your password</h2>
      <p>Hi {name or 'there'},</p>
      <p>We received a request to reset your Play8 password. Click the button below to choose a new one.</p>
      <a href="{reset_url}"
         style="display:inline-block;background:#4f46e5;color:#fff;padding:12px 24px;
                border-radius:6px;text-decoration:none;font-weight:600;margin:16px 0">
        Reset Password
      </a>
      <p style="color:#6b7280;font-size:13px">
        This link expires in 1 hour. If you didn't request a password reset, you can safely ignore this email.
      </p>
    </div>
    """
    try:
        _get_client().send({
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "Reset your Play8 password",
            "html": html,
        })
    except Exception:
        logger.exception("Failed to send password reset email to %s", to_email)
        raise
