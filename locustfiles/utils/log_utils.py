# locustfiles/utils/log_utils.py
import logging
import os
from typing import Optional

def get_logger(name: str = "locust") -> logging.Logger:
    """Konfigüre edilmiş bir logger instance'ı döner."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
        )
        logger.addHandler(handler)
    
    logger.setLevel(level)
    return logger

def log_test_summary(
    environment, 
    logger: Optional[logging.Logger] = None, 
    latency_threshold_ms: float = 200.0, 
    failure_threshold_ratio: float = 0.05
):
    """
    Locust test istatistiklerini formatlı bir şekilde loglar.
    
    Args:
        environment: Locust environment nesnesi.
        logger: Kullanılacak logger (None ise default logger).
        latency_threshold_ms: Uyarı verilecek ortalama gecikme eşiği.
        failure_threshold_ratio: Uyarı verilecek hata oranı eşiği (0.05 = %5).
    """
    logger = logger or get_logger("locust")
    stats = environment.stats.total

    logger.info("=" * 60)
    logger.info("LOCUST TEST SUMMARY")
    logger.info("=" * 60)

    logger.info(f"Total Request Count: {stats.num_requests}")
    logger.info(f"Average Response Time: {stats.avg_response_time:.2f} ms")
    logger.info(f"Max Response Time: {stats.max_response_time:.2f} ms")
    logger.info(f"Failed Request Ratio: {stats.fail_ratio:.2%}")
    logger.info(f"Requests Per Second (RPS): {stats.total_rps:.2f}")

    logger.info("=" * 60)
    logger.info("Performance by Endpoint:")

    for stat in environment.stats.entries.values():
        logger.info(
            f"- Endpoint: {stat.name} [{stat.method}]\n"
            f"  Requests: {stat.num_requests} | Failures: {stat.num_failures}\n"
            f"  Response Time (ms): Avg: {stat.avg_response_time:.2f}, Min: {stat.min_response_time:.2f}, Max: {stat.max_response_time:.2f}"
        )
        logger.info("-" * 40)

    # Threshold Check
    has_issue = False
    if stats.avg_response_time > latency_threshold_ms:
        logger.warning(f"⚠️ CRITICAL: Average response time exceeds {latency_threshold_ms}ms! ({stats.avg_response_time:.2f} ms)")
        has_issue = True

    if stats.fail_ratio > failure_threshold_ratio:
        logger.warning(f"⚠️ CRITICAL: Failure ratio exceeds {failure_threshold_ratio:.0%}! ({stats.fail_ratio:.2%})")
        has_issue = True

    if not has_issue:
        logger.info("✅ Test Successful: Performance criteria met.")