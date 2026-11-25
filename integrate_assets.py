from pathlib import Path
import csv
import shutil
import re


# ========================================
# CONFIGURATION
# ========================================

ROOT = Path(__file__).resolve().parent

REPORT = (
    ROOT
    / "optimized_assets"
    / "reports"
    / "image_optimization_report.csv"
)

SOURCE_FILES = [
    ROOT / "index.html",
    *sorted((ROOT / "projects").rglob("*.html")),
    *sorted((ROOT / "css").rglob("*.css")),
    *sorted((ROOT / "js").rglob("*.js")),
]


# ========================================
# VALIDATION
# ========================================

if not REPORT.is_file():
    raise SystemExit("Optimization report not found.")


# ========================================
# INTEGRATION ENGINE
# ========================================

def main():

    print("=" * 65)
    print("PORTFOLIO WEBP INTEGRATION ENGINE")
    print("=" * 65)

    with REPORT.open(
        encoding="utf-8",
        newline=""
    ) as file:

        records = list(csv.DictReader(file))

    optimized_records = [
        record
        for record in records
        if record["status"] == "OPTIMIZED"
    ]

    source_contents = {
        path: path.read_text(encoding="utf-8-sig")
        for path in SOURCE_FILES
        if path.is_file()
    }

    updated_files = set()

    integrated_count = 0
    reference_count = 0
    skipped_count = 0
    total_saved = 0

    for record in optimized_records:

        relative_path = Path(record["file"])

        original = ROOT / "Images" / relative_path

        optimized = ROOT / record["output_path"]

        destination = original.with_suffix(".webp")

        old_reference = (
            "Images/" + relative_path.as_posix()
        )

        new_reference = (
            "Images/"
            + relative_path.with_suffix(".webp").as_posix()
        )

        if not original.is_file():
            print(f"SKIPPED | Missing original: {relative_path}")
            skipped_count += 1
            continue

        if not optimized.is_file():
            print(f"SKIPPED | Missing WebP: {relative_path}")
            skipped_count += 1
            continue

        if destination.exists():
            if destination.read_bytes() != optimized.read_bytes():
                print(f"SKIPPED | Destination conflict: {relative_path}")
                skipped_count += 1
                continue

        matches = {}

        pattern = (
            re.escape(old_reference)
            + r"""(?=["'\s?#)]|$)"""
        )

        for path, content in source_contents.items():

            count = len(re.findall(pattern, content))

            if count:
                matches[path] = count

        if not matches:

            print(f"UNUSED | {relative_path}")

            skipped_count += 1

            continue

        # Copy only images referenced by the portfolio.

        shutil.copy2(optimized, destination)

        for path, count in matches.items():

            source_contents[path] = re.sub(
                pattern,
                lambda match: new_reference,
                source_contents[path]
            )

            updated_files.add(path)

            reference_count += count

        integrated_count += 1

        total_saved += (
            original.stat().st_size
            - destination.stat().st_size
        )

        print(
            f"INTEGRATED | {relative_path} "
            f"-> {destination.name}"
        )

    # Save updated source files.

    for path in sorted(updated_files):

        path.write_text(
            source_contents[path],
            encoding="utf-8"
        )

        print(
            f"UPDATED SOURCE | "
            f"{path.relative_to(ROOT)}"
        )

    print("\n" + "=" * 65)
    print("INTEGRATION SUMMARY")
    print("=" * 65)

    print(f"Images integrated: {integrated_count}")
    print(f"Images skipped: {skipped_count}")
    print(f"References updated: {reference_count}")
    print(f"Source files updated: {len(updated_files)}")

    print(
        f"Potential delivery savings: "
        f"{total_saved / 1024:.2f} KB"
    )

    print("\nOriginal images remain unchanged.")

    print("=" * 65)


if __name__ == "__main__":
    main()