"""Run configuration: credentials come from the environment, never from code."""
import os
from dataclasses import dataclass

BASE_URL = "https://www.saucedemo.com"


class ConfigError(Exception):
    """Raised when required configuration is missing or invalid."""


@dataclass(frozen=True)
class Config:
    username: str
    password: str
    base_url: str = BASE_URL
    # Upper bound for any single wait. Waits return as soon as the page is
    # ready, so a generous value costs nothing on a fast run and lets the slow
    # performance_glitch_user through without a code change.
    timeout_ms: int = 30_000
    headless: bool = True
    slow_mo_ms: int = 0  # demo only: slows each action so a recording is watchable
    video_dir: str = ""  # demo only: record a video of the run into this folder

    @classmethod
    def from_env(cls, headless: bool = True, slow_mo_ms: int = 0, video_dir: str = "") -> "Config":
        username = os.environ.get("SAUCE_USERNAME")
        password = os.environ.get("SAUCE_PASSWORD")
        missing = [n for n, v in (("SAUCE_USERNAME", username), ("SAUCE_PASSWORD", password)) if not v]
        if missing:
            raise ConfigError("Missing environment variable(s): " + ", ".join(missing))
        return cls(
            username=username,
            password=password,
            base_url=os.environ.get("SAUCE_BASE_URL", BASE_URL),
            timeout_ms=int(os.environ.get("SAUCE_TIMEOUT_MS", "30000")),
            headless=headless,
            slow_mo_ms=slow_mo_ms,
            video_dir=video_dir,
        )
