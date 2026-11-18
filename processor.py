
import fitz
import easyocr
import numpy as np
import unicodedata
import hashlib
import json
import re

from pathlib import Path


DOCUMENTS_DIR = Path("documents")
CACHE_DIR = Path("cache")

CACHE_DIR.mkdir(exist_ok=True)

reader = None


def clean_hindi_text(text):
    text = unicodedata.normalize("NFC", text)

    for char in ["\u200b", "\ufeff"]:
        text = text.replace(char, "")

    lines = [
        " ".join(line.split())
        for line in text.splitlines()
    ]

    return "\n".join(
        line for line in lines if line
    ).strip()


def is_legacy_encoded_text(text):
    if not text:
        return False

    # Common patterns found in some legacy Hindi encodings.
    patterns = {
        "gS", "gSa", "dks", "dk", "esa", "vkSj",
        "iz", "Hk", "ls", "ij", "ugha", "fd",
        "ds", "dh", "का", "है"
    }

    words = re.findall(r"[A-Za-z]+|[\u0900-\u097F]+", text)

    if not words:
        return False

    latin_words = [
        word for word in words
        if re.fullmatch(r"[A-Za-z]+", word)
    ]

    if not latin_words:
        return False

    matches = sum(
        1 for word in latin_words
        if word in patterns
    )

    devanagari_count = sum(
        1 for char in text
        if "\u0900" <= char <= "\u097F"
    )

    # This is a heuristic, not a universal legacy-font detector.
    return matches >= 3 and devanagari_count < 5


def is_readable_text(text):
    if not text or len(text.strip()) < 10:
        return False

    useful = sum(
        1 for char in text
        if char.isalnum()
        or "\u0900" <= char <= "\u097F"
        or char.isspace()
    )

    return useful / max(len(text), 1) >= 0.55


def load_ocr():
    global reader

    if reader is None:
        print("\nLoading Hindi + English OCR model...")

        reader = easyocr.Reader(
            ["hi", "en"],
            gpu=False
        )

    return reader


def get_file_hash(file_path):
    hasher = hashlib.sha256()

    with open(file_path, "rb") as file:
        for block in iter(
            lambda: file.read(1024 * 1024),
            b""
        ):
            hasher.update(block)

    return hasher.hexdigest()


def load_cache(cache_file):
    pages = {}

    if not cache_file.exists():
        return pages

    with open(cache_file, "r", encoding="utf-8") as file:
        for line in file:
            try:
                data = json.loads(line)
                pages[int(data["page"])] = clean_hindi_text(
                    data["text"]
                )
            except (json.JSONDecodeError, KeyError, ValueError):
                continue

    return pages


def save_page_cache(cache_file, page_number, text):
    with open(cache_file, "a", encoding="utf-8") as file:
        file.write(
            json.dumps(
                {
                    "page": page_number,
                    "text": text
                },
                ensure_ascii=False
            ) + "\n"
        )


def perform_ocr(page):
    pix = page.get_pixmap(
        matrix=fitz.Matrix(2, 2),
        alpha=False
    )

    image = np.frombuffer(
        pix.samples,
        dtype=np.uint8
    ).reshape(
        pix.height,
        pix.width,
        pix.n
    )

    ocr_reader = load_ocr()

    results = ocr_reader.readtext(
        image,
        detail=0,
        paragraph=True
    )

    return clean_hindi_text("\n".join(results))


def extract_pdf(file_path):
    file_hash = get_file_hash(file_path)

    cache_file = CACHE_DIR / f"{file_hash}.jsonl"

    extracted_pages = load_cache(cache_file)

    doc = fitz.open(file_path)

    total_pages = len(doc)

    print(f"\nBook: {file_path.name}")
    print(f"Total pages: {total_pages}")
    print(f"Cached pages: {len(extracted_pages)}")

    try:
        for index in range(total_pages):
            page_number = index + 1

            cached_text = extracted_pages.get(page_number, "")

            # Reuse valid cached pages.
            if (
                cached_text
                and is_readable_text(cached_text)
                and not is_legacy_encoded_text(cached_text)
            ):
                continue

            page = doc[index]

            text = clean_hindi_text(
                page.get_text("text")
            )

            # OCR scanned pages or suspicious legacy text.
            if (
                len(text) < 50
                or is_legacy_encoded_text(text)
            ):
                print(
                    f"OCR processing: "
                    f"{page_number}/{total_pages}"
                )

                ocr_text = perform_ocr(page)

                if is_readable_text(ocr_text):
                    text = ocr_text
                elif is_legacy_encoded_text(text):
                    text = ""

            if (
                not is_readable_text(text)
                or is_legacy_encoded_text(text)
            ):
                print(
                    f"Warning: Page {page_number} "
                    "could not be reliably extracted."
                )
                text = ""

            text = clean_hindi_text(text)

            extracted_pages[page_number] = text

            # Save immediately, so processing can resume.
            save_page_cache(
                cache_file,
                page_number,
                text
            )

    finally:
        doc.close()

    print(f"Extraction completed: {file_path.name}")

    return extracted_pages, file_hash


def get_all_books():
    DOCUMENTS_DIR.mkdir(exist_ok=True)

    return sorted(DOCUMENTS_DIR.glob("*.pdf"))
