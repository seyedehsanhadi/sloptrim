#!/usr/bin/env node
// /sloptrim stats: session token usage and own-prose score.
'use strict';
process.on('uncaughtException', () => process.exit(0));
process.on('unhandledRejection', () => process.exit(0));
const fs = require('fs');
const path = require('path');
const { CONFIG_DIR, parseStdin, readMode, runDetect } = require('./sloptrim-lib');

function newestSession(dir) {
  let best = null;
  let stack = [dir];
  while (stack.length) {
    const d = stack.pop();
    let entries;
    try {
      entries = fs.readdirSync(d, { withFileTypes: true });
    } catch (e) {
      continue;
    }
    for (const e of entries) {
      const p = path.join(d, e.name);
      if (e.isDirectory()) stack.push(p);
      else if (e.name.endsWith('.jsonl')) {
        const mt = fs.statSync(p).mtimeMs;
        if (!best || mt > best.mt) best = { p, mt };
      }
    }
  }
  return best && best.p;
}

const input = parseStdin();
const sessionFile = input.transcript_path || newestSession(path.join(CONFIG_DIR, 'projects'));
if (!sessionFile || !fs.existsSync(sessionFile)) {
  process.stdout.write('sloptrim-stats: no session transcript found');
  process.exit(0);
}

let outputTokens = 0;
let cacheRead = 0;
let turns = 0;
const texts = [];
for (const line of fs.readFileSync(sessionFile, 'utf8').split('\n')) {
  if (!line.trim()) continue;
  let entry;
  try {
    entry = JSON.parse(line);
  } catch (e) {
    continue;
  }
  if (!entry || typeof entry !== 'object') continue;
  if (entry.type !== 'assistant' || !entry.message) continue;
  const usage = entry.message.usage || {};
  outputTokens += usage.output_tokens || 0;
  cacheRead += usage.cache_read_input_tokens || 0;
  turns += 1;
  const content = entry.message.content;
  if (Array.isArray(content)) {
    for (const c of content) {
      if (c && c.type === 'text' && c.text) texts.push(c.text);
    }
  }
}

let prose = texts.join('\n\n').replace(/```[\s\S]*?```/g, ' ');
if (prose.length > 40000) prose = prose.slice(-40000);

let scoreLine = 'prose score: n/a (no assistant text)';
if (prose.trim().length > 200) {
  try {
    const out = runDetect(prose, { timeout: 15000 });
    const report = JSON.parse(out);
    const m = report._metrics || {};
    const pats = Object.keys(report).filter((k) => !k.startsWith('_')).length;
    scoreLine = `session prose ai_tell_score: ${m.ai_tell_score} (${m.ai_tell_band}), ${pats} pattern(s) flagged`;
  } catch (e) {
    scoreLine = 'prose score: n/a (detector unavailable)';
  }
}

process.stdout.write([
  `sloptrim-stats (level: ${readMode()})`,
  `assistant turns: ${turns}`,
  `output tokens: ${outputTokens.toLocaleString('en-US')}`,
  `cache-read input tokens: ${cacheRead.toLocaleString('en-US')}`,
  scoreLine,
  'Numbers read from the session transcript (usage fields) - measured, not estimated.',
].join('\n'));
process.exit(0);
