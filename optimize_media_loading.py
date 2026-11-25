from pathlib import Path
from urllib.parse import urlsplit, unquote
from html.parser import HTMLParser
import re

from PIL import Image


# ========================================
# CONFIGURATION
# ========================================

ROOT = Path(__file__).resolve().parent

HTML_FILES = [
    ROOT / "index.html",
    *sorted((ROOT / "projects").rglob("*.html"))
]


# ========================================
# HTML MEDIA PARSER
# ========================================

class MediaOptimizer(HTMLParser):

    def __init__(self, file_path, content):

        super().__init__(convert_charrefs=False)

        self.file_path = file_path
        self.content = content

        self.lines = content.splitlines(keepends=True)

        self.replacements = []

        self.images_updated = 0
        self.videos_updated = 0
        self.missing_assets = 0

        self.image_count = 0


    def handle_starttag(self, tag, attrs):

        if tag not in {"img", "video"}:
            return

        original_tag = self.get_starttag_text()

        attributes = dict(attrs)

        additions = {}


        # ========================================
        # IMAGE OPTIMIZATION
        # ========================================

        if tag == "img":

            self.image_count += 1

            source = attributes.get("src")

            if not source:
                return

            parsed = urlsplit(source)

            if parsed.scheme or parsed.netloc:
                return

            image_path = (
                self.file_path.parent
                / unquote(parsed.path)
            ).resolve()

            if not image_path.is_relative_to(ROOT):
                return

            if not image_path.is_file():

                self.missing_assets += 1

                print(
                    f"MISSING IMAGE | "
                    f"{self.file_path.name} | {source}"
                )

                return

            try:

                with Image.open(image_path) as image:

                    width, height = image.size

            except Exception as error:

                print(f"SKIPPED | {source} | {error}")

                return

            if (
                "width" not in attributes
                and "height" not in attributes
            ):

                additions["width"] = str(width)
                additions["height"] = str(height)

            # Keep the first case study image eager.
            # The homepage uses a CSS-based hero.

            is_priority_image = (
                self.file_path.name != "index.html"
                and self.image_count == 1
            )

            if "loading" not in attributes:

                additions["loading"] = (
                    "eager"
                    if is_priority_image
                    else "lazy"
                )

            if (
                "decoding" not in attributes
                and not is_priority_image
            ):

                additions["decoding"] = "async"

            if additions:

                self.images_updated += 1


        # ========================================
        # VIDEO OPTIMIZATION
        # ========================================

        elif tag == "video":

            if "preload" not in attributes:

                additions["preload"] = "none"

            if "playsinline" not in attributes:

                additions["playsinline"] = None

            if additions:

                self.videos_updated += 1


        # ========================================
        # PRESERVE EXISTING HTML
        # ========================================

        if not additions:
            return

        attribute_text = ""

        for key, value in additions.items():

            if value is None:

                attribute_text += f" {key}"

            else:

                attribute_text += f' {key}="{value}"'

        updated_tag = re.sub(
            r"(\s*/?>)$",
            lambda match: (
                attribute_text + match.group(1)
            ),
            original_tag,
            count=1
        )

        line, column = self.getpos()

        start = (
            sum(
                len(item)
                for item in self.lines[:line - 1]
            )
            + column
        )

        end = start + len(original_tag)

        self.replacements.append(
            (start, end, updated_tag)
        )


    def handle_startendtag(self, tag, attrs):

        self.handle_starttag(tag, attrs)


    def generate_updated_content(self):

        updated = self.content

        for start, end, replacement in sorted(
            self.replacements,
            reverse=True
        ):

            updated = (
                updated[:start]
                + replacement
                + updated[end:]
            )

        return updated


# ========================================
# MAIN ENGINE
# ========================================

def main():

    print("=" * 65)
    print("PORTFOLIO MEDIA LOADING OPTIMIZATION")
    print("=" * 65)

    total_images = 0
    total_videos = 0
    total_missing = 0
    total_files = 0

    for file_path in HTML_FILES:

        if not file_path.is_file():
            continue

        content = file_path.read_text(
            encoding="utf-8-sig"
        )

        optimizer = MediaOptimizer(
            file_path,
            content
        )

        optimizer.feed(content)
        optimizer.close()

        updated = optimizer.generate_updated_content()

        if updated != content:

            file_path.write_text(
                updated,
                encoding="utf-8"
            )

            total_files += 1

        total_images += optimizer.images_updated
        total_videos += optimizer.videos_updated
        total_missing += optimizer.missing_assets

        print(
            f"{file_path.relative_to(ROOT)} | "
            f"Images updated: {optimizer.images_updated} | "
            f"Videos updated: {optimizer.videos_updated}"
        )

    print("\n" + "=" * 65)
    print("MEDIA OPTIMIZATION SUMMARY")
    print("=" * 65)

    print(f"HTML files updated: {total_files}")
    print(f"Images updated: {total_images}")
    print(f"Videos updated: {total_videos}")
    print(f"Missing image references: {total_missing}")

    print("=" * 65)


if __name__ == "__main__":
    main()