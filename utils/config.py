import os
import yaml
from pathlib import Path

_CONFIG_CACHE = None


def load_config(path=None) -> dict:
    global _CONFIG_CACHE
    if _CONFIG_CACHE is not None:
        return _CONFIG_CACHE

    if path is None:
        path = Path(__file__).parent.parent / "config.yaml"

    defaults = {
        "app": {"name": "PORT-777", "version": "2.0.0", "max_iterations": 25, "language": "auto"},
        "ai": {"provider": "openrouter", "model": "openrouter/auto", "temperature": 0.15, "timeout": 90,
               "max_retries": 2, "fallback_models": [],
               "ollama_url": "http://localhost:11434", "ollama_model": "qwen2.5:7b"},
        "executor": {"default_timeout": 120, "long_running_timeout": 600, "max_output_chars": 3000},
        "safety": {"enabled": True, "confirm_destructive": True,
                   "destructive_commands": ["rm -rf", "dd if=", "mkfs", "format", "fdisk"],
                   "confirm_scanning": True, "max_targets_per_session": 5, "require_target_confirmation": True},
        "sessions": {"storage_dir": "sessions", "auto_save": True, "max_history": 50},
        "reporting": {"output_dir": "outputs", "formats": ["markdown", "txt", "html", "csv"],
                       "include_raw_outputs": False, "auto_generate": True},
        "logging": {"level": "INFO", "file": "logs/port777.log", "max_size_mb": 10},
    }

    if not os.path.exists(path):
        _CONFIG_CACHE = defaults
        return defaults

    try:
        with open(path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}
    except Exception:
        _CONFIG_CACHE = defaults
        return defaults

    merged = defaults.copy()
    for section, values in user_config.items():
        if isinstance(values, dict):
            merged[section] = {**merged.get(section, {}), **values}
        else:
            merged[section] = values

    _CONFIG_CACHE = merged
    return merged


def get_config(section: str = None, key: str = None):
    cfg = load_config()
    if section is None:
        return cfg
    if key is None:
        return cfg.get(section, {})
    return cfg.get(section, {}).get(key)
