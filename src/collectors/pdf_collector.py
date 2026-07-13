from pathlib import Path

import requests
import urllib3


urllib3.disable_warnings(
    urllib3.exceptions.InsecureRequestWarning
)


PDF_BASE_URL = "https://cdn.bezstavy.cz"


def download_pdf(
    pdf_key: str,
    output_path: Path,
) -> Path:
    url = f"{PDF_BASE_URL}/{pdf_key}"

    response = requests.get(
        url,
        headers={
            "User-Agent": "Skutec-AI-Assistant/1.0",
        },
        timeout=30,
        verify=False,
    )

    response.raise_for_status()

    output_path.write_bytes(response.content)

    return output_path