"""Download Vatican II documents from the official Vatican archive.

This script fetches the English text for each Vatican II document and writes:
- a cleaned text file to catebot/data/vatican2/<ABBR>.txt
- the raw HTML to catebot/data/vatican2/raw/<ABBR>.html

Usage:
    python scripts/download_vatican2.py
    python scripts/download_vatican2.py --output-dir catebot/data/vatican2

The script only depends on requests plus the Python standard library.
"""
from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

import requests


BASE_URL = "https://www.vatican.va/archive/hist_councils/ii_vatican_council/documents/"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "catebot" / "data" / "vatican2"


@dataclass(frozen=True)
class Document:
    abbr: str
    title: str
    url: str


DOCUMENTS: tuple[Document, ...] = (
    Document("DV", "Dei Verbum", BASE_URL + "vat-ii_const_19651118_dei-verbum_en.html"),
    Document("LG", "Lumen Gentium", BASE_URL + "vat-ii_const_19641121_lumen-gentium_en.html"),
    Document("SC", "Sacrosanctum Concilium", BASE_URL + "vat-ii_const_19631204_sacrosanctum-concilium_en.html"),
    Document("GS", "Gaudium et Spes", BASE_URL + "vat-ii_const_19651207_gaudium-et-spes_en.html"),
    Document("GE", "Gravissimum Educationis", BASE_URL + "vat-ii_decl_19651028_gravissimum-educationis_en.html"),
    Document("NA", "Nostra Aetate", BASE_URL + "vat-ii_decl_19651028_nostra-aetate_en.html"),
    Document("DH", "Dignitatis Humanae", BASE_URL + "vat-ii_decl_19651207_dignitatis-humanae_en.html"),
    Document("AG", "Ad Gentes", BASE_URL + "vat-ii_decree_19651207_ad-gentes_en.html"),
    Document("PO", "Presbyterorum Ordinis", BASE_URL + "vat-ii_decree_19651207_presbyterorum-ordinis_en.html"),
    Document("AA", "Apostolicam Actuositatem", BASE_URL + "vat-ii_decree_19651118_apostolicam-actuositatem_en.html"),
    Document("OT", "Optatam Totius", BASE_URL + "vat-ii_decree_19651028_optatam-totius_en.html"),
    Document("PC", "Perfectae Caritatis", BASE_URL + "vat-ii_decree_19651028_perfectae-caritatis_en.html"),
    Document("CD", "Christus Dominus", BASE_URL + "vat-ii_decree_19651028_christus-dominus_en.html"),
    Document("UR", "Unitatis Redintegratio", BASE_URL + "vat-ii_decree_19641121_unitatis-redintegratio_en.html"),
    Document("OE", "Orientalium Ecclesiarum", BASE_URL + "vat-ii_decree_19641121_orientalium-ecclesiarum_en.html"),
    Document("IM", "Inter Mirifica", BASE_URL + "vat-ii_decree_19631204_inter-mirifica_en.html"),
)

SKIP_LINES = {
    "Index",
    "HOLY FATHER",
    "COLLEGE OF CARDINALS",
    "ROMAN CURIA",
    "ARCHIVE",
    "Back",
    "Top",
    "Print",
    "Search",
    "Facebook",
    "Twitter",
    "Google+",
    "Mail",
    "Skip to content",
    "Navigation Menu",
    "Footer",
    "Additional Links",
}

START_LINE_PATTERNS = (
    re.compile(r"^PREFACE$"),
    re.compile(r"^INTRODUCTION$"),
    re.compile(r"^CHAPTER\s+[IVXLC]+$"),
    re.compile(r"^ARTICLE\s+\d+$"),
    re.compile(r"^\d+\.\s"),
)


class HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignore_depth = 0
        self._skip_newline = False

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"}:
            self._ignore_depth += 1
            return
        if self._ignore_depth:
            return
        if tag in {"p", "div", "section", "article", "header", "footer", "main", "br", "tr", "table", "thead", "tbody", "tfoot", "hr", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")
        if tag == "li":
            self.parts.append("- ")

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in {"script", "style", "noscript"} and self._ignore_depth:
            self._ignore_depth -= 1
            return
        if self._ignore_depth:
            return
        if tag in {"p", "div", "section", "article", "header", "footer", "main", "tr", "table", "thead", "tbody", "tfoot", "li", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignore_depth:
            return
        text = html.unescape(data)
        if text.strip():
            self.parts.append(text)

    def get_text(self) -> str:
        text = "".join(self.parts)
        text = text.replace("\r", "\n")
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        lines = []
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                lines.append("")
                continue
            line = re.sub(r"\s*\[.*?\]\s*", " ", line)
            line = re.sub(r"\s{2,}", " ", line).strip()
            if not line:
                continue
            if line in SKIP_LINES:
                continue
            if re.fullmatch(r"(?:[A-Z]{2,3}(?:\s*-\s*[A-Z]{2,3})+)", line):
                continue
            if line.startswith("©"):
                continue
            lines.append(line)

        cleaned = []
        seen_nonblank = False
        start_index = 0
        for index, line in enumerate(lines):
            if any(pattern.match(line) for pattern in START_LINE_PATTERNS):
                start_index = index
                break
        for line in lines[start_index:]:
            if line == "" and (not cleaned or cleaned[-1] == ""):
                continue
            cleaned.append(line)
        return "\n".join(cleaned).strip() + "\n"


def fetch_document(session: requests.Session, document: Document, timeout: int) -> tuple[str, str]:
    response = session.get(document.url, timeout=timeout)
    response.raise_for_status()
    response.encoding = response.encoding or "utf-8"
    raw_html = response.text
    extractor = HTMLTextExtractor()
    extractor.feed(raw_html)
    text = extractor.get_text()
    return raw_html, text


def write_document(output_dir: Path, document: Document, raw_html: str, text: str) -> None:
    text_dir = output_dir
    raw_dir = output_dir / "raw"
    text_dir.mkdir(parents=True, exist_ok=True)
    raw_dir.mkdir(parents=True, exist_ok=True)

    (text_dir / f"{document.abbr}.txt").write_text(text, encoding="utf-8")
    (raw_dir / f"{document.abbr}.html").write_text(raw_html, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Vatican II documents from the official Vatican archive.")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR, help="Directory where files will be written.")
    parser.add_argument("--timeout", type=int, default=30, help="HTTP timeout in seconds.")
    parser.add_argument("--only", nargs="*", help="Optional list of document abbreviations to download, e.g. DV LG SC.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    wanted = {item.upper() for item in args.only} if args.only else None

    session = requests.Session()
    session.headers.update({"User-Agent": "catebot-vatican2-downloader/1.0"})

    selected_documents = [doc for doc in DOCUMENTS if wanted is None or doc.abbr in wanted]
    if not selected_documents:
        print("No documents selected.")
        return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)

    for document in selected_documents:
        print(f"Downloading {document.abbr} - {document.title}")
        raw_html, text = fetch_document(session, document, args.timeout)
        write_document(args.output_dir, document, raw_html, text)
        print(f"  wrote {args.output_dir / (document.abbr + '.txt')}")
        print(f"  wrote {args.output_dir / 'raw' / (document.abbr + '.html')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
