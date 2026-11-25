from pathlib import Path
from collections import Counter
from playwright.sync_api import sync_playwright
import json


# ========================================
# CONFIGURATION
# ========================================

ROOT = Path(__file__).resolve().parent

BASE_URL = "http://127.0.0.1:5500"

AXE_SCRIPT = (
    ROOT
    / "node_modules"
    / "axe-core"
    / "axe.min.js"
)

REPORT_DIR = ROOT / "accessibility_audit"

REPORT_DIR.mkdir(
    parents=True,
    exist_ok=True
)

PAGES = {
    "homepage": "/index.html",

    "insightpilot-ai":
        "/projects/insightpilot-ai.html",

    "global-superstore":
        "/projects/global-superstore.html",

    "ai-document-analyzer":
        "/projects/ai-document-analyzer.html",

    "sustainex":
        "/projects/sustainex-ecom.html"
}

VIEWPORTS = {
    "desktop": {
        "width": 1440,
        "height": 900
    },

    "mobile": {
        "width": 390,
        "height": 844
    }
}

WCAG_TAGS = [
    "wcag2a",
    "wcag2aa",
    "wcag21a",
    "wcag21aa",
    "wcag22a",
    "wcag22aa"
]


# ========================================
# ACCESSIBILITY ENGINE
# ========================================

def main():

    print("=" * 65)
    print("PORTFOLIO ACCESSIBILITY AUDIT ENGINE")
    print("=" * 65)

    if not AXE_SCRIPT.is_file():

        raise SystemExit(
            "axe-core is missing. Install it using npm."
        )

    results = []

    impact_counts = Counter()

    rule_counts = Counter()

    total_violations = 0

    total_affected_elements = 0

    total_incomplete = 0

    execution_errors = 0

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(
            headless=True
        )

        for page_name, page_path in PAGES.items():

            print(f"\nPAGE: {page_name}")

            for device, viewport in VIEWPORTS.items():

                page = browser.new_page(
                    viewport=viewport,
                    reduced_motion="reduce"
                )

                try:

                    response = page.goto(
                        BASE_URL + page_path,
                        wait_until="load",
                        timeout=30000
                    )

                    if response is None:

                        raise RuntimeError(
                            "No server response."
                        )

                    if response.status >= 400:

                        raise RuntimeError(
                            f"HTTP {response.status}"
                        )

                    page.evaluate(
                        """
                        async () => {
                            await document.fonts.ready;
                        }
                        """
                    )

                    # Reveal scroll-based content.

                    page.evaluate(
                        """
                        async () => {

                            const delay = ms =>
                                new Promise(
                                    resolve =>
                                        setTimeout(resolve, ms)
                                );

                            for (
                                let y = 0;
                                y < document.body.scrollHeight;
                                y += window.innerHeight
                            ) {

                                window.scrollTo(0, y);

                                await delay(100);

                            }

                            window.scrollTo(0, 0);

                        }
                        """
                    )

                    page.wait_for_timeout(500)

                    # Inject axe-core locally.

                    page.add_script_tag(
                        path=str(AXE_SCRIPT)
                    )

                    # Run WCAG accessibility checks.

                    audit = page.evaluate(
                        """
                        async (tags) => {

                            return await axe.run(
                                document,
                                {
                                    runOnly: {
                                        type: "tag",
                                        values: tags
                                    }
                                }
                            );

                        }
                        """,
                        WCAG_TAGS
                    )

                    violations = audit["violations"]

                    incomplete = audit["incomplete"]

                    affected_elements = sum(
                        len(rule["nodes"])
                        for rule in violations
                    )

                    total_violations += len(violations)

                    total_affected_elements += (
                        affected_elements
                    )

                    total_incomplete += len(incomplete)

                    status = (
                        "PASS"
                        if not violations
                        else "FAIL"
                    )

                    results.append({
                        "page": page_name,
                        "device": device,
                        "viewport": viewport,
                        "status": status,
                        "violations": violations,
                        "incomplete": incomplete,
                        "passes": len(audit["passes"]),
                        "inapplicable": len(
                            audit["inapplicable"]
                        )
                    })

                    print(
                        f"{device.upper():8} | "
                        f"{status:5} | "
                        f"Violations: {len(violations)} | "
                        f"Affected elements: "
                        f"{affected_elements} | "
                        f"Manual review: {len(incomplete)}"
                    )

                    for violation in violations:

                        impact = (
                            violation.get("impact")
                            or "unknown"
                        )

                        impact_counts[impact] += 1

                        rule_counts[
                            violation["id"]
                        ] += 1

                        print(
                            f"  [{impact.upper()}] "
                            f'{violation["id"]}'
                        )

                        print(
                            f'  {violation["help"]}'
                        )

                        print(
                            f'  Elements: '
                            f'{len(violation["nodes"])}'
                        )

                except Exception as error:

                    execution_errors += 1

                    results.append({
                        "page": page_name,
                        "device": device,
                        "status": "ERROR",
                        "error": str(error)
                    })

                    print(
                        f"ERROR | {device} | {error}"
                    )

                finally:

                    page.close()

        browser.close()

    report_path = (
        REPORT_DIR
        / "accessibility_report.json"
    )

    report_path.write_text(
        json.dumps(
            results,
            indent=4
        ),
        encoding="utf-8"
    )

    passed = sum(
        result["status"] == "PASS"
        for result in results
    )

    failed = sum(
        result["status"] == "FAIL"
        for result in results
    )

    print("\n" + "=" * 65)
    print("VIOLATIONS BY SEVERITY")
    print("=" * 65)

    for impact in [
        "critical",
        "serious",
        "moderate",
        "minor",
        "unknown"
    ]:

        print(
            f"{impact.capitalize():10}: "
            f"{impact_counts[impact]}"
        )

    print("\n" + "=" * 65)
    print("VIOLATIONS BY RULE")
    print("=" * 65)

    for rule, count in rule_counts.most_common():

        print(f"{rule}: {count}")

    print("\n" + "=" * 65)
    print("ACCESSIBILITY AUDIT SUMMARY")
    print("=" * 65)

    print(f"Pages tested: {len(PAGES)}")

    print(
        f"Device configurations: "
        f"{len(VIEWPORTS)}"
    )

    print(f"Total tests: {len(results)}")

    print(f"Passed: {passed}")

    print(f"Failed: {failed}")

    print(f"Execution errors: {execution_errors}")

    print(
        f"Total rule violations: "
        f"{total_violations}"
    )

    print(
        f"Total affected elements: "
        f"{total_affected_elements}"
    )

    print(
        f"Manual review rule results: "
        f"{total_incomplete}"
    )

    print(f"\nReport: {report_path}")

    print("\nNo portfolio source files were modified.")

    print("=" * 65)


if __name__ == "__main__":

    main()