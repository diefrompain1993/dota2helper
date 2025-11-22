"""Automated setup utilities: GSI config, region calibration, and startup helpers."""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Optional

from online_assets_loader import update_assets

logger = logging.getLogger(__name__)

CONFIG_DIR = Path(__file__).parent / "config"
GSI_CFG_PATH = CONFIG_DIR / "gsi_config_example.cfg"
REGIONS_PATH = CONFIG_DIR / "regions.json"

GSI_CONFIG_CONTENT = """"Valve GameState Integration Configuration"
{
    "uri" "http://localhost:4000/gsi"
    "timeout" "5.0"
    "buffer"  "0.1"
    "throttle" "0.1"
    "heartbeat" "30.0"
    "data"
    {
        "provider"       "1"
        "player"         "1"
        "abilities"      "1"
        "items"          "1"
    }
}
"""


def _find_steam_path() -> Optional[Path]:
    """Best-effort detection of the Steam install path (Windows-first)."""
    try:
        import winreg  # type: ignore

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\\Valve\\Steam") as key:
            path, _ = winreg.QueryValueEx(key, "SteamPath")
            steam_path = Path(path)
            if steam_path.exists():
                return steam_path
    except Exception:  # noqa: BLE001
        logger.debug("Steam path not found via registry; falling back to defaults")

    candidates = [
        Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Steam",
        Path(os.environ.get("PROGRAMFILES", "")) / "Steam",
        Path.home() / "AppData" / "Local" / "Steam",
    ]
    for candidate in candidates:
        if candidate and candidate.exists():
            return candidate
    return None


def _dota_cfg_path() -> Optional[Path]:
    steam_path = _find_steam_path()
    if not steam_path:
        return None
    return (
        steam_path
        / "steamapps"
        / "common"
        / "dota 2 beta"
        / "game"
        / "dota"
        / "cfg"
        / "gamestate_integration"
    )


def install_gsi_config_if_missing() -> None:
    """Copy gsi config into the Dota 2 gamestate folder if absent."""
    target_dir = _dota_cfg_path()
    if target_dir is None:
        logger.warning("Could not locate Dota 2 cfg directory automatically")
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "dota2helper.cfg"
    if target_file.exists():
        logger.info("GSI config already present at %s", target_file)
        return
    target_file.write_text(GSI_CONFIG_CONTENT, encoding="utf-8")
    logger.info("Installed GSI config to %s", target_file)


def auto_calibrate_regions() -> None:
    """Estimate HUD regions based on current screen resolution."""
    width, height = 1920, 1080
    try:
        import pyautogui  # type: ignore

        size = pyautogui.size()
        width, height = size.width, size.height
    except Exception:  # noqa: BLE001
        logger.debug("pyautogui not available; falling back to default 1920x1080")
    top_bar = {
        "left": int(0.2 * width),
        "top": int(0.05 * height),
        "width": int(0.6 * width),
        "height": int(0.1 * height),
    }
    scoreboard = {
        "left": int(0.1 * width),
        "top": int(0.25 * height),
        "width": int(0.8 * width),
        "height": int(0.5 * height),
    }
    REGIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGIONS_PATH.write_text(
        json.dumps(
            {"top_bar_enemies": top_bar, "scoreboard_items": scoreboard},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    logger.info(
        "Auto-calibrated regions saved to %s (screen %sx%s)",
        REGIONS_PATH,
        width,
        height,
    )


def initialize_application() -> None:
    """Run one-time setup before the orchestrator/UI start."""
    install_gsi_config_if_missing()
    auto_calibrate_regions()
    update_assets()


__all__ = ["install_gsi_config_if_missing", "auto_calibrate_regions", "initialize_application"]
