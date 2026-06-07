from __future__ import annotations

import email
import re
from pathlib import Path
from email import policy


try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import docx
except ImportError:
    docx = None


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DOCS_DIR = ROOT / "data" / "docs"


def slugify(name: str) -> str:
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", "_", name)
    return name.strip("_")


def extract_pdf(path: Path) -> str:
    if fitz is None:
        raise RuntimeError("Install PyMuPDF: pip install pymupdf")

    text_parts = []
    with fitz.open(path) as pdf:
        for page in pdf:
            text_parts.append(page.get_text())

    return "\n\n".join(text_parts)


def extract_docx(path: Path) -> str:
    if docx is None:
        raise RuntimeError("Install python-docx: pip install python-docx")

    document = docx.Document(path)
    return "\n\n".join(p.text for p in document.paragraphs if p.text.strip())


def extract_email(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    msg = email.message_from_string(raw, policy=policy.default)

    subject = msg.get("subject", "")
    sender = msg.get("from", "")
    date = msg.get("date", "")

    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                body += part.get_content()
    else:
        body = msg.get_content()

    return f"# Email: {subject}\n\nFrom: {sender}\n\nDate: {date}\n\n{body}"


def extract_txt_or_md(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def write_markdown(source_path: Path, text: str):
    relative_parent = source_path.parent.relative_to(RAW_DIR)
    output_dir = DOCS_DIR / relative_parent
    output_dir.mkdir(parents=True, exist_ok=True)

    output_name = f"{slugify(source_path.stem)}.md"
    output_path = output_dir / output_name

    output_path.write_text(
        f"# Source: {source_path.name}\n\n{text}",
        encoding="utf-8",
    )

    print(f"Created: {output_path.relative_to(ROOT)}")


def main():
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    supported = [".pdf", ".docx", ".eml", ".txt", ".md"]

    for path in RAW_DIR.rglob("*"):
        if not path.is_file():
            continue

        suffix = path.suffix.lower()

        if suffix not in supported:
            print(f"Skipping unsupported file: {path}")
            continue

        try:
            if suffix == ".pdf":
                text = extract_pdf(path)
            elif suffix == ".docx":
                text = extract_docx(path)
            elif suffix == ".eml":
                text = extract_email(path)
            else:
                text = extract_txt_or_md(path)

            if text.strip():
                write_markdown(path, text)
            else:
                print(f"No text extracted: {path}")

        except Exception as exc:
            print(f"Failed: {path} -> {exc}")


if __name__ == "__main__":
    main()