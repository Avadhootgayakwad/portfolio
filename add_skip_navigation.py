from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent

PAGES = [
    ROOT / "index.html",
    ROOT / "projects" / "insightpilot-ai.html",
    ROOT / "projects" / "global-superstore.html",
    ROOT / "projects" / "ai-document-analyzer.html",
    ROOT / "projects" / "sustainex-ecom.html"
]

SKIP_LINK = """
    <a href="#main-content" class="skip-link">
        Skip to main content
    </a>
"""


def main():

    print("=" * 65)
    print("ACCESSIBLE SKIP NAVIGATION")
    print("=" * 65)

    updated = 0
    skipped = 0
    failed = 0

    for path in PAGES:

        if not path.is_file():

            print(f"MISSING | {path.name}")

            failed += 1
            continue

        html = path.read_text(
            encoding="utf-8-sig"
        )

        if (
            'class="skip-link"' in html
            and 'id="main-content"' in html
        ):

            print(f"ALREADY EXISTS | {path.name}")

            skipped += 1
            continue

        body_matches = list(
            re.finditer(
                r"<body\b[^>]*>",
                html,
                flags=re.IGNORECASE
            )
        )

        main_matches = list(
            re.finditer(
                r"<main\b[^>]*>",
                html,
                flags=re.IGNORECASE
            )
        )

        if (
            len(body_matches) != 1
            or len(main_matches) != 1
        ):

            print(
                f"MANUAL REVIEW REQUIRED | {path.name}"
            )

            failed += 1
            continue

        main_tag = main_matches[0].group()

        if (
            re.search(r"\bid\s*=", main_tag)
            or re.search(r"\btabindex\s*=", main_tag)
            or 'id="main-content"' in html
            or 'class="skip-link"' in html
        ):

            print(
                f"EXISTING ATTRIBUTES | {path.name}"
            )

            failed += 1
            continue

        updated_html = re.sub(
            r"<main\b([^>]*)>",
            r'<main\1 id="main-content" tabindex="-1">',
            html,
            count=1,
            flags=re.IGNORECASE
        )

        updated_html = re.sub(
            r"<body\b[^>]*>",
            lambda match: match.group() + "\n" + SKIP_LINK,
            updated_html,
            count=1,
            flags=re.IGNORECASE
        )

        path.write_text(
            updated_html,
            encoding="utf-8"
        )

        print(f"UPDATED | {path.name}")

        updated += 1

    print("\n" + "=" * 65)
    print("IMPLEMENTATION SUMMARY")
    print("=" * 65)

    print(f"Pages updated: {updated}")
    print(f"Already configured: {skipped}")
    print(f"Require manual review: {failed}")

    print("=" * 65)


if __name__ == "__main__":

    main()