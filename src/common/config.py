"""
Centralized configuration loader for ODIN-ETL.

Provides a single entry point for loading any YAML config file with:
- Caching (load once, reuse everywhere)
- Validation of required keys
- Clear error messages

Usage:
    from src.common.config import get_config

    cfg = get_config("ibge_censo")           # loads config/ibge_censo.yml
    cfg = get_config("config_geocode")       # loads config/config_geocode.yml
    cfg = get_config("inep_indicadores")     # loads config/inep_indicadores.yml
"""
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_DIR = _PROJECT_ROOT / "config"


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


@lru_cache(maxsize=16)
def get_config(name: str) -> dict:
    """
    Load and cache a YAML config file by name.

    Args:
        name: Config file name without extension (e.g., 'ibge_censo', 'config_geocode').

    Returns:
        Parsed configuration dictionary.

    Raises:
        ConfigError: If the file doesn't exist or is invalid YAML.
    """
    path = _CONFIG_DIR / f"{name}.yml"
    if not path.exists():
        raise ConfigError(
            f"Config file not found: {path}\n"
            f"Available configs: {[f.stem for f in _CONFIG_DIR.glob('*.yml')]}"
        )

    try:
        with open(path, encoding="utf-8") as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path.name}: {e}") from e

    if not isinstance(config, dict):
        raise ConfigError(f"Config {path.name} must be a YAML mapping, got {type(config).__name__}")

    logger.debug("Config loaded: %s (%d top-level keys)", name, len(config))
    return config


def validate_keys(config: dict, required_keys: list[str], context: str = "") -> None:
    """
    Validate that all required keys exist in a config dict.

    Args:
        config:        The configuration dictionary.
        required_keys: List of dot-separated key paths (e.g., 'ftp.host', 'paths.silver').
        context:       Optional context string for error messages.

    Raises:
        ConfigError: If any required key is missing.
    """
    missing = []
    for key_path in required_keys:
        parts = key_path.split(".")
        current = config
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                missing.append(key_path)
                break
            current = current[part]

    if missing:
        ctx = f" ({context})" if context else ""
        raise ConfigError(
            f"Missing required config keys{ctx}: {missing}"
        )


def get_nested(config: dict, key_path: str, default: Any = None) -> Any:
    """
    Safely get a nested config value using dot notation.

    Args:
        config:   The configuration dictionary.
        key_path: Dot-separated path (e.g., 'ftp.host', 'transform_municipio.gold_output').
        default:  Value to return if key doesn't exist.

    Returns:
        The value at the key path, or default if not found.
    """
    parts = key_path.split(".")
    current = config
    for part in parts:
        if not isinstance(current, dict) or part not in current:
            return default
        current = current[part]
    return current


def reload_config(name: str) -> dict:
    """
    Force reload a config file, clearing the cache for that name.

    Useful in tests or when config files are modified at runtime.
    """
    get_config.cache_clear()
    return get_config(name)
