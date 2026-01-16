
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, computed_field

class Settings(BaseSettings):
    # Base configuration
    base_dir: Path = Field(default_factory=lambda: Path(__file__).parent.parent.parent.resolve())
    
    # Locust Configuration
    locustfiles_subdir: str = Field(default="libs", alias="LOCUSTFILES_SUBDIR")
    locust_target_host: Optional[str] = Field(default=None, alias="LOCUST_TARGET_HOST")
    locust_host: Optional[str] = Field(default="https://localhost:8080", alias="LOCUST_HOST")
    locust_users: int = Field(default=10, alias="LOCUST_USERS")
    locust_spawn_rate: float = Field(default=2.0, alias="LOCUST_SPAWN_RATE")
    locust_run_time: str = Field(default="10s", alias="LOCUST_RUN_TIME")
    locust_csv_prefix: str = Field(default="stats", alias="LOCUST_CSV_PREFIX")
    locust_html_report: bool = Field(default=True, alias="LOCUST_HTML_REPORT")
    locust_csv_full_history: bool = Field(default=True, alias="LOCUST_CSV_FULL_HISTORY")
    
    # ReportPortal Configuration
    rp_endpoint: Optional[str] = Field(default=None, alias="RP_ENDPOINT")
    rp_project: Optional[str] = Field(default=None, alias="RP_PROJECT")
    rp_token: Optional[str] = Field(default=None, alias="RP_TOKEN")
    rp_launch_name: str = Field(default="Locust Load Test", alias="RP_LAUNCH_NAME")
    rp_launch_desc: str = Field(default="Load Test from Locust", alias="RP_DESCRIPTION")
    rp_test_host: Optional[str] = Field(default=None, alias="RP_TEST_HOST")
    rp_host_source: str = Field(default="unknown", alias="RP_HOST_SOURCE")
    rp_locustfile: str = Field(default="Unknown", alias="RP_LOCUSTFILE")
    rp_detailed_log: bool = Field(default=False, alias="RP_DETAILED_LOG")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @computed_field
    def runs_dir(self) -> Path:
        val = os.getenv("RUNS_DIR", "runs")
        p = Path(val)
        if not p.is_absolute():
            return self.base_dir / p
        return p.resolve()

    @computed_field
    def locustfiles_dir(self) -> Path:
        val = os.getenv("LOCUSTFILES_DIR", "locustfiles")
        p = Path(val)
        if not p.is_absolute():
            return self.base_dir / p
        return p.resolve()
        
    @property
    def rp_enabled(self) -> bool:
        return all([self.rp_endpoint, self.rp_project, self.rp_token])

settings = Settings()
