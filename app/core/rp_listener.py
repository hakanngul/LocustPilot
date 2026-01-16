import logging

from datetime import datetime
from reportportal_client import RPClient
from reportportal_client.helpers import timestamp
import gevent
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# DETAILED_LOG removed, using settings.rp_detailed_log


class ReportPortalListener:
    def __init__(self, env):
        self.env = env
        self.rp_client = None
        self.launch_uuid = None
        self.test_item_uuid = None
        self.running = False
        self.last_stats = {}
        self.start_time = None

        # Load typed settings
        from app.core.settings import settings
        self.settings = settings

        self.rp_endpoint = settings.rp_endpoint
        self.rp_project = settings.rp_project
        self.rp_token = settings.rp_token
        self.rp_launch_name = settings.rp_launch_name
        self.rp_launch_desc = settings.rp_launch_desc
        
        logger.info(
            f"🔧 ReportPortal Listener init: {self.rp_endpoint}/{self.rp_project}"
        )

        if not settings.rp_enabled:
            logger.warning("ReportPortal config missing or incomplete. Listener disabled.")
            return

        self.env.events.test_start.add_listener(self.on_test_start)
        self.env.events.test_stop.add_listener(self.on_test_stop)
        self.env.events.request.add_listener(self.on_request)
        # Locust 2.x uses 'request' event for both success and failure
        logger.info("✅ Event listeners registered")

    def clean_http_name(self, name):
        pattern = r"^(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+"

        return re.sub(pattern, "", name)

    def on_test_start(self, **kwargs):
        logger.info("🚀 Test starting, initializing ReportPortal...")
        try:
            # Get host info from settings or locust env
            effective_host = self.settings.rp_test_host or self.env.host or "Unknown"
            host_source = self.settings.rp_host_source
            locustfile = self.settings.rp_locustfile

            # Update settings if host is found in env but not in settings (dynamic runtime update)
            # useful if locust user sets it
            if not self.settings.rp_test_host and self.env.host:
                effective_host = self.env.host

            self.rp_client = RPClient(
                endpoint=self.rp_endpoint,
                project=self.rp_project,
                api_key=self.rp_token,
            )

            # Start upload thread
            self.rp_client.start()
            logger.info("✅ RPClient started")

            self.launch_uuid = self.rp_client.start_launch(
                name=self.rp_launch_name,
                start_time=timestamp(),
                description=self.rp_launch_desc,
            )
            logger.info(f"✅ Launch started: {self.launch_uuid}")

            self.test_item_uuid = self.rp_client.start_test_item(
                name="Load Test Execution",
                start_time=timestamp(),
                item_type="STEP",
                description=f"Host: {effective_host} ({host_source})",
            )
            logger.info(f"✅ Test item started: {self.test_item_uuid}")

            # Save start time
            self.start_time = datetime.now()

            # Log test start with detailed info
            self.rp_client.log(
                time=timestamp(),
                message=f"🚀 Load Test Started\n{'=' * 50}\nLocustfile: {locustfile}\nHost: {effective_host}\nHost Source: {host_source}\nLaunch: {self.rp_launch_name}\n{'=' * 50}",
                level="INFO",
                item_id=self.test_item_uuid,
            )

            # Start periodic stats logging
            self.running = True
            gevent.spawn(self._periodic_stats_logger)

        except Exception as e:
            logger.error(f"❌ Failed to start ReportPortal: {e}", exc_info=True)
            
    def _periodic_stats_logger(self):
        """Log endpoint stats every 30 seconds"""
        while self.running:
            gevent.sleep(30)
            if self.running and self.rp_client and self.test_item_uuid:
                try:
                    # Endpoint bazlı özet
                    lines = ["📊 Endpoint Statistics"]
                    lines.append("=" * 80)
                    lines.append(
                        f"{'Method':<8} {'Name':<40} {'Reqs':<8} {'Fails':<8} {'Avg(ms)':<10} {'RPS':<8}"
                    )
                    lines.append("-" * 80)

                    for stat in self.env.stats.entries.values():
                        if stat.num_requests > 0:
                            lines.append(
                                f"{stat.method:<8} {stat.name[:40]:<40} "
                                f"{stat.num_requests:<8} {stat.num_failures:<8} "
                                f"{stat.avg_response_time:<10.0f} {stat.current_rps:<8.1f}"
                            )

                    # Total
                    total = self.env.stats.total
                    lines.append("-" * 80)
                    lines.append(
                        f"{'TOTAL':<8} {'':<40} "
                        f"{total.num_requests:<8} {total.num_failures:<8} "
                        f"{total.avg_response_time:<10.0f} {total.total_rps:<8.1f}"
                    )
                    lines.append("=" * 80)

                    self.rp_client.log(
                        time=timestamp(),
                        message="\n".join(lines),
                        level="INFO",
                        item_id=self.test_item_uuid,
                    )
                except Exception as e:
                    logger.error(f"Failed to log periodic stats: {e}")




    def on_request(
        self,
        request_type,
        name,
        response_time,
        response_length,
        exception=None,
        response=None,
        **kwargs,
    ):
        # Sadece unique hataları logla
        # exception ve response None olabilir, güvenli kontrol
        has_exception = exception is not None
        has_manual_failure = False

        if response is not None:
            has_manual_failure = (
                hasattr(response, "_manual_result") and response._manual_result is False
            )

        if has_exception or has_manual_failure:
            error_key = f"{request_type}:{name}"

            # İlk kez görülen hata mı?
            if error_key not in self.last_stats:
                self.last_stats[error_key] = {"count": 0, "logged": False}

            self.last_stats[error_key]["count"] += 1

            # İlk hatayı logla
            if (
                not self.last_stats[error_key]["logged"]
                and self.rp_client
                and self.test_item_uuid
            ):
                try:
                    if has_exception:
                        error_msg = str(exception)
                    else:
                        error_msg = getattr(
                            response, "_manual_result_msg", "Manual failure"
                        )

                    self.rp_client.log(
                        time=timestamp(),
                        message=f"❌ First Failure: {request_type} {name}\nError: {error_msg}",
                        level="ERROR",
                        item_id=self.test_item_uuid,
                    )
                    self.last_stats[error_key]["logged"] = True
                except Exception as e:
                    logger.error(f"Failed to log failure: {e}")

    def on_test_stop(self, **kwargs):
        logger.info("🛑 Test stopping, finishing ReportPortal...")
        self.running = False

        if not self.rp_client:
            return

        try:
            total = self.env.stats.total
            end_time = datetime.now()
            duration = (
                (end_time - self.start_time).total_seconds() if self.start_time else 0
            )

            effective_host = self.settings.rp_test_host or self.env.host or "Unknown"
            locustfile = self.settings.rp_locustfile

            # Header
            lines = ["📊 Locust Test Report"]
            lines.append("=" * 80)
            lines.append(
                f"**During:** {self.start_time.strftime('%m/%d/%Y, %I:%M:%S %p')} - {end_time.strftime('%m/%d/%Y, %I:%M:%S %p')} ({int(duration)} seconds)"
            )
            lines.append(f"**Target Host:** {effective_host}")
            lines.append(f"**Script:** {locustfile}")
            lines.append("")

            # Request Statistics Table
            lines.append("### Request Statistics")
            lines.append("")
            lines.append(
                "| Type | Name | # Reqs | # Fails | Avg(ms) | Min(ms) | Max(ms) | RPS | Fail/s |"
            )
            lines.append(
                "|------|------|--------|---------|---------|---------|---------|-----|--------|"
            )

            for stat in self.env.stats.entries.values():
                if stat.num_requests > 0:
                    fail_per_sec = stat.num_failures / duration if duration > 0 else 0
                    sort_name = self.clean_http_name(stat.name)
                    lines.append(
                        f"| {stat.method} | {sort_name} | "
                        f"{stat.num_requests} | {stat.num_failures} | "
                        f"{stat.avg_response_time:.2f} | {stat.min_response_time or 0:.0f} | "
                        f"{stat.max_response_time:.0f} | {stat.total_rps:.2f} | {fail_per_sec:.2f} |"
                    )

            # Aggregated
            total_fail_per_sec = total.num_failures / duration if duration > 0 else 0
            lines.append(
                f"| **Aggregated** | | "
                f"**{total.num_requests}** | **{total.num_failures}** | "
                f"**{total.avg_response_time:.2f}** | **{total.min_response_time or 0:.0f}** | "
                f"**{total.max_response_time:.0f}** | **{total.total_rps:.2f}** | **{total_fail_per_sec:.2f}** |"
            )
            lines.append("")

            # Response Time Percentiles Table
            lines.append("### Response Time Statistics")
            lines.append("")
            lines.append(
                "| Method | Name | 50% | 60% | 70% | 80% | 90% | 95% | 99% | 100% |"
            )
            lines.append(
                "|--------|------|-----|-----|-----|-----|-----|-----|-----|------|"
            )

            for stat in self.env.stats.entries.values():
                if stat.num_requests > 0:
                    name_short = self.clean_http_name(stat.name)

                    lines.append(
                        f"| {stat.method} | {name_short} | "
                        f"{stat.get_response_time_percentile(0.50) or 0:.0f} | "
                        f"{stat.get_response_time_percentile(0.60) or 0:.0f} | "
                        f"{stat.get_response_time_percentile(0.70) or 0:.0f} | "
                        f"{stat.get_response_time_percentile(0.80) or 0:.0f} | "
                        f"{stat.get_response_time_percentile(0.90) or 0:.0f} | "
                        f"{stat.get_response_time_percentile(0.95) or 0:.0f} | "
                        f"{stat.get_response_time_percentile(0.99) or 0:.0f} | "
                        f"{stat.max_response_time or 0:.0f} |"
                    )

            # Aggregated percentiles
            lines.append(
                f"| **Aggregated** | | "
                f"**{total.get_response_time_percentile(0.50) or 0:.0f}** | "
                f"**{total.get_response_time_percentile(0.60) or 0:.0f}** | "
                f"**{total.get_response_time_percentile(0.70) or 0:.0f}** | "
                f"**{total.get_response_time_percentile(0.80) or 0:.0f}** | "
                f"**{total.get_response_time_percentile(0.90) or 0:.0f}** | "
                f"**{total.get_response_time_percentile(0.95) or 0:.0f}** | "
                f"**{total.get_response_time_percentile(0.99) or 0:.0f}** | "
                f"**{total.max_response_time or 0:.0f}** |"
            )
            lines.append("")
            lines.append("=" * 80)
            lines.append(f"**Success Rate:** {(1 - total.fail_ratio) * 100:.1f}%")

            # Error summary
            if self.last_stats:
                lines.append("")
                lines.append("### ❌ Error Summary")
                for key, data in self.last_stats.items():
                    lines.append(f"- **{key}:** {data['count']} failures")

            # Detailed report similar to log_test_summary
            lines.append("")
            lines.append("=" * 80)
            lines.append("### 📊 Detailed Performance Report")
            lines.append("")
            lines.append(f"**Total Requests:** {total.num_requests}")
            lines.append(f"**Average Response Time:** {total.avg_response_time:.2f} ms")
            lines.append(f"**Max Response Time:** {total.max_response_time:.2f} ms")
            lines.append(f"**Failed Request Ratio:** {total.fail_ratio:.2%}")
            lines.append(f"**Requests Per Second (RPS):** {total.total_rps:.2f}")
            lines.append("")


            if self.settings.rp_detailed_log:
                # Detailed by endpoint
                lines.append("**Endpoint Performance:**")
                for stat in self.env.stats.entries.values():
                    if stat.num_requests > 0:
                        lines.append("")
                    lines.append(
                        f"- **Endpoint:** {stat.method} {self.clean_http_name(stat.name)}"
                    )
                    lines.append(f"  - Total Requests: {stat.num_requests}")
                    lines.append(f"  - Failed Requests: {stat.num_failures}")
                    lines.append(
                        f"  - Avg Response Time: {stat.avg_response_time:.2f} ms"
                    )
                    lines.append(
                        f"  - Min Response Time: {stat.min_response_time:.2f} ms"
                    )
                    lines.append(
                        f"  - Max Response Time: {stat.max_response_time:.2f} ms"
                    )
                    lines.append(
                        f"  - Avg Response Size: {stat.avg_content_length:.2f} bytes"
                    )

            # Performance uyarıları
            lines.append("")
            lines.append("**Performance Warnings:**")
            has_issue = False
            if total.avg_response_time > 200:
                lines.append(
                    f"⚠️  Average response time exceeds 200ms! (Actual: {total.avg_response_time:.2f} ms)"
                )
                has_issue = True
            if total.fail_ratio > 0.05:
                lines.append(
                    f"⚠️  Failed request ratio exceeds 5%! (Actual: {total.fail_ratio:.2%})"
                )
                has_issue = True
            if not has_issue:
                lines.append(
                    "✅ No performance issues detected. Failed request ratio is below 5%."
                )

            self.rp_client.log(
                time=timestamp(),
                message="\n".join(lines),
                level="INFO",
                item_id=self.test_item_uuid,
            )
            logger.info("✅ Summary logged")

            # Success rate threshold: 75%
            success_rate = (1 - total.fail_ratio) * 100
            status = "PASSED" if success_rate >= 75 else "FAILED"

            self.rp_client.finish_test_item(
                item_id=self.test_item_uuid, end_time=timestamp(), status=status
            )
            logger.info(f"✅ Test item finished: {status}")

            self.rp_client.finish_launch(end_time=timestamp())
            logger.info("✅ Launch finished")

            # Ensure all pending requests are processed
            self.rp_client.terminate()
            logger.info("✅ ReportPortal terminated successfully")
        except Exception as e:
            logger.error(f"❌ Failed to finish ReportPortal: {e}", exc_info=True)
