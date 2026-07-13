import json
from pathlib import Path


HISTORY_FILE = Path("data/processed_outages.json")


def load_processed_ids() -> set[str]:
    if not HISTORY_FILE.exists():
        return set()

    data = json.loads(
        HISTORY_FILE.read_text(encoding="utf-8")
    )

    return set(str(item) for item in data)


def save_processed_ids(ids: set[str]) -> None:
    HISTORY_FILE.parent.mkdir(exist_ok=True)

    HISTORY_FILE.write_text(
        json.dumps(
            sorted(ids),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def is_processed(event_id) -> bool:
    processed_ids = load_processed_ids()

    return str(event_id) in processed_ids


def mark_as_processed(event_id) -> None:
    processed_ids = load_processed_ids()

    processed_ids.add(str(event_id))

    save_processed_ids(processed_ids)