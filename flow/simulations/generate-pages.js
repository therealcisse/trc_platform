import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const INBOX_DATA = [
  {
    "betreff": "Es ist eine Auktion (ID 1456218) mit dem Sofortkaufpreis 15,00 EUR -- PLZ 22589 eingegangen.",
    "betreffLink": "./myOffer/13855227.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1456098) mit dem Sofortkaufpreis 17,00 EUR -- PLZ 22529 eingegangen.",
    "betreffLink": "./myOffer/13853631.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1456031) mit dem Sofortkaufpreis 15,00 EUR -- PLZ 25474 eingegangen.",
    "betreffLink": "./myOffer/13852658.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455975) mit dem Sofortkaufpreis 17,00 EUR -- PLZ 23669 eingegangen.",
    "betreffLink": "./myOffer/13852006.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455952) mit dem Sofortkaufpreis 70,00 EUR -- PLZ 23619 eingegangen.",
    "betreffLink": "./myOffer/13851814.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455881) mit dem Sofortkaufpreis 17,00 EUR -- PLZ 21147 eingegangen.",
    "betreffLink": "./myOffer/13851050.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455845) mit dem Sofortkaufpreis 20,00 EUR -- PLZ 29565 eingegangen.",
    "betreffLink": "./myOffer/13850517.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455810) mit dem Sofortkaufpreis 22,00 EUR -- PLZ 23689 eingegangen.",
    "betreffLink": "./myOffer/13850135.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455722) mit dem Sofortkaufpreis 17,00 EUR -- PLZ 25335 eingegangen.",
    "betreffLink": "./myOffer/13849151.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455601) mit dem Sofortkaufpreis 17,00 EUR -- PLZ 25551 eingegangen.",
    "betreffLink": "./myOffer/13847498.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455550) mit dem Sofortkaufpreis 70,00 EUR -- PLZ 22145 eingegangen.",
    "betreffLink": "./myOffer/13846964.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455522) mit dem Sofortkaufpreis 30,00 EUR -- PLZ 22609 eingegangen.",
    "betreffLink": "./myOffer/13846694.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455473) mit dem Sofortkaufpreis 17,00 EUR -- PLZ 22177 eingegangen.",
    "betreffLink": "./myOffer/13846088.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455239) mit dem Sofortkaufpreis 17,00 EUR -- PLZ 22844 eingegangen.",
    "betreffLink": "./myOffer/13843628.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455230) mit dem Sofortkaufpreis 10,00 EUR -- PLZ 20253 eingegangen.",
    "betreffLink": "./myOffer/13843587.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455179) mit dem Sofortkaufpreis 17,00 EUR -- PLZ 22177 eingegangen.",
    "betreffLink": "./myOffer/13842909.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455145) mit dem Sofortkaufpreis 17,00 EUR -- PLZ 22869 eingegangen.",
    "betreffLink": "./myOffer/13842389.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1455065) mit dem Sofortkaufpreis 15,00 EUR -- PLZ 22299 eingegangen.",
    "betreffLink": "./myOffer/13841409.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1454939) mit dem Sofortkaufpreis 17,00 EUR -- PLZ 23866 eingegangen.",
    "betreffLink": "./myOffer/13839641.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1454919) mit dem Sofortkaufpreis 17,00 EUR -- PLZ 22041 eingegangen.",
    "betreffLink": "./myOffer/13839262.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1454891) mit dem Sofortkaufpreis 17,00 EUR -- PLZ 21614 eingegangen.",
    "betreffLink": "./myOffer/13838963.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1454886) mit dem Sofortkaufpreis 22,00 EUR -- PLZ 22761 eingegangen.",
    "betreffLink": "./myOffer/13838890.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1454868) mit dem Sofortkaufpreis 17,00 EUR -- PLZ 22527 eingegangen.",
    "betreffLink": "./myOffer/13838599.html",
  },
  {
    "betreff": "Es ist eine Auktion (ID 1454799) mit dem Sofortkaufpreis 12,00 EUR -- PLZ 21709 eingegangen.",
    "betreffLink": "./myOffer/13837524.html",
  }
];

// Function to extract ID from betreff using regex
function extractIdFromBetreff(betreff) {
  // Try different patterns
  const patterns = [
    /\(ID (\d+)\)/,  // Pattern for "Es ist eine Auktion (ID 1456218)"
    /Lead (\d+)/     // Pattern for "Lead 1455952 erfolgreich"
  ];

  for (const pattern of patterns) {
    const match = betreff.match(pattern);
    if (match && match[1]) {
      return match[1];
    }
  }

  return null; // If no ID found
}

// Function to generate myOffer pages
function generateOfferPages(inboxData, template) {
  console.log('\n=== Generating Offer Pages ===');

  // Create myOffer directory if it doesn't exist
  const myOfferDir = path.join(__dirname, 'myOffer');
  if (!fs.existsSync(myOfferDir)) {
    fs.mkdirSync(myOfferDir, { recursive: true });
    console.log('Created myOffer directory');
  }

  // Process each item in INBOX_DATA
  let successCount = 0;
  inboxData.forEach((item, index) => {
    const { betreff, betreffLink } = item;

    // Extract filename from betreffLink
    const filename = path.basename(betreffLink);

    // Extract ID from betreff
    const id = extractIdFromBetreff(betreff);

    // Create the modified HTML content
    let htmlContent = template;

    // Replace HM_TITLE variable
    const titleReplacement = `var HM_TITLE = "Betreff: ${betreff.replace(/"/g, '\\"')}"; // e.g., "Betreff: Es ist eine Auktion (ID 1456218) mit dem Sofortkaufpreis 15,00 EUR -- PLZ 22589 eingegangen."`;
    htmlContent = htmlContent.replace(
      /var HM_TITLE = null; \/\/ e\.g\., "Betreff: Es ist eine Auktion \(ID 1456218\) mit dem Sofortkaufpreis 15,00 EUR -- PLZ 22589 eingegangen\."/,
      titleReplacement
    );

    // Replace HM_ZAHN_LINK variable
    if (id) {
      const zahnLinkReplacement = `var HM_ZAHN_LINK = { href: "/item/${id}.html?id=${id}", text: "${betreff.replace(/"/g, '\\"')}" }; // { href: "...", text: "Zahnzusatzversicherung KW: ..." }`;
      htmlContent = htmlContent.replace(
        /var HM_ZAHN_LINK = null; \/\/ \{ href: "\.\.\."[^}]*\}/,
        zahnLinkReplacement
      );
    }

    // Write the file
    const outputPath = path.join(myOfferDir, filename);

    try {
      fs.writeFileSync(outputPath, htmlContent, 'utf8');
      console.log(`Created offer page: ${filename} (ID: ${id || 'N/A'})`);
      successCount++;
    } catch (err) {
      console.error(`Error writing ${filename}:`, err);
    }
  });

  console.log(`Successfully created ${successCount} offer pages in the myOffer directory.`);
}

// Function to get random captcha file with embedded answer
function getRandomFile() {
  const files = [
    "000__a10.png",
    "001_a8.png",
    "002_a14.png",
    "003_a7.png",
    "004_a8.png",
    "005_a8.png",
    "006_a14.png",
    "007_a9.png",
    "008_a12.png",
    "009_a3.png",
    "010_a3.png",
    "011_a18.png",
    "012_a13.png",
    "013_a11.png",
    "014_a7.png",
    "015_a11.png",
    "016_a10.png",
    "017_a5.png",
    "018_a11.png",
    "019_a10.png",
    "020_a9.png",
    "021_a10.png",
    "022_a12.png",
    "023_a17.png",
    "024_a16.png",
    "025_a10.png",
    "026_a6.png"
  ];

  const index = Math.floor(Math.random() * files.length);
  return `/img_src/${files[index]}`;
}

// Function to generate item pages
function generateItemPages(inboxData, template) {
  console.log('\n=== Generating Item Pages ===');

  // Create item directory if it doesn't exist
  const itemDir = path.join(__dirname, 'item');
  if (!fs.existsSync(itemDir)) {
    fs.mkdirSync(itemDir, { recursive: true });
    console.log('Created item directory');
  }

  // Process each item in INBOX_DATA
  let successCount = 0;
  inboxData.forEach((item, index) => {
    const { betreff, betreffLink } = item;

    // Extract ID from betreff
    const id = extractIdFromBetreff(betreff);

    if (!id) {
      console.warn(`No ID found for: ${betreff}`);
      return;
    }

    // Create filename based on ID
    const filename = `${id}.html`;

    // Create the modified HTML content
    let htmlContent = template;

    // Replace HM_SOFO_KAUFEN_LINK variable
    const sofoKaufenLinkReplacement = `var HM_SOFO_KAUFEN_LINK = { href: "/buy_now/id/${id}.html" }; // e.g., { href: "https://example.com/buy-now" }`;
    htmlContent = htmlContent.replace(
      /var HM_SOFO_KAUFEN_LINK = null; \/\/ e\.g\., \{ href: "[^"]*" \}/,
      sofoKaufenLinkReplacement
    );

    // Write the file
    const outputPath = path.join(itemDir, filename);

    try {
      fs.writeFileSync(outputPath, htmlContent, 'utf8');
      console.log(`Created item page: ${filename} (for ${betreff.slice(0, 50)}...)`);
      successCount++;
    } catch (err) {
      console.error(`Error writing ${filename}:`, err);
    }
  });

  console.log(`Successfully created ${successCount} item pages in the item directory.`);
}

// Function to generate buy_now pages
function generateBuyNowPages(inboxData, template) {
  console.log('\n=== Generating Buy Now Pages ===');

  // Create buy_now/id directory if it doesn't exist
  const buyNowDir = path.join(__dirname, 'buy_now', 'id');
  if (!fs.existsSync(buyNowDir)) {
    fs.mkdirSync(buyNowDir, { recursive: true });
    console.log('Created buy_now/id directory');
  }

  // Process each item in INBOX_DATA
  let successCount = 0;
  inboxData.forEach((item, index) => {
    const { betreff, betreffLink } = item;

    // Extract ID from betreff
    const id = extractIdFromBetreff(betreff);

    if (!id) {
      console.warn(`No ID found for: ${betreff}`);
      return;
    }

    // Create filename based on ID
    const filename = `${id}.html`;

    // Get random captcha file with embedded answer
    const randomCaptcha = getRandomFile();

    // Create the modified HTML content
    let htmlContent = template;

    // Replace HM_CAPTCHA_SRC variable
    const captchaSrcReplacement = `var HM_CAPTCHA_SRC = "${randomCaptcha}"; // e.g., "data:image/png;base64,..." or "https://.../captcha.png"`;
    htmlContent = htmlContent.replace(
      /var HM_CAPTCHA_SRC = null; \/\/ e\.g\., "[^"]*" or "[^"]*"/,
      captchaSrcReplacement
    );

    // Write the file
    const outputPath = path.join(buyNowDir, filename);

    try {
      fs.writeFileSync(outputPath, htmlContent, 'utf8');
      console.log(`Created buy_now page: ${filename} (captcha: ${randomCaptcha})`);
      successCount++;
    } catch (err) {
      console.error(`Error writing ${filename}:`, err);
    }
  });

  console.log(`Successfully created ${successCount} buy_now pages in the buy_now/id directory.`);
}

// Main execution function
function main() {
  console.log('Starting page generation...');

  // Cleanup previous outputs before generating anything
  try {
    const dirsToDelete = [
      path.join(__dirname, 'buy_now'),
      path.join(__dirname, 'item'),
      path.join(__dirname, 'myOffer'),
    ];
    for (const d of dirsToDelete) {
      if (fs.existsSync(d)) {
        fs.rmSync(d, { recursive: true, force: true });
        console.log(`Deleted directory: ${d}`);
      }
    }
    const inboxPathDel = path.join(__dirname, 'inbox.html');
    if (fs.existsSync(inboxPathDel)) {
      fs.rmSync(inboxPathDel, { force: true });
      console.log(`Deleted file: ${inboxPathDel}`);
    }
  } catch (cleanupErr) {
    console.warn('Warning during cleanup:', cleanupErr);
  }

  try {
    // Read template files
    const offerTemplatePath = path.join(__dirname, 'myOffer.html');
    const itemTemplatePath = path.join(__dirname, 'item.html');
    const buyNowTemplatePath = path.join(__dirname, 'buyNow.html');

    const offerTemplate = fs.readFileSync(offerTemplatePath, 'utf8');
    const itemTemplate = fs.readFileSync(itemTemplatePath, 'utf8');
    const buyNowTemplate = fs.readFileSync(buyNowTemplatePath, 'utf8');

    // Build dynamic INBOX_DATA for this run from the static base above
    const base = INBOX_DATA;

    const idRegexes = [
      /\(ID (\d+)\)/,    // e.g. (ID 1456218)
    ];

    function extractIdMatch(str) {
      for (const re of idRegexes) {
        const m = String(str).match(re);
        if (m && m[1]) return m[1];
      }
      return null;
    }

    // Determine slug length from base data
    let inferredSlugLen = 12;
    for (const it of base) {
      const m = String(it?.betreffLink || '').match(/\.\/myOffer\/([A-Za-z0-9_-]+)\.html$/);
      if (m) {
        inferredSlugLen = m[1].length;
        break;
      }
    }

    function genNumeric(len, avoidLeadingZero = true) {
      if (!len || len <= 0) return '';
      const min = avoidLeadingZero ? Math.pow(10, Math.max(0, len - 1)) : 0;
      const max = Math.pow(10, len) - 1;
      let n = Math.floor(Math.random() * (max - min + 1)) + min;
      let s = String(n);
      if (!avoidLeadingZero && s.length < len) s = s.padStart(len, '0');
      if (avoidLeadingZero && s.length < len) {
        s = String(Math.pow(10, len - 1)) + s.padStart(len - 1, '0');
        s = s.slice(0, len);
      }
      return s;
    }

    function compileBetreff(template, newId) {
      let t = String(template || '');
      if (!String(template || '').includes('$MY_ID')) {
        t = t.replace(/\(ID \d+\)/g, `(ID ${newId})`);
        t = t.replace(/(Lead )\d+/g, `$1${newId}`);
      }
      return t;
    }

    const usedIds = new Set();
    const usedSlugs = new Set();

    const runInboxData = base.map((item) => {
      const sampleId = extractIdMatch(item.betreff);
      const idLen = sampleId ? sampleId.length : 7;
      let id;
      do { id = genNumeric(idLen, true); } while (usedIds.has(id));
      usedIds.add(id);

      let slug;
      do { slug = genNumeric(inferredSlugLen, true); } while (usedSlugs.has(slug));
      usedSlugs.add(slug);

      const betreff = compileBetreff(item.betreff, id);
      const betreffLink = `./myOffer/${slug}.html`;

      return { betreff, betreffLink };
    });

    // Generate all types of pages from the per-run data
    generateOfferPages(runInboxData, offerTemplate);
    generateItemPages(runInboxData, itemTemplate);
    generateBuyNowPages(runInboxData, buyNowTemplate);

    // Inject the two-field array into inbox.html as INBOX_DATA
    const inboxTemplatePath = path.join(__dirname, 'inbox.template.html');
    const origHtml = fs.readFileSync(inboxTemplatePath, 'utf8');
    const pretty = JSON.stringify(runInboxData, null, 2);

    const assignRe = /(\b(?:const)\s+INBOX_DATA\s*=\s*)(null)(\s*;?)/;
    let nextHtml;
    if (assignRe.test(origHtml)) {
      nextHtml = origHtml.replace(assignRe, (_, pre, _old, post) => `${pre}${pretty}${post}`);
    } else {
      const bodyClose = origHtml.lastIndexOf('</body>');
      const scriptBlock = `\n<script>\nvar INBOX_DATA = ${pretty};\n</script>\n`;
      if (bodyClose !== -1) {
        nextHtml = origHtml.slice(0, bodyClose) + scriptBlock + origHtml.slice(bodyClose);
      } else {
        nextHtml = origHtml + scriptBlock;
      }
    }
    const inboxPath = path.join(__dirname, 'inbox.html');
    fs.writeFileSync(inboxPath, nextHtml, 'utf8');

    console.log('\n=== Generation Complete ===');
    console.log(`Total processed: ${runInboxData.length} items`);

  } catch (err) {
    console.error('Error during page generation:', err);
    process.exit(1);
  }
}

// Execute main function
main();
