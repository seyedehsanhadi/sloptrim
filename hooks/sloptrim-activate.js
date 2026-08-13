#!/usr/bin/env node
// SessionStart hook: emits the prose contract for the active mode.
'use strict';
process.on('uncaughtException', () => process.exit(0));
process.on('unhandledRejection', () => process.exit(0));
const fs = require('fs');
const { readMode, writeMode, contract, LEVELS, sweepLedgers, FLAG } = require('./sloptrim-lib');

// The mode flag is written the first time this hook runs, so its absence is the
// only reliable signal that nobody has used this install yet.
const firstRun = !fs.existsSync(FLAG);

const WELCOME = [
  'sloptrim is installed and on.',
  '',
  'Every prose file saved from here is scored against 71 documented patterns, and the',
  'ones that fired are named so they get fixed before the file ships. Code, config and',
  'commit messages are never touched.',
  '',
  'It is a command-line tool and a plugin. There is no website and no hosted version.',
  'Nothing you write is uploaded, there is no account, and no text leaves this machine.',
  '',
  '  /sloptrim doctor   check the install',
  '  /sloptrim check    score one file without changing it',
  '  /sloptrim off      turn it off',
  '  /sloptrim help     everything else',
  '',
  'Shown once. It will not appear again.',
  '',
].join('\n');

sweepLedgers();

const mode = readMode();
if (mode === 'off') process.exit(0);
if (LEVELS.includes(mode)) writeMode(mode);
process.stdout.write((firstRun ? WELCOME + '\n' : '') + contract(mode));
process.exit(0);
