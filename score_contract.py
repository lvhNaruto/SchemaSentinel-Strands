"""Shared, versioned score-source contract.

This module keeps the agent prompt and the service-level enforcer in sync.
Add new score-source keys to config/score_contract.json instead of editing
Python code.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Set


DEFAULT_CONTRACT = {
    "valid_score_keys": [
        "relevance_score", "score", "eval_score", "confidence", "confidence_score",
        "confidence_rating", "rating", "popularity_pct", "pct", "percent",
        "percentage", "match_score", "relevance", "stars_count_pct",
    ],
    "raw_metric_score_keys": [
        "rating_out_of_5", "rating_out_of_10", "rating_out_of_100",
        "popularity_pct", "confidence", "relevance_score",
    ],
}


def _contract_path() -> Path:
    """Locate the JSON contract file, falling back to the repo root."""
    env_path = os.environ.get("SCORE_CONTRACT_PATH")
    if env_path:
        return Path(env_path)
    # Default: same directory as this module / config/score_contract.json
    return Path(__file__).resolve().parent / "config" / "score_contract.json"


def _load_contract() -> Dict[str, Any]:
    path = _contract_path()
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return DEFAULT_CONTRACT


def _ensure_config_file() -> None:
    """Persist the default contract file if it does not yet exist."""
    path = _contract_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(DEFAULT_CONTRACT, indent=2), encoding="utf-8")


_ensure_config_file()
_CONTRACT = _load_contract()


def get_valid_score_keys() -> Set[str]:
    return set(_CONTRACT.get("valid_score_keys", DEFAULT_CONTRACT["valid_score_keys"]))


def get_raw_metric_score_keys() -> Set[str]:
    return set(_CONTRACT.get("raw_metric_score_keys", DEFAULT_CONTRACT["raw_metric_score_keys"]))


def get_score_keys_prompt_fragment() -> str:
    """Return a comma-space separated list for the agent prompt."""
    return ", ".join(sorted(get_valid_score_keys()))
