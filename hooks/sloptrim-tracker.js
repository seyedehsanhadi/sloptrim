#!/usr/bin/env node
// UserPromptSubmit hook: /sloptrim command router and per-turn reminder.
'use strict';
process.on('uncaughtException', () => process.exit(0));
process.on('unhandledRejection', () => process.exit(0));
const { execFileSync } = require('child_process');
const path = require('path');
const fs = require('fs');
const { readMode, writeMode, parseStdin, readTextFile, LEVELS, readLedger, verdict, runDetectResult, contract, ROOT } = require('./sloptrim-lib');
const { OFFICE_EXT, NOTEBOOK_EXT, BINARY_PROSE } = require('./sloptrim-guard');

function help() {
  return [
    `sloptrim - always-on prose humanizer. Level now: ${readMode()}. Code, commits, config, chat: never touched.`,
    '  /sloptrim lite            contract only, no file scoring',
    '  /sloptrim full            contract + guard at score 40 (default)',
    '  /sloptrim strict          guard at 20 + character scrub',
    '  /sloptrim off | on        disable / re-enable',
    '  /sloptrim status          one-line current level',
    '  /sloptrim show            what was scored this session, plain language',
    '  /sloptrim check <file>    score a file, report only - no rewrite',
    '  /sloptrim doctor          is everything working? plain-words health check',
    '  /sloptrim stats           session token use + own-prose score',
    '  /sloptrim init            write the prose contract into ./AGENTS.md for other agents',
    '  deep rewrite: say "sloptrim this" / "humanize this" with text or a file',
  ].join('\n');
}

function check(fileArg) {
  if (!fileArg) return 'sloptrim check: give a file path (/sloptrim check draft.md)';
  const p = path.resolve(fileArg);
  const ext = path.extname(p).toLowerCase();
  const isOffice = OFFICE_EXT.has(ext) || NOTEBOOK_EXT.has(ext);
  let text = '';
  try {
    const st = fs.statSync(p);
    if (!st.isFile()) return `sloptrim check: not a file: ${fileArg}`;
    if (BINARY_PROSE.has(ext)) return `sloptrim check: no readable text in ${path.basename(p)}`;
    const cap = isOffice ? 4 * 1024 * 1024 : 512 * 1024;
    if (st.size > cap) return `sloptrim check: file over ${cap / 1024} KB`;
    if (!isOffice) text = readTextFile(p);
  } catch (e) {
    return `sloptrim check: cannot read ${fileArg}`;
  }
  const res = isOffice
    ? runDetectResult('', { timeout: 15000 }, [p])
    : runDetectResult(text, { timeout: 15000 });
  if (!res.ok) {
    if (res.kind === 'no-python') return 'sloptrim check: detector unavailable (needs python on PATH)';
    if (res.kind === 'no-output') return `sloptrim check: detector produced no report for ${path.basename(p)}`;
    if (res.detail === 'empty input') return `sloptrim check: no readable text in ${path.basename(p)}`;
    return `sloptrim check: detector failed on ${path.basename(p)}: ${res.detail}`;
  }
  let rep;
  try { rep = JSON.parse(res.out); } catch (e) { return 'sloptrim check: detector returned no report'; }
  const m = rep._metrics || {};
  const tells = Object.entries(rep)
    .filter(([k, v]) => !k.startsWith('_') && v && v.label)
    .map(([k, v]) => `${v.label} (x${v.count})`);
  return [
    `${path.basename(p)} - ${verdict(m.ai_tell_score)} (score ${m.ai_tell_score}/100, band: ${m.ai_tell_band})`,
    tells.length ? `tells: ${tells.slice(0, 8).join('; ')}` : 'tells: none',
    'report only - say "sloptrim this file" for the rewrite.',
  ].join('\n');
}

function doctor() {
  const { DETECT, FLAG } = require('./sloptrim-lib');
  const lines = ['sloptrim doctor:'];
  const mode = readMode();
  lines.push(`  [${mode === 'off' ? 'off' : 'OK'}] mode: ${mode}${mode === 'off' ? '  -> /sloptrim on' : ''}`);
  lines.push(fs.existsSync(DETECT)
    ? '  [OK] detector found'
    : '  [!!] detector missing - reinstall the plugin (/plugin install sloptrim@sloptrim)');
  const res = runDetectResult('The quick brown fox jumps over the lazy dog. It lands.', { timeout: 15000 });
  let scoreOk = false;
  try { scoreOk = typeof JSON.parse(res.out)._metrics.ai_tell_score === 'number'; } catch (e) {}
  if (scoreOk) {
    lines.push('  [OK] python runs the detector');
  } else if (res.kind === 'no-python') {
    lines.push('  [!!] python not found - install Python 3.9+ from python.org and restart. Until then prose is still shaped, but saved files are not re-scored.');
  } else if (res.kind === 'detector-error') {
    lines.push(`  [!!] python runs, but the detector failed: ${res.detail}. Reinstall the plugin (/plugin install sloptrim@sloptrim).`);
  } else {
    lines.push('  [!!] python runs, but the detector returned no usable report. Reinstall the plugin (/plugin install sloptrim@sloptrim).');
  }
  try {
    fs.accessSync(path.dirname(FLAG), fs.constants.W_OK);
    lines.push('  [OK] settings folder writable');
  } catch (e) {
    lines.push('  [!!] cannot write settings folder');
  }
  const anyFault = lines.some(l => l.includes('[!!]'));
  lines.push(anyFault
    ? 'Fix the [!!] lines above, then run /sloptrim doctor again.'
    : mode === 'off'
      ? `Nothing is wrong. It is switched off, so saved files are not scored. ${SELF} on turns it back on.`
      : scoreOk
        ? `All good. It is on: every prose file saved from here is scored, and the tells are named. ${SELF} show reveals what got checked.`
        : `The install is sound but no file has been scored yet. Save a prose file, then ${SELF} show.`);
  return lines.join('\n');
}

const INIT_MARKER = '<!-- sloptrim-contract -->';
// ----------------------------------------------------- reaching other agents
function initCursorRule() {
  const target = path.resolve('.cursor', 'rules', 'sloptrim.mdc');
  if (fs.existsSync(target)) return `sloptrim init: Cursor rule already at ${target}`;
  try {
    const source = fs.readFileSync(path.join(ROOT, '.cursor', 'rules', 'sloptrim.mdc'), 'utf8');
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, source);
    return `sloptrim init: Cursor rule written to ${target}`;
  } catch (e) {
    return `sloptrim init: cannot write ${target}`;
  }
}

function init() {
  const target = path.resolve('AGENTS.md');
  const cursor = initCursorRule();
  let existing = '';
  try { existing = fs.readFileSync(target, 'utf8'); } catch (e) {}
  if (existing.includes(INIT_MARKER)) return `sloptrim init: already present in ${target}\n${cursor}`;
  const section = `\n${INIT_MARKER}\n## Prose contract\n\n${contract(readMode())}\n`;
  try {
    fs.writeFileSync(target, existing ? existing.replace(/\s*$/, '\n') + section : section.trimStart());
    return `sloptrim init: prose contract written to ${target}\n${cursor}`;
  } catch (e) {
    return `sloptrim init: cannot write ${target}\n${cursor}`;
  }
}

function showLedger(sid) {
  const rows = readLedger(sid);
  if (!rows.length) {
    return 'sloptrim: nothing scored yet this session. It scores prose files as they are saved; '
      + 'this list fills in once a prose file (.md/.txt/…) or a .docx/.pdf deliverable is saved.';
  }
  const lines = ['sloptrim - prose delivered this session (newest first):'];
  for (const r of rows.slice().reverse()) {
    if (r.kind === 'binary') {
      lines.push(`  ${r.file} - binary, shaped at write-time by the contract (not re-scored)`);
    } else {
      const tells = r.tells && r.tells.length ? ` - fixed/flagged: ${r.tells.join('; ')}` : '';
      lines.push(`  ${r.file} - ${verdict(r.score)} (score ${r.score}/${r.band})${tells}`);
    }
  }
  return lines.join('\n');
}

function block(reason) {
  process.stdout.write(JSON.stringify({ decision: 'block', reason }));
  process.exit(0);
}

function remind(mode) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'UserPromptSubmit',
      additionalContext: `SLOPTRIM ACTIVE (${mode}). Prose deliverables follow the human-writing contract; code, config, commits untouched.`,
    },
  }));
  process.exit(0);
}

const input = parseStdin();
const prompt = String(input.prompt || '').trim();
const lower = prompt.toLowerCase();

const cmd = prompt.match(/^\/sloptrim(:sloptrim)?(?:[ :-]+(\w+))?(?:\s+(\S.*?))?\s*$/i);
// A marketplace install namespaces the command, so a reply that suggests
// /sloptrim show is useless to half the users. Echo the form they used.
const SELF = cmd && cmd[1] ? '/sloptrim:sloptrim' : '/sloptrim';
if (cmd) {
  const arg = (cmd[2] || 'help').toLowerCase();
  const rest = cmd[3] || '';
  if (arg === 'off') { writeMode('off'); block('sloptrim: off'); }
  if (arg === 'on') { writeMode('full'); block('sloptrim: on (full)'); }
  if (LEVELS.includes(arg)) { writeMode(arg); block(`sloptrim: level set to ${arg}`); }
  if (arg === 'status') block(`sloptrim: ${readMode()}`);
  if (arg === 'show') block(showLedger(input.session_id));
  if (arg === 'help') block(help());
  if (arg === 'check') block(check(rest));
  if (arg === 'doctor') block(doctor());
  if (arg === 'init') block(init());
  if (arg === 'stats') {
    try {
      const out = execFileSync(process.execPath, [path.join(__dirname, 'sloptrim-stats.js')], {
        input: JSON.stringify(input), timeout: 30000, encoding: 'utf8',
      });
      block(out.trim() || 'sloptrim-stats: no session data found');
    } catch (e) {
      block(`sloptrim-stats failed: ${e.message}`);
    }
  }
  block(`sloptrim: unknown command '${arg}' (off | on | lite | full | strict | status | show | check | doctor | stats | init | help)`);
}
if (lower === 'stop sloptrim' || lower === 'sloptrim off') {
  writeMode('off');
  block('sloptrim: off');
}

const mode = readMode();
if (mode === 'off') process.exit(0);
remind(mode);
