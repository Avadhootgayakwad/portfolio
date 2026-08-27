const filterButtons = document.querySelectorAll(".filter-btn");
const projectCards = document.querySelectorAll(".project-card");

filterButtons.forEach(button => {

    button.addEventListener("click", () => {

        const filter = button.dataset.filter;


        // Remove active state
        filterButtons.forEach(btn => {
            btn.classList.remove("active");
        });


        // Add active state
        button.classList.add("active");


        // Filter projects
        projectCards.forEach(card => {

            const category = card.dataset.category;


            if (filter === "all" || category === filter) {

                card.style.display = "block";

            } else {

                card.style.display = "none";

            }

        });

    });

});
/* ================================
   SCROLL REVEAL
================================ */

const revealElements =
    document.querySelectorAll(".reveal");

const revealObserver =
    new IntersectionObserver(

        (entries) => {

            entries.forEach(entry => {

                if (entry.isIntersecting) {

                    entry.target.classList.add("active");

                    revealObserver.unobserve(entry.target);

                }

            });

        },

        {
            threshold: 0.15
        }

    );


revealElements.forEach(element => {

    revealObserver.observe(element);

});
/* ================================
   ACTIVE NAVIGATION
================================ */

const sections =
    document.querySelectorAll("section[id]");

const navLinks =
    document.querySelectorAll(".nav-link");


window.addEventListener("scroll", () => {

    let current = "";

    sections.forEach(section => {

        const sectionTop =
            section.offsetTop - 150;

        const sectionHeight =
            section.offsetHeight;

        if (
            window.scrollY >= sectionTop &&
            window.scrollY < sectionTop + sectionHeight
        ) {

            current = section.getAttribute("id");

        }

    });


    navLinks.forEach(link => {

        link.classList.remove("active");

        if (
            link.getAttribute("href") ===
            `#${current}`
        ) {

            link.classList.add("active");

        }

    });

});
/* ================================
   MOBILE NAVIGATION
================================ */

const mobileMenuBtn =
    document.querySelector(".mobile-menu-btn");

const navMenu =
    document.querySelector(".nav-menu");


if (mobileMenuBtn && navMenu) {

    mobileMenuBtn.addEventListener("click", () => {

        const isOpen =
            navMenu.classList.toggle("active");

        mobileMenuBtn.setAttribute(
            "aria-expanded",
            isOpen
        );

        mobileMenuBtn.textContent =
            isOpen ? "✕" : "☰";

    });


    // Close menu after clicking a link

    navMenu.querySelectorAll("a").forEach(link => {

        link.addEventListener("click", () => {

            navMenu.classList.remove("active");

            mobileMenuBtn.setAttribute(
                "aria-expanded",
                "false"
            );

            mobileMenuBtn.textContent = "☰";

        });

    });

}