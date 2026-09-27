// Report CSS selectors never referenced in templates, JS, or Python.
// Usage: npm run css:unused [-- --write]  (--write deletes them in place)
import { randomBytes } from "node:crypto";
import { renameSync, unlinkSync, writeFileSync } from "node:fs";
import { basename, dirname, join } from "node:path";
import { PurgeCSS } from "purgecss";

function writeFileAtomic(file, content) {
  const tmp = join(
    dirname(file),
    `.${basename(file)}.${randomBytes(8).toString("hex")}.tmp`,
  );
  try {
    writeFileSync(tmp, content);
    renameSync(tmp, file);
  } catch (err) {
    try {
      unlinkSync(tmp);
    } catch {
      // tmp may not exist if write failed before creation
    }
    throw err;
  }
}

const results = await new PurgeCSS().purge({
  css: ["tcf_website/static/css/site/**/*.css"],
  content: [
    "tcf_website/templates/**/*.html",
    "tcf_website/static/js/**/*.js",
    "tcf_website/**/*.py",
  ],
  // Default extractor drops ":", missing responsive classes like `md:flex-row`.
  defaultExtractor: (content) => content.match(/[\w:-]+/g) || [],
  rejected: true,
  safelist: {
    // Base element styles, kept for any markup that uses them.
    standard: ["h5", "ol", "pre", "code"],
    greedy: [
      // Assembled from template variables, e.g. `--tone-{{ event.tone }}`.
      /--tone-\d/,
      /^landing-marquee--/,
      // AdSense sets data-ad-status on the slot at runtime.
      /^leaderboard-ad__slot$/,
    ],
  },
});

const write = process.argv.includes("--write");
let total = 0;
for (const { file, css, rejected } of results) {
  // reset.css targets elements/pseudo-classes (:focus-visible) by design.
  if (!rejected.length || file.endsWith("reset.css")) continue;
  total += rejected.length;
  if (write) writeFileAtomic(file, css);
  console.log(`\n${file.replace(`${process.cwd()}/`, "")}`);
  for (const selector of rejected) {
    console.log(`  ${selector.replace(/\s+/g, " ").trim()}`);
  }
}
console.log(`\n${total} unused selectors`);
if (total && !write) process.exitCode = 1;
