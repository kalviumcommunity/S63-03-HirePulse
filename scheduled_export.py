"""Daily scheduled export entry point with an immediate test mode."""

from __future__ import annotations

import logging
from datetime import datetime

from streamlit_export_integration import generate_current_report


LOGGER = logging.getLogger("scheduled_export")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def scheduled_export():
    """Run one export and log success or a useful failure."""
    started = datetime.now().astimezone().isoformat()
    try:
        report_dir = generate_current_report()
        LOGGER.info("export_success timestamp=%s report_dir=%s", started, report_dir)
        return report_dir
    except Exception as error:
        LOGGER.exception("export_failure timestamp=%s error=%s", started, error)
        raise


def run_scheduler():
    import schedule
    import time

    schedule.every().day.at("17:00").do(scheduled_export)
    LOGGER.info("scheduled_export_ready time=17:00")
    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    import sys
    if "--once" in sys.argv:
        scheduled_export()
    else:
        run_scheduler()