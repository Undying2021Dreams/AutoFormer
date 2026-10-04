// Render every converted expression with KaTeX and report failures.
//
//   KATEX=/path/to/node_modules/katex node scripts/check_latex.mjs
//
// KaTeX is what the marking system renders with, so "it renders in
// KaTeX" is the bar that matters, not "it looks like valid LaTeX".

import { readFileSync } from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const katex = require(process.env.KATEX ?? "katex");

const items = JSON.parse(readFileSync("data/check/latex.json", "utf8"));
const failures = [];
const warnings = [];

for (const { module, latex } of items) {
  try {
    katex.renderToString(latex, {
      throwOnError: true,
      strict: (code, msg) => { warnings.push({ module, latex, code, msg }); return "ignore"; },
    });
  } catch (err) {
    failures.push({ module, latex, error: String(err.message).split("\n")[0] });
  }
}

const pct = (n) => ((100 * n) / items.length).toFixed(3);
console.log(`${items.length} expressions`);
console.log(`failed:   ${failures.length} (${pct(failures.length)}%)`);
console.log(`warnings: ${warnings.length} (${pct(warnings.length)}%)`);

const byError = new Map();
for (const f of failures) {
  const key = f.error.replace(/at position \d+.*/, "").slice(0, 90);
  if (!byError.has(key)) byError.set(key, []);
  byError.get(key).push(f);
}
for (const [key, fs] of [...byError].sort((a, b) => b[1].length - a[1].length).slice(0, 10)) {
  console.log(`\n${fs.length} x ${key}`);
  console.log(`   e.g. ${fs[0].latex.slice(0, 140)}`);
}

const byCode = new Map();
for (const w of warnings) byCode.set(w.code, (byCode.get(w.code) ?? 0) + 1);
if (byCode.size) console.log("\nwarning codes:", Object.fromEntries(byCode));
