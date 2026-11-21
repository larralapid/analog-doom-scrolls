#!/usr/bin/env python3
"""Refresh copy-ready TikTok posts and the README from the Books table in each post."""

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

import yaml


ROOT = Path(__file__).resolve().parents[1]
START = "<!-- book-index:start -->"
END = "<!-- book-index:end -->"


def archive_updates():
    updates = {}
    total = 0
    haul_count = 0
    lines = []
    for path in sorted(ROOT.glob("[0-9][0-9][0-9]/post.md")):
        haul = path.parent.name
        original = path.read_text(encoding="utf-8")
        match = re.match(r"\A---\n(.*?)\n---\n", original, re.DOTALL)
        if not match:
            raise ValueError(f"{haul}/post.md needs YAML frontmatter")

        data = yaml.safe_load(match[1])
        if not isinstance(data, dict) or data.get("haul") != haul:
            raise ValueError(f"{haul}/post.md needs a matching quoted haul number")

        number = haul
        publish_url = data.get("publish_url")
        if data.get("status") == "published":
            if not data.get("publish_date") or not isinstance(publish_url, str):
                raise ValueError(f"{haul}/post.md needs a publish date and TikTok URL")
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
                raise ValueError(f"{haul}/post.md needs a TikTok post URL")
            number = f"[{haul}]({publish_url})"

        body = original[match.end():]
        block = re.match(
            rf"\s*# Haul {haul}\n\n```text\n(?P<count>[^\n]*)\n\n(?P<books>.*?)\n```(?:\n|$)",
            body,
            re.DOTALL,
        )
        if not block:
            raise ValueError(f"{path} needs a count, a blank line, and a book list under its heading")
        section = re.search(
            r"^## Books\n+\| title \| author \| page_photo \|\n"
            r"\|[-: |]+\|\n(?P<rows>(?:\|[^\n]*\|(?:\n|$))+)", body, re.MULTILINE
        )
        if not section:
            raise ValueError(f"{path} needs a Books table with title, author, and page_photo columns")
        books = []
        for row in section["rows"].splitlines():
            cells = re.split(r"(?<!\\)\|", row[1:-1])
            if len(cells) != 3 or not all(cell.strip() for cell in cells[:2]):
                raise ValueError(f"{path} has an incomplete Books row: {row}")
            title, author = (cell.strip().replace(r"\|", "|") for cell in cells[:2])
            books.append(f"{title} — {author}")
        count = f"{len(books)} {'book' if len(books) == 1 else 'books'}"
        total += len(books)
        haul_count += 1
        count_line = f"{count} this haul | {total} total {'checkout' if total == 1 else 'checkouts'}"
        start, end = block.start("count"), block.end("books")
        updates[path] = match[0] + body[:start] + count_line + "\n\n" + "\n".join(books) + body[end:]
        lines.extend([
            f'<a id="haul-{haul}"></a>',
            "<details>",
            f"<summary><samp>{haul} · {count} · {total} total checkouts</samp></summary>",
            "",
            f"[Copy post]({haul}/post.md) · [Files]({haul}/)" +
            (f" · {number}" if number != haul else ""),
            "",
            *[f"- {line}" for line in books],
            "",
            "</details>",
            "",
        ])
    summary = f"**{haul_count} hauls · {total} total checkouts**"
    return updates, summary + "\n\n" + "\n".join(lines).rstrip()


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

    updates, index = archive_updates()
    updates[readme] = f"{before}{START}\n\n{index}\n\n{END}{after}"
    stale = [path for path, content in updates.items() if path.read_text(encoding="utf-8") != content]
    if args.check and stale:
        sys.exit("Run python3 scripts/update_book_index.py to refresh " + ", ".join(str(p.relative_to(ROOT)) for p in stale))
    for path in stale:
        path.write_text(updates[path], encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, yaml.YAMLError) as error:
        sys.exit(str(error))
