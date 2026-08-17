#!/usr/bin/env node
// PostToolUse hook: scores a saved prose file, nudges past threshold.
'use strict';
process.on('uncaughtException', () => process.exit(0));
process.on('unhandledRejection', () => process.exit(0));
const path = require('path');
const fs = require('fs');
const { readMode, parseStdin, readTextFile, runDetect, verdict, logDeliverable } = require('./sloptrim-lib');

// ------------------------------------------------------------------------
// SCOPE: Which files are prose, which are documents, and which are neither.
// ------------------------------------------------------------------------
const PROSE_EXT = new Set([
  '.md', '.mdx', '.markdown', '.txt', '.text', '.rst', '.tex', '.org', '.adoc',
]);
const OFFICE_EXT = new Set([
  '.docx', '.docm', '.pptx', '.pptm', '.xlsx', '.xlsm',
  '.odt', '.odp', '.ods', '.epub',
]);
const BINARY_PROSE = new Set(['.pdf', '.rtf']);
// A notebook is prose in its markdown cells and code everywhere else, so the
// detector is handed the path and pulls out only the markdown.
const NOTEBOOK_EXT = new Set(['.ipynb']);

module.exports = { OFFICE_EXT, NOTEBOOK_EXT, BINARY_PROSE };
if (require.main !== module) return;

const mode = readMode();
if (mode === 'off' || mode === 'lite') process.exit(0);

const input = parseStdin();
const sid = input.session_id;
// NotebookEdit names its target notebook_path, not file_path.
const ti = input.tool_input || {};
const filePath = String(ti.file_path || ti.notebook_path || '');
if (!filePath) process.exit(0);

const ext = path.extname(filePath).toLowerCase();
const base = path.basename(filePath);

if (/(^|[\\/])node_modules[\\/]|[\\/]\.git[\\/]|[\\/]memory[\\/]/i.test(filePath)) process.exit(0);

const selfRoot = process.env.CLAUDE_PLUGIN_ROOT || path.resolve(__dirname, '..');
try {
  const rel = path.relative(selfRoot, path.resolve(filePath));
  if (rel && !rel.startsWith('..') && !path.isAbsolute(rel)) process.exit(0);
} catch (e) { /* unresolvable path: fall through and score it */ }

// Instruction files are the agent's own scaffolding, not a deliverable. The exempt names
// are exact, because agents.txt and memory.txt are ordinary prose a user may well write.
// Outside the prose extensions the stem is enough: skill.pdf is scaffolding whatever its
// format, and matching it here rather than lower down keeps it out of the binary log too.
const lowerBase = base.toLowerCase();
const SKIP_NAMES = new Set(['claude.md', 'claude.local.md', 'agents.md', 'agents.local.md',
                            'skill.md', 'memory.md']);
const SKIP_STEMS = new Set(['claude', 'claude.local', 'agents', 'agents.local',
                            'skill', 'memory']);
const stem = lowerBase.slice(0, lowerBase.length - ext.length);
if (SKIP_NAMES.has(lowerBase)) process.exit(0);
if (!PROSE_EXT.has(ext) && SKIP_STEMS.has(stem)) process.exit(0);

const isOffice = OFFICE_EXT.has(ext) || NOTEBOOK_EXT.has(ext);
if (!PROSE_EXT.has(ext) && !isOffice) {
  if (BINARY_PROSE.has(ext)) {
    logDeliverable({ t: Date.now(), file: base, kind: 'binary' }, sid);
  }
  process.exit(0);
}

// ------------------------------------------------------------------------
// READ: Plain text is read here; zip-based documents are handed to the detector by path.
// ------------------------------------------------------------------------
let text = '';
try {
  const stat = fs.statSync(filePath);
  if (!stat.isFile()) process.exit(0);
  const limit = isOffice ? 4 * 1024 * 1024 : 512 * 1024;
  if (stat.size > limit) {
    logDeliverable({ t: Date.now(), file: base, kind: 'skipped',
                     reason: 'size', size: stat.size, limit }, sid);
    process.exit(0);
  }
  if (!isOffice) text = readTextFile(filePath);
} catch (e) {
  process.exit(0);
}

const out = isOffice
  ? runDetect('', { timeout: 15000 }, [filePath])
  : runDetect(text, { timeout: 8000 });
if (out == null) process.exit(0);

let report;
try {
  report = JSON.parse(out);
} catch (e) {
  process.exit(0);
}
const m = report._metrics || {};
const score = m.ai_tell_score;
if (typeof score !== 'number') process.exit(0);

// ------------------------------------------------------------------------
// REPORT: The nudge, in plain language, or silence.
// ------------------------------------------------------------------------
const labels = Object.entries(report)
  .filter(([k, v]) => !k.startsWith('_') && v && v.label)
  .map(([k, v]) => v.label)
  .slice(0, 5);

const threshold = mode === 'strict' ? 20 : 40;
const flagged = score > threshold && m.confidence !== 'none';

logDeliverable({ t: Date.now(), file: base, kind: 'scored', score,
                 band: m.ai_tell_band, tells: labels, flagged }, sid);

if (!flagged) process.exit(0);

process.stdout.write(JSON.stringify({
  hookSpecificOutput: {
    hookEventName: 'PostToolUse',
    additionalContext:
      `sloptrim: ${base} ${verdict(score)} (score ${score}, band ${m.ai_tell_band}` +
      // The scan stops at 256 KB, so on a longer file the score covers a prefix.
      `${m.truncated ? ', first 256 KB only' : ''}). Flagged: ${labels.join('; ')}. ` +
      'Fix the flagged spans before finishing (max 2 passes, keep rhythm variation).',
  },
}));
process.exit(0);
