from pathlib import Path

from src.collectors.cez_collector import CezCollector
from src.collectors.pdf_collector import download_pdf
from src.generators.article_generator import generate_article
from src.generators.sms_generator import generate_sms
from src.generators.social_generator import generate_social
from src.generators.graphic_generator import generate_graphic
from src.utils.email_sender import send_outage_email
from src.utils.formatter import parse_datetime
from src.utils.history import (
    is_processed,
    mark_as_processed,
)


OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def main():
    collector = CezCollector(572241)

    events = collector.normalize()

    print(f"Nalezeno {len(events)} odstávek")

    new_events = 0

    for event in events:
        event_id = event["id"]

        if is_processed(event_id):
            print(
                f"– Odstávka {event_id} již byla zpracována"
            )
            continue

        print(f"⚡ Nová odstávka: {event_id}")

        event_dir = OUTPUT_DIR / str(event_id)
        event_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        # Datum odstávky pro název PDF
        event_date = parse_datetime(
            event["from"]
        )

        date_filename = event_date.strftime(
            "%d%m%Y"
        )

        # PDF ČEZ
        pdf_path = (
            event_dir
            / f"{date_filename}.pdf"
        )

        download_pdf(
            event["pdf"],
            pdf_path,
        )

        print(
            f"✓ Staženo PDF: {pdf_path}"
        )

        # Web
        web_path = event_dir / "web.docx"

        generate_article(
            event,
            web_path,
        )

        # SMS
        sms_title, sms_text = generate_sms(
            event
        )

        sms_path = event_dir / "sms.txt"

        sms_path.write_text(
            f"{sms_title}\n\n{sms_text}",
            encoding="utf-8",
        )

        # Facebook + Instagram
        social = generate_social(
            event
        )

        social_path = (
            event_dir
            / "social.txt"
        )

        social_path.write_text(
            social,
            encoding="utf-8",
        )

        # Grafika
        graphic_path = (
            event_dir
            / "social.jpg"
        )

        generate_graphic(
            event,
            pdf_path,
            graphic_path,
        )

        # E-mailová notifikace
        attachments = [
            web_path,
            sms_path,
            social_path,
            graphic_path,
            pdf_path,
        ]

        print(
            "✉ Odesílám e-mailovou notifikaci..."
        )

        send_outage_email(
            event,
            attachments,
        )

        # Odstávku označíme jako zpracovanou
        # až po úspěšném odeslání e-mailu
        mark_as_processed(
            event_id
        )

        new_events += 1

        print(
            f"✓ Vytvořen web: "
            f"{web_path}"
        )

        print(
            f"✓ Vytvořena SMS: "
            f"{sms_path}"
        )

        print(
            f"✓ Vytvořen text pro FB a IG: "
            f"{social_path}"
        )

        print(
            f"✓ Vytvořena grafika: "
            f"{graphic_path}"
        )

    if new_events == 0:
        print(
            "Žádná nová odstávka."
        )

    else:
        print(
            f"Hotovo. Zpracováno nových odstávek: "
            f"{new_events}"
        )


if __name__ == "__main__":
    main()