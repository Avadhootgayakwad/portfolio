from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
from collections import Counter
import re


# ========================================
# CONFIGURATION
# ========================================

ROOT = Path(__file__).resolve().parent

HTML_FILES = [
    ROOT / "index.html",
    *sorted((ROOT / "projects").rglob("*.html"))
]

CSS_FILES = sorted(
    (ROOT / "css").rglob("*.css")
)

REFERENCED_FILES = set()
ISSUES = []
PLACEHOLDERS = []

STATS = Counter()


# ========================================
# VALIDATION UTILITIES
# ========================================

def relative_name(path):

    return path.relative_to(ROOT).as_posix()


def check_exact_case(path):

    try:

        parts = path.relative_to(ROOT).parts

    except ValueError:

        return False

    current = ROOT

    for part in parts:

        if not current.is_dir():
            return False

        names = {
            item.name
            for item in current.iterdir()
        }

        if part not in names:
            return False

        current = current / part

    return True


def validate_reference(source_file, reference):

    if not reference:
        return

    reference = reference.strip()

    if reference == "#":

        PLACEHOLDERS.append({
            "file": relative_name(source_file),
            "reference": reference
        })

        return

    parsed = urlsplit(reference)

    if (
        parsed.scheme
        or parsed.netloc
        or not parsed.path
    ):

        return

    STATS["references_checked"] += 1

    decoded_path = unquote(parsed.path)

    if decoded_path.startswith("/"):

        target = (
            ROOT / decoded_path.lstrip("/")
        ).resolve()

        STATS["root_relative_paths"] += 1

    else:

        target = (
            source_file.parent / decoded_path
        ).resolve()

    if not target.is_relative_to(ROOT):

        ISSUES.append({
            "type": "OUTSIDE PROJECT",
            "file": relative_name(source_file),
            "reference": reference
        })

        return

    if target.is_dir():

        target = target / "index.html"

    if not target.is_file():

        ISSUES.append({
            "type": "MISSING FILE",
            "file": relative_name(source_file),
            "reference": reference
        })

        return

    if not check_exact_case(target):

        ISSUES.append({
            "type": "CASE MISMATCH",
            "file": relative_name(source_file),
            "reference": reference
        })

        return

    REFERENCED_FILES.add(target)

    STATS["valid_references"] += 1


# ========================================
# HTML VALIDATION
# ========================================

class AssetParser(HTMLParser):

    def __init__(self, source_file):

        super().__init__()

        self.source_file = source_file


    def handle_starttag(self, tag, attrs):

        attributes = dict(attrs)

        for attribute in (
            "src",
            "href",
            "poster",
            "data"
        ):

            if attribute in attributes:

                validate_reference(
                    self.source_file,
                    attributes[attribute]
                )


    def handle_startendtag(self, tag, attrs):

        self.handle_starttag(tag, attrs)


# ========================================
# CSS VALIDATION
# ========================================

def validate_css(file_path):

    content = file_path.read_text(
        encoding="utf-8-sig"
    )

    content = re.sub(
        r"/\*.*?\*/",
        "",
        content,
        flags=re.DOTALL
    )

    references = re.findall(
        r"""url\(\s*['"]?([^'")]+)['"]?\s*\)""",
        content,
        flags=re.IGNORECASE
    )

    for reference in references:

        validate_reference(
            file_path,
            reference.strip()
        )


# ========================================
# UNUSED ASSET AUDIT
# ========================================

def find_unused_assets():

    asset_directories = [
        ROOT / "Images",
        ROOT / "Videos",
        ROOT / "Logos",
        ROOT / "assets"
    ]

    unused = []

    for directory in asset_directories:

        if not directory.is_dir():
            continue

        for path in directory.rglob("*"):

            if not path.is_file():
                continue

            if path.resolve() not in REFERENCED_FILES:

                unused.append(path)

    return sorted(unused)


# ========================================
# MAIN VALIDATION ENGINE
# ========================================

def main():

    print("=" * 65)
    print("PORTFOLIO ASSET VALIDATION ENGINE")
    print("=" * 65)

    for file_path in HTML_FILES:

        if not file_path.is_file():
            continue

        parser = AssetParser(file_path)

        parser.feed(
            file_path.read_text(
                encoding="utf-8-sig"
            )
        )

        parser.close()

        STATS["html_files"] += 1

        print(
            f"CHECKED HTML | "
            f"{relative_name(file_path)}"
        )

    for file_path in CSS_FILES:

        validate_css(file_path)

        STATS["css_files"] += 1

        print(
            f"CHECKED CSS  | "
            f"{relative_name(file_path)}"
        )


    # ========================================
    # VALIDATION ISSUES
    # ========================================

    print("\n" + "=" * 65)
    print("BROKEN ASSET REFERENCES")
    print("=" * 65)

    if not ISSUES:

        print("No broken local references detected.")

    else:

        for issue in ISSUES:

            print(
                f'{issue["type"]} | '
                f'{issue["file"]} | '
                f'{issue["reference"]}'
            )


    # ========================================
    # PLACEHOLDER LINKS
    # ========================================

    print("\n" + "=" * 65)
    print("PLACEHOLDER LINKS")
    print("=" * 65)

    if not PLACEHOLDERS:

        print("No placeholder links detected.")

    else:

        for item in PLACEHOLDERS:

            print(
                f'{item["file"]} | '
                f'{item["reference"]}'
            )


    # ========================================
    # UNUSED ASSETS
    # ========================================

    unused = find_unused_assets()

    unused_bytes = sum(
        path.stat().st_size
        for path in unused
    )

    print("\n" + "=" * 65)
    print("POTENTIALLY UNUSED ASSETS")
    print("=" * 65)

    for path in unused:

        size_kb = path.stat().st_size / 1024

        print(
            f"{relative_name(path)} | "
            f"{size_kb:.2f} KB"
        )


    # ========================================
    # FINAL SUMMARY
    # ========================================

    print("\n" + "=" * 65)
    print("ASSET VALIDATION SUMMARY")
    print("=" * 65)

    print(f'HTML files checked: {STATS["html_files"]}')

    print(f'CSS files checked: {STATS["css_files"]}')

    print(
        f'Local references checked: '
        f'{STATS["references_checked"]}'
    )

    print(
        f'Valid local references: '
        f'{STATS["valid_references"]}'
    )

    print(f"Broken references: {len(ISSUES)}")

    print(f"Placeholder links: {len(PLACEHOLDERS)}")

    print(
        f'Root-relative paths: '
        f'{STATS["root_relative_paths"]}'
    )

    print(
        f"Unique referenced files: "
        f"{len(REFERENCED_FILES)}"
    )

    print(
        f"Potentially unused assets: "
        f"{len(unused)}"
    )

    print(
        f"Potentially unused storage: "
        f"{unused_bytes / 1024 / 1024:.2f} MB"
    )

    print("\nNo files were modified or deleted.")

    print("=" * 65)


if __name__ == "__main__":
    main()