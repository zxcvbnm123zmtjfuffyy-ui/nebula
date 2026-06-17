import logging
import requests
from datetime import datetime
import config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("nebula.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("Nebula")

def send_log_to_webhook(message: str, level: str = "INFO", details: dict = None):
    if not config.LOG_WEBHOOK_URL:
        return
    colors = {"INFO": 0x00bfff, "SUCCESS": 0x00ff00, "WARNING": 0xffcc00, "ERROR": 0xff0000}
    embed = {
        "embeds": [{
            "title": f"📋 Nebula - {level}",
            "description": message,
            "color": colors.get(level, 0x00bfff),
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": "Nebula Monitor"}
        }]
    }
    if details:
        embed["embeds"][0]["fields"] = [
            {"name": k, "value": str(v)[:100], "inline": True}
            for k, v in details.items()
        ]
    try:
        requests.post(config.LOG_WEBHOOK_URL, json=embed, timeout=5)
    except Exception as e:
        logger.error(f"فشل إرسال سجل للويب هوك: {e}")

def log_info(message: str, details: dict = None):
    logger.info(message)
    send_log_to_webhook(message, "INFO", details)

def log_success(message: str, details: dict = None):
    logger.info(f"✅ {message}")
    send_log_to_webhook(f"✅ {message}", "SUCCESS", details)

def log_warning(message: str, details: dict = None):
    logger.warning(f"⚠️ {message}")
    send_log_to_webhook(f"⚠️ {message}", "WARNING", details)

def log_error(message: str, details: dict = None):
    logger.error(f"❌ {message}")
    send_log_to_webhook(f"❌ {message}", "ERROR", details)