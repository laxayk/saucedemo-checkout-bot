import argparse
import logging
import sys
from pathlib import Path

from .bot import run
from .config import Config, ConfigError


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="saucebot", description="Saucedemo checkout bot")
    ap.add_argument("--input", type=Path, default=Path("input.json"))
    ap.add_argument("--out", type=Path, default=Path("outputs"))
    ap.add_argument("--headed", action="store_true", help="show the browser window")
    ap.add_argument("--demo-video", type=Path, metavar="DIR", help="slow down and record a video into DIR")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        config = Config.from_env(
            headless=not args.headed,
            slow_mo_ms=600 if args.demo_video else 0,
            video_dir=str(args.demo_video or ""),
        )
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    result = run(config, args.input, args.out)
    print(f"status={result.status}" + (f" error={result.error}" if result.error else ""))
    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
