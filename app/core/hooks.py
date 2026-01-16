"""
Locust ReportPortal Hook
This file is automatically loaded by Locust and starts ReportPortal listener.
"""
import os
import logging
from locust import events

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Adds ReportPortal listener when Locust is initialized."""
    logger.info("🔧 ReportPortal Hook called")

    # Check RP_ENABLED
    rp_enabled = os.getenv("RP_ENABLED", "true").lower()
    if rp_enabled == "false":
        logger.info("⚠️  ReportPortal disabled (RP_ENABLED=false)")
        return

    rp_endpoint = os.getenv("RP_ENDPOINT")
    rp_project = os.getenv("RP_PROJECT")
    rp_token = os.getenv("RP_TOKEN")

    logger.info(f"RP Config: endpoint={rp_endpoint}, project={rp_project}, token={'***' if rp_token else None}")

    if rp_endpoint and rp_project and rp_token:
        try:
            from app.core.rp_listener import ReportPortalListener
            ReportPortalListener(environment)
            logger.info("✅ ReportPortal Listener initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ReportPortal: {e}", exc_info=True)
    else:
        logger.warning("⚠️  ReportPortal config missing, listener disabled")
