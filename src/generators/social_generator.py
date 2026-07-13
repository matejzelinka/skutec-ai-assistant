from src.utils.formatter import (
    parse_datetime,
    format_time,
    decline_place,
    natural_join,
)


STREET_SHORT_NAMES = {
    "Boženy Němcové": "B. Němcové",
}


def format_social_time(dt) -> str:
    if dt.minute == 0:
        return str(dt.hour)

    return format_time(dt)


def shorten_street(street: str) -> str:
    return STREET_SHORT_NAMES.get(street, street)


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


def build_social_locations(
    parts: list[str],
    streets: list[str],
) -> str:
    groups = []

    if streets:
        short_streets = [
            shorten_street(street)
            for street in streets
        ]

        groups.append(
            "ve Skutči v ulicích "
            + natural_join(short_streets)
        )

    if parts:
        declined_parts = [
            decline_place(part)
            for part in parts
        ]

        groups.append(
            "v " + natural_join(declined_parts)
        )

    return ", ".join(groups)


def generate_social(event: dict) -> str:
    start = parse_datetime(event["from"])
    end = parse_datetime(event["to"])

    parts, streets = collect_locations(event)

    locations = build_social_locations(
        parts,
        streets,
    )

    return (
        f"⚡ Zítra od {format_social_time(start)} "
        f"do {format_social_time(end)} hodin "
        f"bude přerušena dodávka elektřiny "
        f"{locations}.\n"
        f"Přesný rozpis na 👉 www.skutec.cz"
    )