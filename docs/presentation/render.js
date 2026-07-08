const fs = require("fs");
const path = require("path");
const puppeteer = require("puppeteer");
const { PDFDocument } = require("pdf-lib");
const cliProgress = require("cli-progress");
const { updateSlides } = require("./update-slides.js");

// -------------------- PARSE ARGUMENTS --------------------
const args = process.argv.slice(2);

if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    console.log(`
📄 PDF Slide Generator

Usage: node render.js <slidesDirectory> [scale]

Arguments:
  slidesDirectory  Directory containing X.Y.Z.html files (required)
  scale            Float value for zoom (optional, default: 1.0)

Description:
  Updates all slides (injects indicator, computes prev/next) then generates a PDF.

Examples:
  node render.js ./slides              # uses ./slides, scale 1.0
  node render.js ./slides 1.5          # uses ./slides, scale 1.5
`);
    process.exit(0);
}

const slidesDir = args[0];
if (!fs.existsSync(slidesDir)) {
    console.error(`❌ Directory "${slidesDir}" does not exist.`);
    process.exit(1);
}

let scale = 1.0;
if (args.length > 1) {
    const parsed = parseFloat(args[1]);
    if (isNaN(parsed) || parsed <= 0) {
        console.error("❌ Error: Scale must be a positive number.");
        process.exit(1);
    }
    scale = parsed;
}

// -------------------- MAIN --------------------
(async () => {
    // ÉTAPE 1 : Mettre à jour les slides
    console.log("🔄 Updating slides...");
    await updateSlides(slidesDir);

    // ÉTAPE 2 : Générer le PDF
    const files = fs
        .readdirSync(slidesDir)
        .filter((file) => /^\d+\.\d+\.html$/.test(file))
        .sort((a, b) => {
            const [aP, aS] = a.split(".").map(Number);
            const [bP, bS] = b.split(".").map(Number);
            if (aP !== bP) return aP - bP;
            return aS - bS;
        });

    if (files.length === 0) {
        console.error(`❌ No X.Y.html files found in "${slidesDir}"!`);
        process.exit(1);
    }

    const progressBar = new cliProgress.SingleBar({
        format: "{bar} {percentage}% | {value}/{total} slides",
        barCompleteChar: "\u2588",
        barIncompleteChar: "\u2591",
        hideCursor: true,
    });
    progressBar.start(files.length, 0);

    const browser = await puppeteer.launch();
    const pdfDoc = await PDFDocument.create();

    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        const page = await browser.newPage();
        const absoluteFilePath = path.resolve(slidesDir, file);
        const filePath = `file:///${absoluteFilePath.replace(/\\/g, "/")}?mode=all`;

        await page.goto(filePath, { waitUntil: "networkidle0" });

        const pdfBytes = await page.pdf({
            width: "1920px",
            height: "1080px",
            printBackground: true,
            scale: scale,
        });

        const doc = await PDFDocument.load(pdfBytes);
        const [copiedPage] = await pdfDoc.copyPages(doc, [0]);
        pdfDoc.addPage(copiedPage);

        await page.close();
        progressBar.update(i + 1);
    }

    progressBar.stop();
    await browser.close();

    const finalPdf = await pdfDoc.save();
    fs.writeFileSync("slides.pdf", finalPdf);
    console.log(`✅ PDF generated: slides.pdf (scale ${scale})`);
})();
