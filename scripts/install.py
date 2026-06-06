"""Install the smart-model-routing Hermes plugin."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


PLUGIN_FILES = (
    "plugin.yaml",
    "__init__.py",
    "router.py",
    "config.example.yaml",
)


def default_hermes_home() -> Path:
    if os.environ.get("HERMES_HOME"):
        return Path(os.environ["HERMES_HOME"]).expanduser()
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        candidate = Path(local_app_data) / "hermes"
        if candidate.exists():
            return candidate
    return Path.home() / ".hermes"


def copy_tree(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    for name in PLUGIN_FILES:
        shutil.copy2(src / name, dst / name)
    skills_src = src / "skills"
    skills_dst = dst / "skills"
    if skills_dst.exists():
        shutil.rmtree(skills_dst)
    shutil.copytree(skills_src, skills_dst)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--hermes-home",
        default=str(default_hermes_home()),
        help="Hermes home directory. Defaults to HERMES_HOME, Windows LocalAppData, or ~/.hermes.",
    )
    parser.add_argument(
        "--plugin-dir",
        default="",
        help="Explicit destination plugin directory.",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    hermes_home = Path(args.hermes_home).expanduser().resolve()
    dest = (
        Path(args.plugin_dir).expanduser().resolve()
        if args.plugin_dir
        else hermes_home / "plugins" / "smart-model-routing"
    )

    copy_tree(root, dest)
    print(f"Installed smart-model-routing plugin to {dest}")
    print("Automatic switching also requires the Hermes core integration in patches/core-integration.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
