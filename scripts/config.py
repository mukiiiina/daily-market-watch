#!/usr/bin/env python3
"""User preferences and configuration manager."""

import argparse
import json
import sys
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "daily-market-watch"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "morning_push": "0915",
    "evening_push": "1530",
    "detail_level": "detailed",  # concise | detailed
    "alert_mode": "enabled",     # enabled | disabled
    "index_volatility_threshold": 1.0,
    "lark_webhook": "",
}


def ensure_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    ensure_dir()
    if not CONFIG_FILE.exists():
        return dict(DEFAULTS)
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Merge with defaults for missing keys
    for k, v in DEFAULTS.items():
        if k not in data:
            data[k] = v
    return data


def save_config(data: dict):
    ensure_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cmd_get(args: argparse.Namespace) -> int:
    data = load_config()
    val = data.get(args.key)
    print(json.dumps({args.key: val}, ensure_ascii=False))
    return 0


def cmd_set(args: argparse.Namespace) -> int:
    data = load_config()
    # Try to infer type
    raw = args.value
    if raw.lower() in ("true", "false"):
        data[args.key] = raw.lower() == "true"
    else:
        try:
            data[args.key] = int(raw)
        except ValueError:
            try:
                data[args.key] = float(raw)
            except ValueError:
                data[args.key] = raw
    save_config(data)
    print(json.dumps({"ok": True, args.key: data[args.key]}, ensure_ascii=False))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    data = load_config()
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        for k, v in data.items():
            print(f"{k} = {v}")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description="Configuration manager")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    sub = parser.add_subparsers(dest="command", required=True)

    p_get = sub.add_parser("get", help="Get config value")
    p_get.add_argument("key")
    p_get.set_defaults(func=cmd_get)

    p_set = sub.add_parser("set", help="Set config value")
    p_set.add_argument("key")
    p_set.add_argument("value")
    p_set.set_defaults(func=cmd_set)

    p_list = sub.add_parser("list", help="List all config")
    p_list.set_defaults(func=cmd_list)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    if sys.platform == "win32":
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
    sys.exit(main())
