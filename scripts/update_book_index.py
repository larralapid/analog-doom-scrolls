#!/usr/bin/env python3
"""Regenerate the README book list from the numbered haul caption files."""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[1]
START = "<!-- book-index:start -->"
END = "<!-- book-index:end -->"


def index_lines():
    lines = []
    for path in sorted(ROOT.glob("[0-9][0-9][0-9]/caption.md")):
        haul = path.parent.name
        match = re.match(r"\A---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
        if not match:
            raise ValueError(f"{haul}/caption.md needs YAML frontmatter")

        data = yaml.safe_load(match[1])
        if not isinstance(data, dict) or data.get("haul") != haul:
            raise ValueError(f"{haul}/caption.md needs a matching quoted haul number")

        number = haul
        publish_url = data.get("publish_url")
        if data.get("status") == "published":
            if not data.get("publish_date") or not isinstance(publish_url, str):
                raise ValueError(f"{haul}/caption.md needs a publish date and TikTok URL")
            parsed_url = urlsplit(publish_url)
            post_hosts = {"tiktok.com", "www.tiktok.com", "m.tiktok.com"}
            short_hosts = {"vm.tiktok.com", "vt.tiktok.com"}
            full_post = parsed_url.hostname in post_hosts and re.fullmatch(
                r"/@[\w.]+/(?:video|photo)/\d+/?", parsed_url.path
            )
            short_link = parsed_url.hostname in short_hosts and re.fullmatch(
                r"/[\w-]+/?", parsed_url.path
            )
            if parsed_url.scheme != "https" or not (full_post or short_link):
                raise ValueError(f"{haul}/caption.md needs a TikTok post URL")
            number = f"[{haul}]({publish_url})"

        books = data.get("books")
        if not isinstance(books, list):
            raise ValueError(f"{haul}/caption.md needs a books list")
        count = f"{len(books)} {'book' if len(books) == 1 else 'books'}"
        lines.extend([f"### Haul {number} · {count}", "", f"[Caption and files]({haul}/caption.md)", ""])
        for book in books:
            title = book.get("title") if isinstance(book, dict) else None
            if not isinstance(title, str) or not title.strip() or "\n" in title:
                raise ValueError(f"{haul}/caption.md has a book entry without a valid title")
            note = book.get("note")
            suffix = f" ({note})" if note else ""
            lines.append(f"- {title}{suffix}")
        if not books:
            lines.append("Book list pending.")
        lines.append("")
    return "\n".join(lines).rstrip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check that the index is up to date.")
    args = parser.parse_args()

    readme = ROOT / "README.md"
    original = readme.read_text(encoding="utf-8")
    before, start, remainder = original.partition(START)
    _, end, after = remainder.partition(END)
    if not start or not end or START in remainder or END in after:
        raise ValueError("README.md needs one pair of book index markers")

    updated = f"{before}{START}\n\n{index_lines()}\n\n{END}{after}"
    if args.check:
        if original != updated:
            sys.exit("README book index is out of date. Run python3 scripts/update_book_index.py.")
    elif original != updated:
        readme.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, yaml.YAMLError) as error:
        sys.exit(str(error))
