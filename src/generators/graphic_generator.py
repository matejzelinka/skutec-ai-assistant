from pathlib import Path
from io import BytesIO

import fitz

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)

from src.utils.formatter import (
    parse_datetime,
    format_weekday,
    decline_place,
    natural_join,
)


WIDTH = 1080
HEIGHT = 1350

BACKGROUND_COLOR = "#f9d235"
OVERLAY_OPACITY = 0.85
TEXT_COLOR = "#000000"

ASSETS_DIR = Path("src") / "assets"

FONT_PATH = ASSETS_DIR / "AvalonCEBold.TTF"
LOGO_PATH = ASSETS_DIR / "logo.png"
FLASH_PATH = ASSETS_DIR / "flash.png"
SQUARE_PATH = ASSETS_DIR / "ctverec.png"


# TEXT

TEXT_X = 158
TEXT_Y = 174

TEXT_MAX_WIDTH = 830

FONT_SIZE = 80
LINE_HEIGHT = 104


# ČTVEREC

SQUARE_X = 103
SQUARE_Y = 123
SQUARE_SIZE = 56


# LOGO

LOGO_X = 155
LOGO_BOTTOM = 75
LOGO_MAX_WIDTH = 205
LOGO_MAX_HEIGHT = 90


# BLESK

FLASH_RIGHT = 70
FLASH_BOTTOM = 70
FLASH_MAX_SIZE = 235
FLASH_OPACITY = 0.26


# JEDNOZNAKOVÉ PŘEDLOŽKY A SPOJKY

NON_BREAKING_WORDS = {
    "k",
    "s",
    "v",
    "z",
    "o",
    "u",
    "a",
    "i",
}


def find_map_page(document) -> int:
    best_page_index = 0
    best_score = None

    for page_index in range(len(document)):
        page = document[page_index]

        text = page.get_text("text").strip()
        text_length = len(text)

        images = page.get_images(full=True)
        image_count = len(images)

        drawings = page.get_drawings()
        drawing_count = len(drawings)

        score = (
            image_count * 1000
            + drawing_count * 10
            - text_length
        )

        print(
            f"Strana {page_index + 1}: "
            f"text={text_length}, "
            f"obrazky={image_count}, "
            f"kresby={drawing_count}, "
            f"score={score}"
        )

        if best_score is None or score > best_score:
            best_score = score
            best_page_index = page_index

    print(
        f"✓ Mapa nalezena na straně "
        f"{best_page_index + 1}"
    )

    return best_page_index


def extract_map_image(
    pdf_path: Path,
) -> Image.Image:
    document = fitz.open(pdf_path)

    map_page_index = find_map_page(document)
    page = document[map_page_index]

    images = page.get_images(full=True)

    if not images:
        document.close()

        raise ValueError(
            "Na mapové stránce nebyl nalezen obrázek."
        )

    largest_image = None
    largest_area = 0

    for image_info in images:
        xref = image_info[0]

        extracted = document.extract_image(xref)

        image = Image.open(
            BytesIO(extracted["image"])
        ).convert("RGB")

        area = image.width * image.height

        print(
            f"Obrázek xref={xref}: "
            f"{image.width} × {image.height}"
        )

        if area > largest_area:
            largest_area = area
            largest_image = image.copy()

    document.close()

    if largest_image is None:
        raise ValueError(
            "Nepodařilo se získat mapu z PDF."
        )

    print(
        f"✓ Vybrán mapový obrázek: "
        f"{largest_image.width} × "
        f"{largest_image.height}"
    )

    return largest_image


def resize_map_to_canvas(
    image: Image.Image,
) -> Image.Image:
    scale = HEIGHT / image.height

    new_width = int(
        image.width * scale
    )

    image = image.resize(
        (
            new_width,
            HEIGHT,
        ),
        Image.Resampling.LANCZOS,
    )

    if new_width < WIDTH:
        scale = WIDTH / image.width

        new_height = int(
            image.height * scale
        )

        image = image.resize(
            (
                WIDTH,
                new_height,
            ),
            Image.Resampling.LANCZOS,
        )

        top = (
            image.height - HEIGHT
        ) // 2

        return image.crop(
            (
                0,
                top,
                WIDTH,
                top + HEIGHT,
            )
        )

    left = (
        new_width - WIDTH
    ) // 2

    return image.crop(
        (
            left,
            0,
            left + WIDTH,
            HEIGHT,
        )
    )


def render_pdf_background(
    pdf_path: Path,
) -> Image.Image:
    map_image = extract_map_image(
        pdf_path
    )

    return resize_map_to_canvas(
        map_image
    )


def add_yellow_overlay(
    image: Image.Image,
) -> Image.Image:
    overlay = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        BACKGROUND_COLOR,
    )

    return Image.blend(
        image,
        overlay,
        OVERLAY_OPACITY,
    )


def format_graphic_date(dt) -> str:
    return dt.strftime("%d.%m.")


def format_graphic_locations(
    event: dict,
) -> str:
    parts = []

    for location in event["locations"]:
        part = location["part"]

        if part not in parts:
            parts.append(part)

    if len(parts) == 1:
        if parts[0] == "Skuteč":
            return "ve Skutči"

        return (
            f"v {decline_place(parts[0])}"
        )

    declined = []

    for part in parts:
        if part == "Skuteč":
            declined.append("Skutči")
        else:
            declined.append(
                decline_place(part)
            )

    return (
        "v "
        + natural_join(declined)
    )


def build_graphic_text(
    event: dict,
) -> str:
    start = parse_datetime(
        event["from"]
    )

    weekday = format_weekday(start)
    date = format_graphic_date(start)

    locations = format_graphic_locations(
        event
    )

    return (
        f"{weekday.capitalize()} {date} "
        f"bude přerušena "
        f"dodávka elektřiny "
        f"{locations}."
    )


def create_word_units(
    text: str,
) -> list[str]:
    words = text.split()

    units = []

    index = 0

    while index < len(words):
        word = words[index]

        normalized = (
            word
            .lower()
            .strip(".,;:!?")
        )

        if (
            normalized in NON_BREAKING_WORDS
            and index + 1 < len(words)
        ):
            units.append(
                word
                + " "
                + words[index + 1]
            )

            index += 2

        else:
            units.append(word)

            index += 1

    return units


def wrap_text(
    draw,
    text,
    font,
    max_width,
) -> list[str]:
    units = create_word_units(
        text
    )

    lines = []
    current_line = ""

    for unit in units:
        test_line = (
            f"{current_line} {unit}".strip()
        )

        bbox = draw.textbbox(
            (0, 0),
            test_line,
            font=font,
        )

        width = (
            bbox[2] - bbox[0]
        )

        if (
            width <= max_width
            or not current_line
        ):
            current_line = test_line

        else:
            lines.append(
                current_line
            )

            current_line = unit

    if current_line:
        lines.append(
            current_line
        )

    return lines


def prepare_logo(
    image: Image.Image,
) -> Image.Image:
    image = image.convert("RGBA")

    pixels = image.load()

    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = pixels[x, y]

            brightness = (
                r + g + b
            ) / 3

            if brightness > 235:
                pixels[x, y] = (
                    255,
                    255,
                    255,
                    0,
                )

            else:
                pixels[x, y] = (
                    0,
                    0,
                    0,
                    a,
                )

    return image


def add_square(
    canvas: Image.Image,
) -> None:
    square = Image.open(
        SQUARE_PATH
    ).convert("RGBA")

    square = square.resize(
        (
            SQUARE_SIZE,
            SQUARE_SIZE,
        ),
        Image.Resampling.LANCZOS,
    )

    canvas.alpha_composite(
        square,
        (
            SQUARE_X,
            SQUARE_Y,
        ),
    )


def add_logo(
    canvas: Image.Image,
) -> None:
    logo = Image.open(
        LOGO_PATH
    )

    logo = prepare_logo(
        logo
    )

    logo.thumbnail(
        (
            LOGO_MAX_WIDTH,
            LOGO_MAX_HEIGHT,
        ),
        Image.Resampling.LANCZOS,
    )

    y = (
        HEIGHT
        - logo.height
        - LOGO_BOTTOM
    )

    canvas.alpha_composite(
        logo,
        (
            LOGO_X,
            y,
        ),
    )


def add_flash(
    canvas: Image.Image,
) -> None:
    flash = Image.open(
        FLASH_PATH
    ).convert("RGBA")

    flash.thumbnail(
        (
            FLASH_MAX_SIZE,
            FLASH_MAX_SIZE,
        ),
        Image.Resampling.LANCZOS,
    )

    alpha = flash.getchannel("A")

    alpha = alpha.point(
        lambda value: int(
            value * FLASH_OPACITY
        )
    )

    flash.putalpha(alpha)

    x = (
        WIDTH
        - flash.width
        - FLASH_RIGHT
    )

    y = (
        HEIGHT
        - flash.height
        - FLASH_BOTTOM
    )

    canvas.alpha_composite(
        flash,
        (
            x,
            y,
        ),
    )


def generate_graphic(
    event: dict,
    pdf_path: Path,
    output_path: Path,
) -> None:
    background = render_pdf_background(
        pdf_path
    )

    background = add_yellow_overlay(
        background
    )

    canvas = background.convert(
        "RGBA"
    )

    draw = ImageDraw.Draw(
        canvas
    )

    font = ImageFont.truetype(
        str(FONT_PATH),
        FONT_SIZE,
    )

    text = build_graphic_text(
        event
    )

    lines = wrap_text(
        draw,
        text,
        font,
        TEXT_MAX_WIDTH,
    )

    x = TEXT_X
    y = TEXT_Y

    for line in lines:
        draw.text(
            (
                x,
                y,
            ),
            line,
            font=font,
            fill=TEXT_COLOR,
        )

        y += LINE_HEIGHT

    add_square(
        canvas
    )

    add_logo(
        canvas
    )

    add_flash(
        canvas
    )

    canvas = canvas.convert(
        "RGB"
    )

    canvas.save(
        output_path,
        quality=95,
    )