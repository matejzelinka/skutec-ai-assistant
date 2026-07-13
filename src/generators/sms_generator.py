from datetime import datetime

from src.utils.formatter import (
    parse_datetime,
    format_time,
    decline_place,
    natural_join,
)


def format_sms_date(dt: datetime) -> str:
    return f"{dt.day}. {dt.month}."


def remove_diacritics(text: str) -> str:
    replacements = str.maketrans(
        {
            "á": "a",
            "č": "c",
            "ď": "d",
            "é": "e",
            "ě": "e",
            "í": "i",
            "ň": "n",
            "ó": "o",
            "ř": "r",
            "š": "s",
            "ť": "t",
            "ú": "u",
            "ů": "u",
            "ý": "y",
            "ž": "z",
            "Á": "A",
            "Č": "C",
            "Ď": "D",
            "É": "E",
            "Ě": "E",
            "Í": "I",
            "Ň": "N",
            "Ó": "O",
            "Ř": "R",
            "Š": "S",
            "Ť": "T",
            "Ú": "U",
            "Ů": "U",
            "Ý": "Y",
            "Ž": "Z",
        }
    )

    return text.translate(replacements)


def collect_locations(event: dict) -> tuple[list[str], list[str]]:
    parts = []
    streets = []

    for location in event["locations"]:
        part = location["part"]
        street = location["street"]

        if part == "Skuteč":
            if street and street not in streets:
                streets.append(street)
        else:
            if part not in parts:
                parts.append(part)

    return parts, streets


def build_sms_locations(
    parts: list[str],
    streets: list[str],
) -> str:
    groups = []

    if parts:
        declined_parts = [
            decline_place(part)
            for part in parts
        ]

        groups.append(
            "v " + natural_join(declined_parts)
        )

    if streets:
        groups.append(
            "v ulicich " + natural_join(streets)
        )

    return " a ".join(groups)


def build_sms_title_locations(
    parts: list[str],
    streets: list[str],
) -> str:
    locations = []

    locations.extend(parts)
    locations.extend(streets)

    return natural_join(locations)


def generate_sms(event: dict) -> tuple[str, str]:
    start = parse_datetime(event["from"])
    end = parse_datetime(event["to"])

    parts, streets = collect_locations(event)

    title_locations = build_sms_title_locations(
        parts,
        streets,
    )

    title = (
        f"Elektrina - {title_locations}, "
        f"{format_sms_date(start)}"
    )

    locations = build_sms_locations(
        parts,
        streets,
    )

    text = (
        f"Zitra od {format_time(start)} "
        f"do {format_time(end)} "
        f"bude prerusena dodavka elektriny "
        f"{locations}. "
        f"Presny rozpis na www.skutec.cz."
    )

    return (
        remove_diacritics(title),
        remove_diacritics(text),
    )