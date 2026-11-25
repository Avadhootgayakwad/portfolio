from pathlib import Path
from playwright.sync_api import sync_playwright
import json


# ========================================
# CONFIGURATION
# ========================================

ROOT = Path(__file__).resolve().parent

BASE_URL = "http://127.0.0.1:5500"

REPORT_DIR = ROOT / "responsive_audit"

SCREENSHOT_DIR = REPORT_DIR / "screenshots"

SCREENSHOT_DIR.mkdir(
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

VIEWPORTS = [
    (1920, 1080),
    (1440, 900),
    (1366, 768),
    (1024, 768),
    (768, 1024),
    (430, 932),
    (390, 844),
    (360, 800),
    (320, 568)
]


# ========================================
# RESPONSIVE ANALYSIS
# ========================================

ANALYSIS_SCRIPT = """
() => {

    const viewportWidth =
        document.documentElement.clientWidth;

    const documentWidth =
        document.documentElement.scrollWidth;

    const bodyWidth =
        document.body.scrollWidth;

    const overflowingElements = [];

    document.querySelectorAll("body *")
        .forEach(element => {

            const style =
                window.getComputedStyle(element);

            if (
                style.display === "none" ||
                style.visibility === "hidden"
            ) {
                return;
            }

            const rect =
                element.getBoundingClientRect();

            if (
                rect.width === 0 ||
                rect.height === 0
            ) {
                return;
            }

            if (
                rect.right > viewportWidth + 2 ||
                rect.left < -2
            ) {

                overflowingElements.push({

                    tag: element.tagName,

                    id: element.id || "",

                    className:
                        element.getAttribute("class") || "",

                    width:
                        Math.round(rect.width),

                    left:
                        Math.round(rect.left),

                    right:
                        Math.round(rect.right),

                    position:
                        style.position

                });

            }

        });

    const brokenImages = Array.from(
        document.images
    ).filter(image => {

        return image.complete &&
               image.naturalWidth === 0;

    }).map(image => image.getAttribute("src"));

    return {

        viewportWidth,

        documentWidth,

        bodyWidth,

        horizontalOverflow:
            documentWidth > viewportWidth + 2 ||
            bodyWidth > viewportWidth + 2,

        overflowCount:
            overflowingElements.length,

        overflowingElements:
            overflowingElements.slice(0, 30),

        brokenImages

    };

}
"""


# ========================================
# MAIN ENGINE
# ========================================

def main():

    print("=" * 65)
    print("PORTFOLIO RESPONSIVE AUDIT ENGINE")
    print("=" * 65)

    results = []

    with sync_playwright() as playwright:

        browser = playwright.chromium.launch(
            headless=True
        )

        for page_name, page_path in PAGES.items():

            print(f"\nPAGE: {page_name}")

            for width, height in VIEWPORTS:

                page = browser.new_page(
                    viewport={
                        "width": width,
                        "height": height
                    },
                    device_scale_factor=1,
                    reduced_motion="reduce"
                )

                errors = []

                page.on(
                    "pageerror",
                    lambda error:
                        errors.append(str(error))
                )

                try:

                    response = page.goto(
                        BASE_URL + page_path,
                        wait_until="load",
                        timeout=30000
                    )

                    if response is None:

                        raise RuntimeError(
                            "No server response"
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

                    # Trigger lazy-loaded content
                    # and scroll-based reveal effects.

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

                    page.wait_for_timeout(1000)

                    analysis = page.evaluate(
                        ANALYSIS_SCRIPT
                    )

                    screenshot_path = (
                        SCREENSHOT_DIR /
                        f"{page_name}-{width}x{height}.png"
                    )

                    page.screenshot(
                        path=str(screenshot_path),
                        full_page=True,
                        animations="disabled"
                    )

                    status = "PASS"

                    if (
                        analysis["horizontalOverflow"]
                        or analysis["brokenImages"]
                        or errors
                    ):

                        status = "FAIL"

                    elif analysis["overflowCount"]:

                        status = "REVIEW"

                    result = {
                        "page": page_name,
                        "width": width,
                        "height": height,
                        "status": status,
                        "javascriptErrors": errors,
                        **analysis
                    }

                    results.append(result)

                    print(
                        f"{status:8} | "
                        f"{width}x{height} | "
                        f"Overflow elements: "
                        f'{analysis["overflowCount"]} | '
                        f"Broken images: "
                        f'{len(analysis["brokenImages"])}'
                    )

                except Exception as error:

                    results.append({
                        "page": page_name,
                        "width": width,
                        "height": height,
                        "status": "ERROR",
                        "error": str(error)
                    })

                    print(
                        f"ERROR | "
                        f"{width}x{height} | "
                        f"{error}"
                    )

                finally:

                    page.close()

        browser.close()

    report_path = (
        REPORT_DIR /
        "responsive_report.json"
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

    review = sum(
        result["status"] == "REVIEW"
        for result in results
    )

    failed = sum(
        result["status"] == "FAIL"
        for result in results
    )

    errors = sum(
        result["status"] == "ERROR"
        for result in results
    )

    print("\n" + "=" * 65)
    print("RESPONSIVE AUDIT SUMMARY")
    print("=" * 65)

    print(f"Pages tested: {len(PAGES)}")
    print(f"Viewport configurations: {len(VIEWPORTS)}")
    print(f"Total tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Require review: {review}")
    print(f"Failed: {failed}")
    print(f"Execution errors: {errors}")

    print(f"\nReport: {report_path}")
    print(f"Screenshots: {SCREENSHOT_DIR}")

    print("=" * 65)


if __name__ == "__main__":

    main()