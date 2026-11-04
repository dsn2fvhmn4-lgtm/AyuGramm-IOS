#!/usr/bin/env node
// Adds a release to the AltStore / SideStore source (newest first).
// Usage: node altstore/update-source.mjs <version> <build> <release tag> <ipa path> "<what's new>"
// Add the source in AltStore: https://raw.githubusercontent.com/neosay-dev/VoidGram/main/altstore/source.json
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const [version, build, tag, ipaPath, notes] = process.argv.slice(2);
if (!version || !build || !tag || !ipaPath) {
  console.error('usage: update-source.mjs <version> <build> <tag> <ipa> "<notes>"');
  process.exit(2);
}
const sourcePath = path.join(path.dirname(fileURLToPath(import.meta.url)), "source.json");
const source = JSON.parse(fs.readFileSync(sourcePath, "utf8"));
const app = source.apps[0];
const entry = {
  version,
  buildVersion: String(build),
  date: new Date().toISOString().replace(/\.\d+Z$/, "Z"),
  localizedDescription: notes || `VoidGram ${version}`,
  downloadURL: `https://github.com/neosay-dev/VoidGram/releases/download/${tag}/${path.basename(ipaPath)}`,
  size: fs.statSync(ipaPath).size,
  minOSVersion: "15.0",
};
app.versions = [entry, ...app.versions.filter((item) => item.version !== version)].slice(0, 20);
fs.writeFileSync(sourcePath, JSON.stringify(source, null, 2) + "\n");
console.log(`source.json: ${version} (${entry.size} bytes) -> ${entry.downloadURL}`);
