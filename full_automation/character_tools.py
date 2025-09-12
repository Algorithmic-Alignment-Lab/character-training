import json
from pathlib import Path
from typing import Any, Dict, List


CHAR_DEF_PATH = Path("auto_eval_gen/character_definitions.json").resolve()
BEHAVIORS_PATH = Path("auto_eval_gen/behaviors/behaviors.json").resolve()
BEHAVIOR_EXAMPLES_DIR = Path("auto_eval_gen/behaviors/examples").resolve()


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def upsert_character(character_id: str, spec: Dict[str, Any]) -> None:
    data = load_json(CHAR_DEF_PATH)
    data[character_id] = spec
    save_json(CHAR_DEF_PATH, data)


def upsert_behaviors(behaviors: Dict[str, str]) -> None:
    data = load_json(BEHAVIORS_PATH)
    data.update(behaviors)
    save_json(BEHAVIORS_PATH, data)


def write_behavior_example(name: str, example: Dict[str, Any]) -> Path:
    out = BEHAVIOR_EXAMPLES_DIR / f"{name}.json"
    save_json(out, example)
    return out


def ensure_character_exists(character_id: str) -> bool:
    return character_id in load_json(CHAR_DEF_PATH)


def get_character(character_id: str) -> Dict[str, Any]:
    data = load_json(CHAR_DEF_PATH)
    if character_id not in data:
        raise KeyError(f"Character '{character_id}' not found in {CHAR_DEF_PATH}")
    return data[character_id]
