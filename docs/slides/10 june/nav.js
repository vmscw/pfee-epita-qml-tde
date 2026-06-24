(function () {
    var idx = parseInt(document.documentElement.dataset.slideIndex, 10);
    var total = parseInt(document.documentElement.dataset.slideTotal, 10);

    document.addEventListener("keydown", function (e) {
        if (e.key === "ArrowDown" || e.key === "ArrowRight") {
            if (idx < total) location.href = idx + 1 + ".html";
        } else if (e.key === "ArrowUp" || e.key === "ArrowLeft") {
            if (idx > 1) location.href = idx - 1 + ".html";
        }
    });
})();
