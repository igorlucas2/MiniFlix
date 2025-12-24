const normalizeText = (value) =>
    value
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "");

document.addEventListener("DOMContentLoaded", () => {
    const searchInput = document.querySelector("[data-search-input]");
    if (!searchInput) {
        return;
    }

    const cards = Array.from(document.querySelectorAll("[data-search-card]"));
    const emptyState = document.querySelector("[data-search-empty]");

    const filterCards = () => {
        const term = normalizeText(searchInput.value.trim());
        let visible = 0;

        cards.forEach((card) => {
            const name = normalizeText(card.dataset.name || "");
            const show = !term || name.includes(term);
            card.style.display = show ? "" : "none";
            if (show) {
                visible += 1;
            }
        });

        if (emptyState) {
            emptyState.classList.toggle("hidden", visible > 0);
        }
    };

    searchInput.addEventListener("input", filterCards);
});
