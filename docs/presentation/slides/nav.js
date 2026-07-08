(function () {
    const prevFile = document.documentElement.dataset.slidePrev || "";
    const nextFile = document.documentElement.dataset.slideNext || "";

    const urlParams = new URLSearchParams(window.location.search);
    const mode = urlParams.get("mode") || "first";

    // Récupère tous les éléments avec une classe page-N
    const allPageElements = Array.from(document.querySelectorAll('[class*="page-"]')).filter((el) =>
        /page-\d+/.test(el.className)
    );

    // Groupe par numéro de page
    const groups = new Map();
    for (const el of allPageElements) {
        const match = el.className.match(/page-(\d+)/);
        if (match) {
            const num = parseInt(match[1], 10);
            if (!groups.has(num)) {
                groups.set(num, []);
            }
            groups.get(num).push(el);
        }
    }

    const sortedKeys = Array.from(groups.keys()).sort((a, b) => a - b);
    const pageGroups = sortedKeys.map((key) => groups.get(key));
    const totalPages = pageGroups.length;

    // État : combien de groupes sont actuellement visibles (1 = premier groupe seulement)
    let visibleCount = 1; // par défaut, la première page est visible

    function showPagesUpTo(count) {
        // count = nombre de groupes visibles (1 → page 1, 2 → pages 1 et 2, etc.)
        for (let i = 0; i < pageGroups.length; i++) {
            const visible = i < count;
            for (const el of pageGroups[i]) {
                el.style.opacity = visible ? "1" : "0";
                el.style.pointerEvents = visible ? "auto" : "none";
            }
        }
        document.documentElement.dataset.slidePage = count;
        visibleCount = count;
    }

    // --- INITIALISATION ---
    if (totalPages === 0) {
        document.addEventListener("keydown", function (e) {
            if (e.key === "ArrowDown" || e.key === "ArrowRight") {
                if (nextFile) location.href = nextFile + "?mode=first";
            } else if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
                if (prevFile) location.href = prevFile + "?mode=all";
            }
        });
        return;
    }

    // Initialisation : mode 'all' → toutes les pages, sinon juste la première
    if (mode === "all") {
        showPagesUpTo(totalPages);
    } else {
        showPagesUpTo(1);
    }

    // --- GESTION DES TOUCHES ---
    document.addEventListener("keydown", function (e) {
        if (e.key === "ArrowDown" || e.key === "ArrowRight") {
            if (visibleCount < totalPages) {
                showPagesUpTo(visibleCount + 1);
            } else if (nextFile) {
                location.href = nextFile + "?mode=first";
            }
        } else if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
            if (visibleCount > 1) {
                showPagesUpTo(visibleCount - 1);
            } else if (prevFile) {
                location.href = prevFile + "?mode=all";
            }
        }
    });
})();
