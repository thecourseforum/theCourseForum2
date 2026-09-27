// Report CSS selectors never referenced in templates, JS, or Python.
// Usage: npm run css:unused [-- --write]  (--write deletes them in place)
import { writeFileSync } from "node:fs";
import { PurgeCSS } from "purgecss";

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
  if (write) writeFileSync(file, css);
  console.log(`\n${file.replace(`${process.cwd()}/`, "")}`);
  for (const selector of rejected) {
    console.log(`  ${selector.replace(/\s+/g, " ").trim()}`);
  }
}
console.log(`\n${total} unused selectors`);
