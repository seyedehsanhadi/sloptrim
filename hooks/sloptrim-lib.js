// Shared state, mode flags, ledger, and detect.py runner for all hooks.
'use strict';
const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');
const { execFileSync } = require('child_process');

// ------------------------------------------------------------------------
// PATHS: Where the mode flag, the session ledgers and the detector live.
// ------------------------------------------------------------------------
const CONFIG_DIR = process.env.CLAUDE_CONFIG_DIR || path.join(os.homedir(), '.claude');
const FLAG = path.join(CONFIG_DIR, '.sloptrim-active');
const LEDGER = path.join(CONFIG_DIR, '.sloptrim-ledger.json');
const LEDGER_CAP = 20;
const ROOT = process.env.CLAUDE_PLUGIN_ROOT || path.resolve(__dirname, '..');
const LEVELS = ['lite', 'full', 'strict'];

// ------------------------------------------------------------------------
// MODE: Reading and writing the one-word level flag.
// ------------------------------------------------------------------------
function readMode() {
  try {
    const v = fs.readFileSync(FLAG, 'utf8').trim().slice(0, 16);
    if (v === 'off') return 'off';
    if (LEVELS.includes(v)) return v;
  } catch (e) {}
  const d = (process.env.SLOPTRIM_DEFAULT_MODE || 'full').trim();
  return LEVELS.includes(d) || d === 'off' ? d : 'full';
}

function writeMode(mode) {
  try {
    fs.mkdirSync(CONFIG_DIR, { recursive: true });
    try {
      const st = fs.lstatSync(FLAG);
      if (!st.isFile()) fs.unlinkSync(FLAG);
    } catch (e) {}
    let flags;
    try {
      flags = fs.constants.O_WRONLY | fs.constants.O_CREAT | fs.constants.O_TRUNC | fs.constants.O_NOFOLLOW;
    } catch (e) {
      flags = 'w';
    }
    const fd = fs.openSync(FLAG, flags, 0o600);
    try {
      fs.writeSync(fd, mode);
    } finally {
      fs.closeSync(fd);
    }
  } catch (e) {}
}

function readStdin() {
  try {
    return fs.readFileSync(0, 'utf8');
  } catch (e) {
    return '';
  }
}

function readTextFile(p) {
  const buf = fs.readFileSync(p);
  if (buf.length >= 2 && buf[0] === 0xff && buf[1] === 0xfe) {
    return buf.subarray(2).toString('utf16le');
  }
  if (buf.length >= 2 && buf[0] === 0xfe && buf[1] === 0xff) {
    const body = buf.subarray(2, buf.length - ((buf.length - 2) % 2));
    return Buffer.from(body).swap16().toString('utf16le');
  }
  if (buf.includes(0)) return '';
  const s = buf.toString('utf8');
  return s.charCodeAt(0) === 0xfeff ? s.slice(1) : s;
}

function parseStdin() {
  try {
    const v = JSON.parse(readStdin() || '{}');
    return v && typeof v === 'object' && !Array.isArray(v) ? v : {};
  } catch (e) {
    return {};
  }
}

const DETECT = [
  path.join(ROOT, 'scripts', 'detect.py'),
  path.join(ROOT, 'skills', 'sloptrim', 'scripts', 'detect.py'),
].find((p) => { try { return fs.statSync(p).isFile(); } catch (e) { return false; } })
  || path.join(ROOT, 'scripts', 'detect.py');

// ------------------------------------------------------------------------
// DETECTOR BRIDGE: Runs detect.py. Text goes in on stdin; no filename reaches a command line unless the format is binary.
// ------------------------------------------------------------------------
function detectorMessage(e) {
  const err = String((e && e.stderr) || '');
  const last = err.split(/\r?\n/).filter((l) => l.trim()).pop();
  if (last) {
    try {
      const j = JSON.parse(last);
      if (j && j.error) return String(j.error).slice(0, 200);
    } catch (e2) {}
    return last.trim().slice(0, 200);
  }
  if (e && e.code) return String(e.code).slice(0, 200);
  return `exit ${e && e.status != null ? e.status : 'unknown'}`;
}

function runDetectResult(inputText, opts, extraArgs) {
  const base = {
    input: inputText,
    encoding: 'utf8',
    maxBuffer: 32 * 1024 * 1024,
    env: { ...process.env, PYTHONIOENCODING: 'utf-8' },
    ...opts,
  };
  const args = [DETECT].concat(extraArgs || []);
  let ran = null;
  for (const exe of ['python', 'python3', 'py']) {
    try {
      const out = execFileSync(exe, args, base);
      if (String(out || '').trim()) return { ok: true, out, kind: 'ok', detail: '' };
      return { ok: false, out: null, kind: 'no-output', detail: '' };
    } catch (e) {
      // Only a launcher that is not there is worth trying the next name for. Once an
      // interpreter has started, its failure is the answer, and retrying the other two
      // spends the same timeout again for nothing.
      if (e && e.status == null && e.code !== 'ETIMEDOUT') continue;
      ran = e;
      break;
    }
  }
  if (ran) return { ok: false, out: null, kind: 'detector-error', detail: detectorMessage(ran) };
  return { ok: false, out: null, kind: 'no-python', detail: '' };
}

function runDetect(inputText, opts, extraArgs) {
  const r = runDetectResult(inputText, opts, extraArgs);
  return r.ok ? r.out : null;
}

// ------------------------------------------------------------------------
// PLAIN LANGUAGE: Turning a 0-100 score into words a person can act on.
// ------------------------------------------------------------------------
function verdict(score) {
  if (typeof score !== 'number') return 'not scored';
  if (score <= 20) return 'reads clean';
  if (score <= 40) return 'reads mostly clean';
  if (score <= 60) return 'reads with some AI tells';
  if (score <= 80) return 'reads with heavy AI tells';
  return 'reads with pervasive AI tells';
}

function ledgerPath(sessionId) {
  const raw = String(sessionId || '');
  if (!raw) return LEDGER;
  // Stripping unsafe characters and truncating both merge distinct ids onto one file.
  // Hashing the whole id keeps the filename safe and short without collapsing any two.
  const safe = raw.replace(/[^a-zA-Z0-9-]/g, '').slice(0, 40);
  const tag = crypto.createHash('sha256').update(raw).digest('hex').slice(0, 12);
  return path.join(CONFIG_DIR, `.sloptrim-ledger-${safe}-${tag}.json`);
}

// ------------------------------------------------------------------------
// SESSION LEDGER: Per-session record of what was scored, so /sloptrim show can report it.
// ------------------------------------------------------------------------
function logDeliverable(rec, sessionId) {
  try {
    const file = ledgerPath(sessionId);
    let arr = readLedger(sessionId);
    arr.push(rec);
    if (arr.length > LEDGER_CAP) arr = arr.slice(-LEDGER_CAP);
    fs.writeFileSync(file, JSON.stringify(arr), { mode: 0o600 });
  } catch (e) {}
}

function readLedger(sessionId) {
  try {
    const arr = JSON.parse(fs.readFileSync(ledgerPath(sessionId), 'utf8'));
    return Array.isArray(arr) ? arr : [];
  } catch (e) {
    return [];
  }
}

function sweepLedgers() {
  try {
    const cutoff = Date.now() - 7 * 24 * 3600 * 1000;
    for (const f of fs.readdirSync(CONFIG_DIR)) {
      if (!f.startsWith('.sloptrim-ledger')) continue;
      const p = path.join(CONFIG_DIR, f);
      try { if (fs.statSync(p).mtimeMs < cutoff) fs.unlinkSync(p); } catch (e) {}
    }
  } catch (e) {}
}

function contract(mode) {
  const lines = [
    `SLOPTRIM ACTIVE - level: ${mode}`,
    '',
    '# Sloptrim',
    '',
    'You write prose like a careful human writer. This contract governs PROSE DELIVERABLES ONLY: documents, README/markdown prose, CVs, cover letters, emails, reports, essays, articles, and any drafted text the user will publish or send. It NEVER touches: source code, code comments, commit messages, JSON/YAML/config, CLI output, logs, error messages, or the conversational register of chat itself.',
    'Composes with other active modes; it does not override them. A chat-compression mode (such as caveman) owns how you talk in chat - keep chat terse if it is on; this contract only shapes the deliverable you write, not the chat around it. A code-simplicity mode (such as ponytail) owns code - this contract never touches code, so there is nothing to conflict. Each mode keeps its own domain: terse chat, lazy code, human prose. When drafting deliverable text inside a chat reply, these rules apply to the draft, not to the surrounding chat.',
    '',
    'Rules for prose:',
    '- Vary sentence length irregularly: a short sentence, then a long one that develops it. Never metronomic, never mechanical short-long alternation.',
    '- Banned vocabulary (use plain alternatives): delve, tapestry, pivotal, crucial, leverage, robust, seamless, foster, underscore, showcase, landscape (abstract), journey (abstract), realm, multifaceted, holistic, testament, vibrant, comprehensive, plethora, myriad, boast, elevate, empower, unlock, game-changer, supercharge, genuinely, fascinating, nuanced.',
    '- Banned moves: rule-of-three flourishes; "it\'s not just X, it\'s Y"; hedge stacking (two hedges in one sentence); signposting ("let\'s dive in"); empty pivots ("it\'s worth noting"); "In conclusion / Overall" closers; outcome-speculation tails (", paving the way for"); self-thoroughness ("this comprehensive guide"); generic upbeat endings; chatbot phrases ("I hope this helps").',
    '- Em-dash: at most one per paragraph. No bold-for-emphasis inside prose sentences. No emojis in prose. Semicolons and parentheses where a writer would naturally use them.',
    '- Mode: factual/encyclopedic content stays neutral third-person - never inject first-person voice or opinions into it. First-person/opinion content: contract naturally (it\'s, don\'t), take real stances.',
    '- Preserve exactly: numbers, units, dates, proper nouns, citations, quotes, technical terms. Never invent facts, sources, or statistics.',
    '- Concrete subjects, active verbs. End sections on a fact or observation, not a sentiment.',
    '- SILENT. Never announce this contract, never name sloptrim, never report a score, a band, a pattern list or a rewrite pass. Do not offer the user a style choice. When the file guard flags a span, fix it and say nothing. The clean prose is the only output; the process is never narrated.',
  ];
  if (mode !== 'lite') {
    const target = mode === 'strict'
      ? 'the clean band (score <= 20), and finish by piping the file through detect.py --clean'
      : 'clean or light tells (score <= 40)';
    lines.push(
      '',
      `After writing a prose file (.md/.txt), run: python "${DETECT}" "<file>" and read _metrics.ai_tell_score. If the band is worse than the target - ${target} - fix only the flagged spans, at most two passes, keeping rhythm variation (a flattened husk is as obvious as slop). For a deep rewrite, invoke the sloptrim skill.`
    );
  }
  return lines.join('\n');
}

module.exports = { CONFIG_DIR, FLAG, LEDGER, ROOT, DETECT, LEVELS, readMode, writeMode, readStdin, readTextFile, parseStdin, runDetect, runDetectResult, contract, verdict, logDeliverable, readLedger, ledgerPath, sweepLedgers };
