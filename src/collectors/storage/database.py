import json
import os

from src.config import DATA_DIR


DATABASE = os.path.join(DATA_DIR, "events.json")


def load_database():

    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

    if not os.path.exists(DATABASE):
        return []

    with open(DATABASE, encoding="utf-8") as f:
        return json.load(f)


def save_database(data):

    with open(DATABASE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)