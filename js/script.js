"use strict";

/* ========================================
   PORTFOLIO INTERACTION ENGINE
======================================== */

(() => {

    /* ========================================
       PROJECT COLLECTION FILTERING
    ======================================== */

    function initializeProjectFilters() {

        const filterButtons = [
            ...document.querySelectorAll(
                ".project-filters .filter-btn"
            )
        ];

        const projectCards = [
            ...document.querySelectorAll(
                ".premium-project-grid .premium-project-card"
            )
        ];

        if (!filterButtons.length) return;

        const projectResults =
            document.getElementById("projectResults");

        const projectEmptyState =
            document.getElementById("projectEmptyState");

        const resetButton =
            document.getElementById("resetProjectFilters");

        const collectionCount =
            document.getElementById("projectCollectionCount");

        // Cache project categories once.

        const projects = projectCards.map(card => ({
            element: card,
            categories: (card.dataset.category || "")
                .trim()
                .split(/\s+/)
                .filter(Boolean)
        }));

        let activeFilter = null;

        function filterProjects(filter = "all") {

            if (activeFilter === filter) return;

            activeFilter = filter;

            let visibleCount = 0;

            filterButtons.forEach(button => {

                const isActive =
                    button.dataset.filter === filter;

                button.classList.toggle("active", isActive);

                button.setAttribute(
                    "aria-pressed",
                    String(isActive)
                );

            });

            projects.forEach(project => {

                const isVisible =
                    filter === "all" ||
                    project.categories.includes(filter);

                project.element.hidden = !isVisible;

                if (isVisible) visibleCount++;

            });

            if (projectResults) {

                const label =
                    visibleCount === 1
                        ? "project"
                        : "projects";

                projectResults.textContent =
                    `Showing ${visibleCount} ${label}`;

            }

            if (projectEmptyState) {

                projectEmptyState.hidden =
                    visibleCount !== 0;

            }

        }

        filterButtons.forEach(button => {

            button.addEventListener("click", () => {

                filterProjects(
                    button.dataset.filter || "all"
                );

            });

        });

        if (resetButton) {

            resetButton.addEventListener("click", () => {

                filterProjects("all");

                filterButtons
                    .find(button =>
                        button.dataset.filter === "all"
                    )
                    ?.focus();

            });

        }

        if (collectionCount) {

            collectionCount.textContent =
                `${String(projects.length).padStart(2, "0")} PROJECTS`;

        }

        filterProjects("all");

    }


    /* ========================================
       SCROLL REVEAL
    ======================================== */

    function initializeScrollReveal() {

        const revealElements =
            document.querySelectorAll(".reveal");

        if (!revealElements.length) return;

        const reducedMotion = window.matchMedia(
            "(prefers-reduced-motion: reduce)"
        );

        if (
            reducedMotion.matches ||
            !("IntersectionObserver" in window)
        ) {

            revealElements.forEach(element => {

                element.classList.add("active");

            });

            return;

        }

        const observer = new IntersectionObserver(
            entries => {

                entries.forEach(entry => {

                    if (!entry.isIntersecting) return;

                    entry.target.classList.add("active");

                    observer.unobserve(entry.target);

                });

            },
            {
                threshold: 0.05
            }
        );

        revealElements.forEach(element => {

            observer.observe(element);

        });

    }


    /* ========================================
       ACTIVE NAVIGATION
    ======================================== */

    function initializeActiveNavigation() {

        const sections = [
            ...document.querySelectorAll("section[id]")
        ];

        const navLinks = [
            ...document.querySelectorAll(
                '.nav-menu a[href^="#"]'
            )
        ];

        if (!sections.length || !navLinks.length) return;

        let activeSection = null;
        let framePending = false;

        function updateActiveNavigation() {

            let currentSection = "";

            for (const section of sections) {

                if (
                    section.getBoundingClientRect().top <= 160
                ) {

                    currentSection = section.id;

                }

            }

            if (currentSection === activeSection) return;

            activeSection = currentSection;

            navLinks.forEach(link => {

                const isActive =
                    link.getAttribute("href") ===
                    `#${currentSection}`;

                link.classList.toggle("active", isActive);

                if (isActive) {

                    link.setAttribute(
                        "aria-current",
                        "location"
                    );

                } else {

                    link.removeAttribute("aria-current");

                }

            });

        }

        function scheduleNavigationUpdate() {

            if (framePending) return;

            framePending = true;

            window.requestAnimationFrame(() => {

                updateActiveNavigation();

                framePending = false;

            });

        }

        window.addEventListener(
            "scroll",
            scheduleNavigationUpdate,
            { passive: true }
        );

        window.addEventListener(
            "resize",
            scheduleNavigationUpdate
        );

        window.addEventListener(
            "load",
            scheduleNavigationUpdate
        );

        updateActiveNavigation();

    }


    /* ========================================
       MOBILE NAVIGATION
    ======================================== */

    function initializeMobileNavigation() {

        const menuButton =
            document.querySelector(".mobile-menu-btn");

        const navMenu =
            document.querySelector(".nav-menu");

        if (!menuButton || !navMenu) return;

        const desktopViewport = window.matchMedia(
            "(min-width: 801px)"
        );

        function setMenuState(
            isOpen,
            restoreFocus = false
        ) {

            navMenu.classList.toggle("active", isOpen);

            menuButton.setAttribute(
                "aria-expanded",
                String(isOpen)
            );

            menuButton.setAttribute(
                "aria-label",
                isOpen
                    ? "Close navigation menu"
                    : "Open navigation menu"
            );

            menuButton.textContent =
                isOpen
                    ? "\u2715"
                    : "\u2630";

            if (restoreFocus) {

                menuButton.focus();

            }

        }

        menuButton.addEventListener("click", () => {

            const isOpen =
                navMenu.classList.contains("active");

            setMenuState(!isOpen);

        });

        navMenu.addEventListener("click", event => {

            if (event.target.closest("a")) {

                setMenuState(false);

            }

        });

        document.addEventListener("keydown", event => {

            if (
                event.key === "Escape" &&
                navMenu.classList.contains("active")
            ) {

                setMenuState(false, true);

            }

        });

        // Close the menu when clicking outside it.

        document.addEventListener("click", event => {

            if (!navMenu.classList.contains("active")) return;

            const clickedInsideMenu =
                navMenu.contains(event.target);

            const clickedMenuButton =
                menuButton.contains(event.target);

            if (
                !clickedInsideMenu &&
                !clickedMenuButton
            ) {

                setMenuState(false);

            }

        });

        // Reset mobile state when switching to desktop.

        function handleViewportChange(event) {

            if (event.matches) {

                setMenuState(false);

            }

        }

        if (desktopViewport.addEventListener) {

            desktopViewport.addEventListener(
                "change",
                handleViewportChange
            );

        } else if (desktopViewport.addListener) {

            desktopViewport.addListener(
                handleViewportChange
            );

        }

        setMenuState(false);

    }


    /* ========================================
       APPLICATION INITIALIZATION
    ======================================== */

    function initializePortfolio() {

        initializeProjectFilters();

        initializeScrollReveal();

        initializeActiveNavigation();

        initializeMobileNavigation();

    }

    if (document.readyState === "loading") {

        document.addEventListener(
            "DOMContentLoaded",
            initializePortfolio,
            { once: true }
        );

    } else {

        initializePortfolio();

    }

})();

/* ========================================
   END OF PORTFOLIO INTERACTION ENGINE
======================================== */