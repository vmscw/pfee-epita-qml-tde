const fs = require("fs");
const path = require("path");
const cheerio = require("cheerio");
const prettier = require("prettier");

function validateAndNormalizePages($, filePath) {
    const slide = $(".slide");
    if (slide.length === 0) {
        throw new Error(`No .slide element found in ${filePath}`);
    }

    // ---- Vérifier s'il y a des classes page-N quelque part ----
    const allPageElements = $("[class*='page-']").filter((i, el) => {
        const classes = $(el).attr("class")?.split(/\s+/) || [];
        return classes.some((c) => /^page-\d+$/.test(c));
    });

    const hasPageClass = allPageElements.length > 0;

    // Cas 1 : Aucune classe page-N → on ajoute page-1 sur .slide
    if (!hasPageClass) {
        const current = slide.attr("class") || "";
        if (!/page-1\b/.test(current)) {
            slide.attr("class", (current + " page-1").trim());
        }
        return 1;
    }

    // ---- Cas 2 : Il y a des classes page-N ----
    // Règle : soit le .slide a une classe page-N, soit tous ses enfants directs en ont une
    const slideClasses = slide.attr("class")?.split(/\s+/) || [];
    const slideHasPage = slideClasses.some((c) => /^page-\d+$/.test(c));

    if (slideHasPage) {
        // .slide a une page-N → c'est valide, on continue (on ne bloque rien)
        // Rien à vérifier de plus, on compte simplement les pages
    } else {
        // .slide n'a pas de page-N → tous les enfants directs doivent en avoir une
        const directChildren = slide.children();
        if (directChildren.length === 0) {
            throw new Error(`No direct children under .slide in ${filePath}`);
        }

        directChildren.each((i, child) => {
            const $child = $(child);
            const childClasses = $child.attr("class")?.split(/\s+/) || [];
            const hasPage = childClasses.some((c) => /^page-\d+$/.test(c));
            if (!hasPage) {
                const name = child.name || "?";
                throw new Error(
                    `Direct child <${name}> of .slide must have a page-N class in ${filePath}`
                );
            }
        });
    }

    // ---- Compter le nombre de pages uniques (max) ----
    const pageClasses = new Set();
    $("[class*='page-']").each((i, el) => {
        const classes = $(el).attr("class")?.split(/\s+/) || [];
        for (const c of classes) {
            if (/^page-\d+$/.test(c)) {
                pageClasses.add(c);
            }
        }
    });

    const pageNumbers = Array.from(pageClasses)
        .map((c) => parseInt(c.split("-")[1], 10))
        .sort((a, b) => a - b);

    if (pageNumbers.length === 0) {
        throw new Error(`No .page-N classes found in ${filePath}`);
    }

    // Vérifier que les numéros sont consécutifs à partir de 1
    for (let i = 0; i < pageNumbers.length; i++) {
        if (pageNumbers[i] !== i + 1) {
            throw new Error(
                `Page numbers must be consecutive starting from 1. Found: ${pageNumbers.join(", ")} in ${filePath}`
            );
        }
    }

    // Retourner le nombre total de pages (le max)
    return Math.max(...pageNumbers);
}

// ------------------------------------------------------------
//  Restructuration du body : gère 0 ou 1 élément .slide
// ------------------------------------------------------------
function ensureSlideStructure($, filePath) {
    const body = $("body");
    const slides = body.children(".slide");

    if (slides.length > 1) {
        throw new Error(`Multiple .slide elements found in ${filePath}. Only 0 or 1 allowed.`);
    }

    // Supprimer tout ancien .slide-indicator (sera réinjecté après)
    $(".slide-indicator").remove();

    let slide = slides.first();

    if (slide.length === 0) {
        // Créer un .slide et y déplacer tout le body
        slide = $('<div class="slide"></div>');
        const children = [];
        body.children().each((i, el) => children.push(el));
        body.empty();
        for (const el of children) slide.append(el);
        body.append(slide);
    } else {
        // Déplacer tous les autres enfants directs dans le .slide
        const otherChildren = [];
        body.children().each((i, el) => {
            const $el = $(el);
            if (!$el.is(".slide")) otherChildren.push(el);
        });
        for (const el of otherChildren) slide.append(el);
    }

    // Ajouter un placeholder pour l'indicateur
    const indicatorPlaceholder = $('<div class="slide-indicator-placeholder"></div>');
    body.append(indicatorPlaceholder);
}

// ------------------------------------------------------------
//  Validation du template slide-indicator.html
// ------------------------------------------------------------
function validateIndicatorTemplate(templatePath) {
    if (!templatePath) {
        console.error(`❌ No template path provided.`);
        return null;
    }
    const rawContent = fs.readFileSync(templatePath, "utf8").trim();
    const fullHtml = `<html><body>${rawContent}</body></html>`;
    const $full = cheerio.load(fullHtml, { decodeEntities: false });

    const indicatorDiv = $full("body > .slide-indicator");
    if (indicatorDiv.length !== 1) {
        console.error(
            `❌ slide-indicator.html must contain exactly ONE div.slide-indicator at root level. Got ${indicatorDiv.length}.`
        );
        return null;
    }
    const bodyChildren = $full("body").children();
    if (bodyChildren.length !== 1) {
        console.error(
            `❌ slide-indicator.html must contain only ONE root element. Got ${bodyChildren.length}.`
        );
        return null;
    }
    return indicatorDiv.html();
}

// ------------------------------------------------------------
//  Fonction principale
// ------------------------------------------------------------
async function updateSlides(directory) {
    const slidesDir = directory || ".";

    if (!fs.existsSync(slidesDir)) {
        console.error(`❌ Directory "${slidesDir}" not found.`);
        return;
    }

    const files = fs
        .readdirSync(slidesDir)
        .filter((f) => /^\d+\.\d+\.html$/.test(f))
        .sort((a, b) => {
            const [aP, aS] = a.split(".").map(Number);
            const [bP, bS] = b.split(".").map(Number);
            if (aP !== bP) return aP - bP;
            return aS - bS;
        });

    if (files.length === 0) {
        console.error(`❌ No X.Y.html files found in "${slidesDir}".`);
        return;
    }

    // ---- Fichier slide-indicator.html ----
    const indicatorPath = path.join(slidesDir, "slide-indicator.html");
    let indicatorHtml = null;

    if (!fs.existsSync(indicatorPath)) {
        const defaultContent = `<div class="slide-indicator">Partie {part} - Slide {slide}/{total} (page {page})</div>`;
        fs.writeFileSync(indicatorPath, defaultContent, "utf8");
        console.log(`📝 Created default slide-indicator.html`);
        indicatorHtml = defaultContent;
    } else {
        indicatorHtml = fs.readFileSync(indicatorPath, "utf8");
    }

    // Valider le template (on utilise une fonction séparée)
    const indicatorContent = validateIndicatorTemplate(indicatorPath);
    if (indicatorContent === null) {
        return;
    }

    console.log(`📄 ${files.length} slide(s) found.`);

    // Grouper par partie pour le total des slides
    const slideTotals = {};
    files.forEach((file) => {
        const part = parseInt(file.split(".")[0], 10);
        slideTotals[part] = (slideTotals[part] || 0) + 1;
    });

    // ---- Lecture, validation et normalisation ----
    const allSlides = [];
    for (const file of files) {
        const filePath = path.join(slidesDir, file);
        const content = fs.readFileSync(filePath, "utf8");
        const $ = cheerio.load(content, { decodeEntities: false });

        const [part, slide] = file.split(".").map(Number);

        // 1. Restructuration du body (0 ou 1 .slide)
        try {
            ensureSlideStructure($, filePath);
        } catch (err) {
            console.error(err.message);
            return;
        }

        // 2. Validation et normalisation des pages
        let pageCount;
        try {
            pageCount = validateAndNormalizePages($, filePath);
        } catch (err) {
            console.error(err.message);
            return;
        }

        const slideTotal = slideTotals[part];

        allSlides.push({
            file,
            part,
            slide,
            slideTotal,
            pageCount,
            dom: $.html(),
        });
    }

    // ---- Traitement final de chaque fichier ----
    for (let i = 0; i < allSlides.length; i++) {
        const { file, part, slide, slideTotal, pageCount, dom } = allSlides[i];
        const prevFile = i > 0 ? allSlides[i - 1].file : "";
        const nextFile = i < allSlides.length - 1 ? allSlides[i + 1].file : "";

        const filePath = path.join(slidesDir, file);
        const $ = cheerio.load(dom, { decodeEntities: false });

        ensureStylesheet($);
        ensureNavScript($);

        // Injecter l'indicateur
        injectSlideIndicator($, part, slide, slideTotal, indicatorContent);

        // Attributs prev/next
        setSlideAttributes($, part, slide, slideTotal, prevFile, nextFile);

        const config = JSON.parse(fs.readFileSync(".prettierrc", "utf8"));
        let formatted = await prettier.format($.html(), { ...config, parser: "html" });
        formatted = formatted.replace(/<!DOCTYPE html>/i, "<!doctype html>");
        fs.writeFileSync(filePath, formatted, "utf8");
        console.log(`✅ ${file} (${pageCount} page(s))`);
    }

    console.log("🎉 All done.");
}

// ---- Fonctions auxiliaires ----
function ensureStylesheet($) {
    if ($('head link[rel="stylesheet"][href="styles.css"]').length === 0) {
        $("head").append('<link rel="stylesheet" href="styles.css">');
    }
}

function ensureNavScript($) {
    $('head script[src="nav.js"]').remove();
    $("head").append('<script src="nav.js" defer></script>');
}

function injectSlideIndicator($, part, slide, slideTotal, indicatorContent) {
    let html = indicatorContent
        .replace(/\{part\}/g, part)
        .replace(/\{slide\}/g, slide)
        .replace(/\{total\}/g, slideTotal);

    const indicator = $('<div class="slide-indicator"></div>');
    indicator.html(html);

    const placeholder = $(".slide-indicator-placeholder");
    placeholder.replaceWith(indicator);
}

function setSlideAttributes($, part, slide, slideTotal, prevFile, nextFile) {
    const html = $("html");
    html.attr("data-slide-part", part);
    html.attr("data-slide-slide", slide);
    html.attr("data-slide-total", slideTotal);
    html.attr("data-slide-prev", prevFile);
    html.attr("data-slide-next", nextFile);
}

if (require.main === module) {
    const dir = process.argv[2] || ".";
    updateSlides(dir).catch(console.error);
}

module.exports = { updateSlides };
