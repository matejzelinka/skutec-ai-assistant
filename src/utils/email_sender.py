import os
import smtplib

from email.message import EmailMessage
from pathlib import Path

from src.utils.formatter import parse_datetime


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465

EMAIL_TO = "matej.zelinka@skutec.cz"


def format_locations(event: dict) -> str:
    locations = {}

    for location in event["locations"]:
        part = location["part"]
        street = location.get("street")

        if part not in locations:
            locations[part] = []

        if (
            street
            and street != part
            and street not in locations[part]
        ):
            locations[part].append(street)

    formatted_locations = []

    for part, streets in locations.items():
        if streets:
            streets_text = ", ".join(streets)

            formatted_locations.append(
                f"{part} ({streets_text})"
            )
        else:
            formatted_locations.append(part)

    return ", ".join(formatted_locations)


def send_outage_email(
    event: dict,
    attachments: list[Path],
) -> None:
    email_from = os.getenv("EMAIL_FROM")
    email_password = os.getenv("EMAIL_PASSWORD")

    if not email_from:
        raise ValueError(
            "Chybí proměnná EMAIL_FROM."
        )

    if not email_password:
        raise ValueError(
            "Chybí proměnná EMAIL_PASSWORD."
        )

    start = parse_datetime(
        event["from"]
    )

    end = parse_datetime(
        event["to"]
    )

    locations = format_locations(event)

    subject = (
        "Nová odstávka elektřiny – "
        f"{start.strftime('%d.%m.%Y')}"
    )

    body = (
        "Byla nalezena nová plánovaná "
        "odstávka elektrické energie.\n\n"
        f"Termín: {start.strftime('%d.%m.%Y')}\n"
        f"Čas: {start.strftime('%H:%M')} "
        f"– {end.strftime('%H:%M')}\n"
        f"Lokality: {locations}\n\n"
        "V příloze jsou připraveny podklady "
        "pro web, SMS a sociální sítě."
    )

    message = EmailMessage()

    message["From"] = email_from
    message["To"] = EMAIL_TO
    message["Subject"] = subject

    message.set_content(body)

    for attachment_path in attachments:
        attachment_path = Path(
            attachment_path
        )

        with attachment_path.open("rb") as file:
            file_data = file.read()

        suffix = (
            attachment_path
            .suffix
            .lower()
        )

        if suffix == ".pdf":
            maintype = "application"
            subtype = "pdf"

        elif suffix == ".docx":
            maintype = "application"
            subtype = (
                "vnd.openxmlformats-officedocument."
                "wordprocessingml.document"
            )

        elif suffix == ".txt":
            maintype = "text"
            subtype = "plain"

        elif suffix in {
            ".jpg",
            ".jpeg",
        }:
            maintype = "image"
            subtype = "jpeg"

        elif suffix == ".png":
            maintype = "image"
            subtype = "png"

        else:
            maintype = "application"
            subtype = "octet-stream"

        message.add_attachment(
            file_data,
            maintype=maintype,
            subtype=subtype,
            filename=attachment_path.name,
        )

    with smtplib.SMTP_SSL(
        SMTP_HOST,
        SMTP_PORT,
    ) as smtp:
        smtp.login(
            email_from,
            email_password,
        )

        smtp.send_message(
            message
        )

    print(
        f"✓ Odeslán e-mail na {EMAIL_TO}"
    )