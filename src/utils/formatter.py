from datetime import datetime
from dateutil import tz

def parse_datetime(value: str):
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return dt.astimezone(tz.gettz("Europe/Prague"))

MONTHS = {
    1: "ledna",
    2: "února",
    3: "března",
    4: "dubna",
    5: "května",
    6: "června",
    7: "července",
    8: "srpna",
    9: "září",
    10: "října",
    11: "listopadu",
    12: "prosince",
}

WEEKDAYS = {
    0: "v pondělí",
    1: "v úterý",
    2: "ve středu",
    3: "ve čtvrtek",
    4: "v pátek",
    5: "v sobotu",
    6: "v neděli",
}

PLACE_DECLINATION = {
    "Borek": "Borku",
    "Hněvětice": "Hněvěticích",
    "Lažany": "Lažanech",
    "Lešany": "Lešanech",
    "Lhota u Skutče": "Lhotě u Skutče",
    "Nová Ves": "Nové Vsi",
    "Přibylov": "Přibylově",
    "Radčice": "Radčicích",
    "Skuteč": "části Skutče",
    "Skutíčko": "Skutíčku",
    "Štěpánov": "Štěpánově",
    "Zbožnov": "Zbožnově",
    "Zhoř": "Zhoři",
    "Žďárec u Skutče": "Žďárci u Skutče",
}



def format_date(dt: datetime) -> str:
    return f"{dt.day}. {MONTHS[dt.month]}"


def format_time(dt: datetime) -> str:
    return f"{dt.hour}:{dt.strftime('%M')}"


def format_weekday(dt: datetime) -> str:
    return WEEKDAYS[dt.weekday()]


def decline_place(place: str) -> str:
    return PLACE_DECLINATION.get(place, place)


def natural_join(items: list[str]) -> str:

    if not items:
        return ""

    if len(items) == 1:
        return items[0]

    if len(items) == 2:
        return f"{items[0]} a {items[1]}"

    return ", ".join(items[:-1]) + " a " + items[-1]


def location_sentence(parts: list[str], streets: list[str]) -> str:
    """
    Vrací přirozenou větu.

    Příklady:

    ve Hněvěticích

    ve Hněvěticích a Lažanech

    ve Hněvěticích, Lažanech a části Skutče

    ve Skutči v ulicích Boženy Němcové a Zahradní

    ve Hněvěticích, Lažanech a ve Skutči v ulicích
    Boženy Němcové, Dr. Znojemského a Zahradní
    """

    parts = list(dict.fromkeys(parts))
    streets = list(dict.fromkeys(streets))

    has_skutec = "Skuteč" in parts

    parts = [p for p in parts if p != "Skuteč"]

    declined = [decline_place(p) for p in parts]

    text = ""

    if declined:
        text = "ve " + natural_join(declined)

    if has_skutec and not streets:

        if text:
            text += " a části Skutče"
        else:
            text = "ve Skutči"

    if streets:

        street_text = natural_join(streets)

        if text:
            text += f" a ve Skutči v ulicích {street_text}"
        else:
            text = f"ve Skutči v ulicích {street_text}"

    return text