"""Notification stubs — Slack / email with logging fallback."""

import logging

import yaml

from engine.context import get_config_path

logger = logging.getLogger(__name__)


def notify(message: str, config_path: str | None = None) -> None:
    """Send a notification via the configured method, or log if disabled."""
    if config_path is None:
        config_path = str(get_config_path())
    with open(config_path) as f:
        config = yaml.safe_load(f)

    notif = config.get("notifications", {})

    if not notif.get("enabled", False):
        logger.info("Notification (disabled): %s", message)
        return

    method = notif.get("method", "slack")

    if method == "slack":
        _send_slack(message, notif.get("slack_webhook_url", ""))
    elif method == "email":
        _send_email(message, notif.get("email_to", ""))
    else:
        logger.warning("Unknown notification method '%s', falling back to log", method)
        logger.info("Notification: %s", message)


def _send_slack(message: str, webhook_url: str) -> None:
    """Send a Slack webhook notification. Stub — logs instead of sending."""
    if not webhook_url:
        logger.warning("Slack webhook URL not configured, logging instead")
        logger.info("Slack notification: %s", message)
        return
    # Real implementation would POST to webhook_url
    logger.info("Slack notification sent: %s", message)


def _send_email(message: str, to_address: str) -> None:
    """Send an email notification. Stub — logs instead of sending."""
    if not to_address:
        logger.warning("Email address not configured, logging instead")
        logger.info("Email notification: %s", message)
        return
    # Real implementation would use smtplib
    logger.info("Email notification sent to %s: %s", to_address, message)
